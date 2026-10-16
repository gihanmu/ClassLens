# ClassLens — Single Teacher Authentication & Access Guide

ClassLens uses a simple, secure, single-teacher authentication system engineered specifically for AI Builder Cup reviewers and educators.

---

## 1. Teacher Persona & Credentials

| Attribute | Value |
| :--- | :--- |
| **Display Name** | Mrs. Sarah Lim |
| **School Affiliation** | Cedar Secondary School |
| **Academic Department** | Mathematics Department |
| **Teacher Role** | Secondary 1 Mathematics Teacher |
| **Username / Email** | `teacher@classlens.demo` |
| **Password** | Configured locally via `CLASSLENS_DEMO_PASSWORD` |

> [!IMPORTANT]
> The teacher password is **never hardcoded or committed to git**. Each reviewer or local operator configures their own local password via `CLASSLENS_DEMO_PASSWORD` in `.env` or during account initialization.

---

## 2. Local Account Initialization

Initialize the default teacher account using the local initialization CLI:

```bash
# Option A: Initialize using CLASSLENS_DEMO_PASSWORD from .env
python scripts/init_teacher.py

# Option B: Initialize with an explicit password argument
python scripts/init_teacher.py --password "YourSecurePassword2026!"

# Option C: Initialize via the Python module entrypoint
python -m services.api.scripts.init_teacher --password "YourSecurePassword2026!"
```

### Idempotency Guarantee
The initialization command is **fully idempotent**:
- If `teacher@classlens.demo` already has an active password configured, re-running `init_teacher.py` will **safely exit without modifying the existing password**.
- To explicitly change or update an existing password, pass the `--reset` or `--force` flag:

```bash
python scripts/init_teacher.py --password "NewPassword2026!" --reset
```

---

## 3. Security Architecture

### Argon2id Password Hashing
- ClassLens uses **Argon2id** (the winner of the Password Hashing Competition), a hybrid algorithm that combines data-dependent and data-independent memory access.
- Parameter configuration:
  - Algorithm: Argon2id (`$argon2id$...`)
  - Memory Cost: 65,536 KiB (64 MiB)
  - Time Cost: 2 iterations
  - Parallelism: 1 lane
  - Salt & Hash Length: 32 bytes cryptographically secure random bytes

### Session Management & Cookie Protections
- **HTTP-Only Session Cookie (`__session`)**: Signed HMAC-SHA256 token containing user claims (`sub`, `org`, `role`, `iat`, `exp`). Inaccessible to client-side JavaScript, preventing token theft via Cross-Site Scripting (XSS).
- **Session Expiration**: Sessions automatically expire after 24 hours (`exp` claim validated on every API request).
- **Strict Anti-LocalStorage Rule**: No passwords, access tokens, or session tokens are stored in `localStorage` or `sessionStorage`.
- **SameSite Protection**: Session cookies are configured with `SameSite=Lax` and scoped to `path=/`.
- **CSRF Defense**: State mutations (`POST`, `PUT`, `DELETE`, `PATCH`) require the `X-Requested-With: ClassLens` header.

### Backend Authorization
All teacher-facing FastAPI endpoints fail-closed with **HTTP 401 Unauthorized** if an unauthenticated or expired request is received:
- `/api/v1/assessments` (assessment creation, listing, status)
- `/api/v1/assessments/{id}/upload` & `/upload-batch` (worksheet ingestion)
- `/api/v1/assessments/{id}/responses` (student responses)
- `/api/v1/assessments/{id}/insights` (cohort analytics & recommendations)
- `/api/v1/dashboard/summary`, `/recent-activity`, `/attention-queue` (teacher overview)
- `/api/v1/responses/{id}` & `/review` & `/override` (teacher diagnostic authority)
- `/api/v1/responses/{id}/audit-trail` (immutable tamper-evident event log)
- `/api/v1/responses/{id}/image` (handwritten student worksheet viewing)

---

## 4. Frontend Login & Routing Experience

- **Login Page (`/login`)**:
  - ClassLens brand identity and Cedar Secondary School badge.
  - Informative reviewer guidance note without ever displaying the password in the UI.
  - Password visibility toggle (Show/Hide).
  - Clear error notifications for invalid credentials and expired sessions.
- **Route Guards**:
  - Unauthenticated visitors to `/` or any protected view are automatically redirected to `/login?redirect=<path>`.
  - Authenticated teachers visiting `/login` are automatically redirected to the dashboard.
  - Intended navigation paths (`?redirect=...`) are preserved and sanitized (preventing open redirect attacks).
- **Logout Flow**:
  - An accessible "Sign out" button is integrated into the teacher profile card at the bottom of the navigation sidebar.
  - Clicking sign out calls `POST /api/v1/auth/logout`, clears session cookies, and redirects the browser back to `/login`.

---

## 5. Non-Destructive Reset & Troubleshooting

### Resetting the Teacher Password
If you need to change your local password:
```bash
python scripts/init_teacher.py --password "<new_password>" --reset
```

### Checking User Account Status in SQLite
To inspect the local users table in SQLite:
```bash
sqlite3 local-data/store/classlens.db "SELECT id, email, name, role, school, SUBSTR(password_hash, 1, 20) FROM users;"
```
Output:
```
usr_sarah_lim|teacher@classlens.demo|Mrs. Sarah Lim|Secondary 1 Mathematics Teacher|Cedar Secondary School|$argon2id$v=19$m=65
```

### Preserving Existing Assessment & Student Data
Password initialization or resets **only touch the `users` table** and will never modify, overwrite, or delete existing assessments, uploaded student worksheets, or teacher review overrides.
