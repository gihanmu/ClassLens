# ==============================================================================
# Google Cloud APIs Activation & Core Storage Resources
# ==============================================================================

locals {
  name_prefix = "${var.app_name}-${var.environment}"
}

# 1. Artifact Registry Repository for OCI Container Images
resource "google_artifact_registry_repository" "classlens" {
  location      = var.region
  repository_id = "${var.app_name}-repo"
  description   = "Docker repository for ClassLens frontend and backend images"
  format        = "DOCKER"

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = var.app_name
  }
}

# 2. Private Google Cloud Storage Bucket for Uploaded Student Worksheets
# Strict Security: Uniform bucket-level access, public access prevention, retention/versioning
resource "google_storage_bucket" "worksheets" {
  name                        = "${var.project_id}-${var.app_name}-worksheets"
  location                    = var.region
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 90 # Retain uploaded student worksheets for 90 days
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = var.app_name
  }
}

# 3. Google Secret Manager Secrets for Runtime Protection
resource "google_secret_manager_secret" "session_secret" {
  secret_id = "${local.name_prefix}-session-secret"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_secret_manager_secret" "teacher_password" {
  secret_id = "${local.name_prefix}-teacher-password"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_secret_manager_secret" "live_auth_key" {
  secret_id = "${local.name_prefix}-live-auth-key"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }
}
