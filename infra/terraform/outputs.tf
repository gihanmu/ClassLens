# ==============================================================================
# Terraform Infrastructure Outputs
# ==============================================================================

output "load_balancer_ip" {
  description = "The static public IPv4 address of the HTTPS Application Load Balancer."
  value       = google_compute_global_address.lb_ip.address
}

output "application_url" {
  description = "The public application URL accessible by reviewers."
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${google_compute_global_address.lb_ip.address}"
}

output "worksheets_bucket" {
  description = "Google Cloud Storage bucket name for uploaded student worksheets."
  value       = google_storage_bucket.worksheets.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry Docker repository URL."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.classlens.repository_id}"
}

output "backend_service_account" {
  description = "Dedicated service account email for the backend service."
  value       = google_service_account.backend.email
}

output "frontend_service_account" {
  description = "Dedicated service account email for the frontend service."
  value       = google_service_account.frontend.email
}

output "cloud_run_backend_service" {
  description = "FastAPI backend Cloud Run service name."
  value       = google_cloud_run_v2_service.backend.name
}

output "cloud_run_frontend_service" {
  description = "Next.js frontend Cloud Run service name."
  value       = google_cloud_run_v2_service.frontend.name
}

output "cloud_sql_instance_name" {
  description = "Cloud SQL PostgreSQL instance connection name."
  value       = var.enable_cloud_sql ? google_sql_database_instance.postgres[0].connection_name : "none"
}

output "cloud_run_backend_url" {
  description = "Direct Cloud Run backend URL (internal ingress)."
  value       = google_cloud_run_v2_service.backend.uri
}

output "cloud_run_frontend_url" {
  description = "Direct Cloud Run frontend URL (internal ingress)."
  value       = google_cloud_run_v2_service.frontend.uri
}
