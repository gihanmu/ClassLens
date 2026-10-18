# ==============================================================================
# Optional Managed Cloud SQL PostgreSQL Architecture
# ==============================================================================

resource "random_password" "db_password" {
  count   = var.enable_cloud_sql ? 1 : 0
  length  = 24
  special = false
}

resource "google_sql_database_instance" "postgres" {
  count            = var.enable_cloud_sql ? 1 : 0
  name             = "${var.app_name}-${var.environment}-pg"
  database_version = "POSTGRES_15"
  region           = var.region

  deletion_protection = true # Safeguard against accidental destruction

  settings {
    tier                  = var.db_tier  # db-f1-micro minimum baseline tier for low cost
    edition               = "ENTERPRISE" # Required for shared-core db-f1-micro in Google Provider v5+
    availability_type     = "ZONAL"      # Single-zone for hackathon cost control
    disk_type             = "PD_SSD"
    disk_size             = 10 # Minimum 10 GB SSD
    disk_autoresize       = true
    disk_autoresize_limit = 20 # Cap storage growth at 20 GB for budget protection

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = false
      transaction_log_retention_days = 3
    }

    ip_configuration {
      # Public IPv4 is enabled ONLY for IAM-authenticated Cloud SQL Auth Proxy tunnel;
      # zero authorized_networks blocks all direct public network access.
      # Unix domain socket connections from Cloud Run (/cloudsql/...) are local to the proxy
      # after TLS termination, so require_ssl must be false to prevent Unix socket rejection.
      ipv4_enabled = true
      require_ssl  = false
    }

    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = false
      record_client_address   = false
    }

    user_labels = {
      environment = var.environment
      managed_by  = "terraform"
      application = var.app_name
    }
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_sql_database" "app_db" {
  count    = var.enable_cloud_sql ? 1 : 0
  name     = "classlens"
  instance = google_sql_database_instance.postgres[0].name
}

resource "google_sql_user" "app_user" {
  count    = var.enable_cloud_sql ? 1 : 0
  name     = "classlens_app"
  instance = google_sql_database_instance.postgres[0].name
  password = random_password.db_password[0].result
}

# Store database password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  count     = var.enable_cloud_sql ? 1 : 0
  secret_id = "${var.app_name}-${var.environment}-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "db_password" {
  count       = var.enable_cloud_sql ? 1 : 0
  secret      = google_secret_manager_secret.db_password[0].id
  secret_data = random_password.db_password[0].result
}

# Store complete PostgreSQL connection URL in Secret Manager for Cloud Run mounting
resource "google_secret_manager_secret" "database_url" {
  count     = var.enable_cloud_sql ? 1 : 0
  secret_id = "${var.app_name}-${var.environment}-database-url"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "database_url" {
  count       = var.enable_cloud_sql ? 1 : 0
  secret      = google_secret_manager_secret.database_url[0].id
  secret_data = "postgresql://classlens_app:${random_password.db_password[0].result}@/classlens?host=/cloudsql/${google_sql_database_instance.postgres[0].connection_name}"

  depends_on = [
    google_sql_database.app_db,
    google_sql_user.app_user,
  ]
}
