# ==============================================================================
# Least-Privilege IAM & Service Account Definitions
# ==============================================================================

# 1. Dedicated Service Account for FastAPI Backend
resource "google_service_account" "backend" {
  account_id   = "${var.app_name}-backend-sa"
  display_name = "ClassLens Backend Runtime Service Account"
  description  = "Dedicated least-privilege identity for ClassLens FastAPI backend service"
}

# 2. Dedicated Service Account for Next.js Frontend
resource "google_service_account" "frontend" {
  account_id   = "${var.app_name}-frontend-sa"
  display_name = "ClassLens Frontend Runtime Service Account"
  description  = "Dedicated least-privilege identity for ClassLens Next.js frontend service"
}

# 3. Vertex AI Access for Backend (Gemini Multimodal Vision Inference)
resource "google_project_iam_member" "backend_vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# 4. Cloud Logging & Cloud Trace Permissions for Observability
resource "google_project_iam_member" "backend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_trace" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "frontend_logging" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.frontend.email}"
}

# 5. Fine-Grained Storage Object User on Worksheets Bucket Only
resource "google_storage_bucket_iam_member" "backend_storage_user" {
  bucket = google_storage_bucket.worksheets.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.backend.email}"
}

# 6. Secret Manager Access for Application Secrets
resource "google_secret_manager_secret_iam_member" "backend_session_secret" {
  secret_id = google_secret_manager_secret.session_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_teacher_password" {
  secret_id = google_secret_manager_secret.teacher_password.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_live_auth_key" {
  secret_id = google_secret_manager_secret.live_auth_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_secret_manager_secret_iam_member" "backend_database_url" {
  count     = var.enable_cloud_sql ? 1 : 0
  secret_id = google_secret_manager_secret.database_url[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

# 7. Cloud SQL Client Role for Backend Service Account
resource "google_project_iam_member" "backend_cloudsql" {
  count   = var.enable_cloud_sql ? 1 : 0
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.backend.email}"
}
