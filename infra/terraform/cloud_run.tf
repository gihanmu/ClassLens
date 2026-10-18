# ==============================================================================
# Cloud Run Services (Public Frontend BFF & Private IAM-Protected Backend)
# ==============================================================================

# 1. Cloud Run Next.js Frontend Service (Public HTTPS Entry Point + BFF Proxy)
resource "google_cloud_run_v2_service" "frontend" {
  name     = "${var.app_name}-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.frontend.email
    timeout         = "300s"

    scaling {
      min_instance_count = var.min_scale
      max_instance_count = var.max_scale
    }

    containers {
      image = var.frontend_image != "" ? var.frontend_image : "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.classlens.repository_id}/frontend:${var.image_tag}"

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
        name  = "INTERNAL_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = var.app_name
  }

  depends_on = [
    google_project_service.required_apis,
    google_cloud_run_v2_service.backend,
    google_project_iam_member.frontend_logging,
  ]
}

# 2. Cloud Run FastAPI Backend Service (Private IAM-Authenticated Service)
resource "google_cloud_run_v2_service" "backend" {
  name     = "${var.app_name}-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend.email
    timeout         = "300s"

    scaling {
      min_instance_count = var.min_scale
      max_instance_count = var.max_scale
    }

    containers {
      image = var.backend_image != "" ? var.backend_image : "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.classlens.repository_id}/backend:${var.image_tag}"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        timeout_seconds       = 5
        failure_threshold     = 12
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 15
        period_seconds        = 30
        timeout_seconds       = 5
        failure_threshold     = 3
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
        value = var.gemini_location
      }
      env {
        name  = "CLASSLENS_GEMINI_MODEL"
        value = var.gemini_model
      }
      env {
        name  = "CLASSLENS_AI_MODE"
        value = var.ai_mode
      }
      env {
        name  = "CLASSLENS_LIVE_INFERENCE_ENABLED"
        value = tostring(var.live_inference_enabled)
      }
      env {
        name  = "MOCK_LLM"
        value = var.ai_mode == "live" ? "false" : "true"
      }
      env {
        name  = "CLASSLENS_GCS_BUCKET"
        value = google_storage_bucket.worksheets.name
      }
      env {
        name  = "CLASSLENS_DB_POOL_MAX"
        value = "5"
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

      dynamic "env" {
        for_each = var.enable_cloud_sql ? [1] : []
        content {
          name = "CLASSLENS_DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.database_url[0].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "volume_mounts" {
        for_each = var.enable_cloud_sql ? [1] : []
        content {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }
    }

    dynamic "volumes" {
      for_each = var.enable_cloud_sql ? [1] : []
      content {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.postgres[0].connection_name]
        }
      }
    }
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
    application = var.app_name
  }

  depends_on = [
    google_project_service.required_apis,
    google_sql_database_instance.postgres,
    google_sql_database.app_db,
    google_sql_user.app_user,
    google_secret_manager_secret_version.database_url,
    google_secret_manager_secret_iam_member.backend_session_secret,
    google_secret_manager_secret_iam_member.backend_teacher_password,
    google_secret_manager_secret_iam_member.backend_live_auth_key,
    google_secret_manager_secret_iam_member.backend_database_url,
    google_project_iam_member.backend_cloudsql,
    google_project_iam_member.backend_vertex_ai,
    google_storage_bucket_iam_member.backend_storage_user,
  ]
}

# 3. Cloud Run IAM Invoker Bindings
# Frontend is publicly accessible via Google-managed HTTPS (*.a.run.app)
resource "google_cloud_run_v2_service_iam_member" "frontend_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Backend is strictly private: ONLY the Frontend Service Account can invoke it using OIDC identity tokens
resource "google_cloud_run_v2_service_iam_member" "backend_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.frontend.email}"
}
