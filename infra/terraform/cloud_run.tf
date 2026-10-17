# ==============================================================================
# Cloud Run Services (Frontend & Backend) with Strict Ingress Security
# ==============================================================================

# 1. Cloud Run Next.js Frontend Service
resource "google_cloud_run_v2_service" "frontend" {
  name     = "${var.app_name}-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.frontend.email

    scaling {
      min_instance_count = var.min_scale
      max_instance_count = var.max_scale
    }

    containers {
      image = var.frontend_image != "" ? var.frontend_image : "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.classlens.repository_id}/frontend:latest"

      ports {
        container_port = 3000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "NODE_ENV"
        value = "production"
      }
      env {
        name  = "PORT"
        value = "3000"
      }
      env {
        name  = "INTERNAL_API_URL"
        value = "http://127.0.0.1:8000"
      }
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = var.app_name
  }
}

# 2. Serverless NEG for Frontend
resource "google_compute_region_network_endpoint_group" "frontend_neg" {
  name                  = "${var.app_name}-frontend-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.frontend.name
  }
}

# 3. Cloud Run FastAPI Backend Service
resource "google_cloud_run_v2_service" "backend" {
  name     = "${var.app_name}-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = var.min_scale
      max_instance_count = var.max_scale
    }

    containers {
      image = var.backend_image != "" ? var.backend_image : "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.classlens.repository_id}/backend:latest"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "CLASSLENS_GEMINI_MODEL"
        value = var.gemini_model
      }
      env {
        name  = "CLASSLENS_GCS_BUCKET"
        value = google_storage_bucket.worksheets.name
      }
      env {
        name  = "PORT"
        value = "8000"
      }

      # Secrets mounted from Secret Manager
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.session_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "CLASSLENS_DEMO_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.teacher_password.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "CLASSLENS_LIVE_AUTH_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.live_auth_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = var.app_name
  }
}

# 4. Serverless NEG for Backend
resource "google_compute_region_network_endpoint_group" "backend_neg" {
  name                  = "${var.app_name}-backend-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.backend.name
  }
}

# 5. Allow Load Balancer to invoke Cloud Run services
# Ingress is restricted to internal-and-cloud-load-balancing, so services are ONLY reachable via the LB
resource "google_cloud_run_v2_service_iam_member" "frontend_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "backend_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
