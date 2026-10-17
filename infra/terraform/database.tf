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
    tier              = "db-f1-micro" # Minimum baseline tier for low cost
    availability_type = "ZONAL"       # Single-zone for hackathon cost control

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = false
      transaction_log_retention_days = 3
    }

    ip_configuration {
      ipv4_enabled = true # Supports Cloud SQL Auth Proxy connection
      require_ssl  = true
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
}

resource "google_secret_manager_secret_version" "db_password" {
  count       = var.enable_cloud_sql ? 1 : 0
  secret      = google_secret_manager_secret.db_password[0].id
  secret_data = random_password.db_password[0].result
}
