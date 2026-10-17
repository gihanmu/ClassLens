# ClassLens Local Development Guide

## Prerequisites

- **Node.js**: 20.x or higher (`node -v`)
- **Python**: 3.12.x (`python3 --version`)
- **Package Managers**: `npm` 10+, `pip`, and virtual environment tool (`venv` or `uv`)
- **OS**: macOS, Linux, or WSL2 on Windows

---

## Initial Setup

### 1. Clone Repository & Setup Python Environment

```bash
git clone https://github.com/gihanmu/ClassLens.git
cd ClassLens

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python backend dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
npm --prefix apps/web ci
```

### 3. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key environment variables:
- `CLASSLENS_ENV`: Set to `development` for local work.
- `CLASSLENS_SECRET_KEY`: Set to a strong random 32+ character string.
- `CLASSLENS_AI_MODE`: Set to `mock` for zero-cost offline local development, or `vertex_ai` for live Gemini testing.
- `GOOGLE_CLOUD_PROJECT`: Required if testing Vertex AI live inference.
- `GOOGLE_CLOUD_LOCATION`: Vertex AI region (e.g., `asia-southeast1` or `us-central1`).
- `CLASSLENS_GCS_BUCKET`: Leave empty for local filesystem storage (`data/uploads/`).

### 4. Initialize Local Database and Teacher Account

Run the initialization script to create the local SQLite schema and seed the initial teacher account:

```bash
python3 scripts/init_teacher.py
```

This creates a default teacher login:
- **Email**: `teacher@classlens.edu`
- **Password**: `password123` (or the value set in `CLASSLENS_TEACHER_PASSWORD`)

---

## Running the Application

### Option A: Simultaneous Development Servers

In terminal 1 (Backend API):
```bash
source .venv/bin/activate
uvicorn services.api.main:app --host 127.0.0.1 --port 8000 --reload
```

In terminal 2 (Frontend Web):
```bash
npm --prefix apps/web run dev
```

Visit:
- Web Application: [http://localhost:3000](http://localhost:3000)
- API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs) (Enabled in `development` mode)
- Backend Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## Running Tests

### Backend Unit & Integration Tests

```bash
source .venv/bin/activate
pytest
```

Run specific test modules:
```bash
pytest tests/unit/test_math_verifier.py
pytest tests/unit/test_file_storage.py
pytest tests/integration/
```

### Frontend Build & Typecheck

```bash
npm --prefix apps/web run build
npm --prefix apps/web run lint
```

---

## Common Troubleshooting

| Issue | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'argon2'` | Backend venv missing dependencies | Run `pip install -r requirements.txt` inside `.venv` |
| `Failed to proxy http://127.0.0.1:8000: ECONNREFUSED` | FastAPI backend is not running | Start backend on port 8000 with `uvicorn services.api.main:app --reload` |
| `Invalid token or session expired` | Cookie expired or secret key changed | Navigate to `/login` and sign in again |
| `Insufficient Evidence on all live analyses` | Uploaded images unreadable or misrouted | Ensure worksheet images have legible handwriting and correct task type |
| Database state mismatch | Old schema in local SQLite database | Backup and remove `data/classlens.db`, then re-run `python3 scripts/init_teacher.py` |
