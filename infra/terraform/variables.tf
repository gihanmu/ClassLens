variable "project_id" {
  type        = string
  description = "The Google Cloud project ID to deploy ClassLens into."
}

variable "region" {
  type        = string
  description = "Primary Google Cloud deployment region (default: asia-southeast1 Singapore)."
  default     = "asia-southeast1"
}

variable "environment" {
  type        = string
  description = "Deployment environment name (production, staging)."
  default     = "production"
}

variable "app_name" {
  type        = string
  description = "Application prefix for naming resources."
  default     = "classlens"
}

variable "frontend_image" {
  type        = string
  description = "Container image URI for the Next.js frontend."
  default     = ""
}

variable "backend_image" {
  type        = string
  description = "Container image URI for the FastAPI backend."
  default     = ""
}

variable "domain_name" {
  type        = string
  description = "Optional custom domain name for Google-managed SSL certificate (e.g. classlens.demo)."
  default     = ""
}

variable "gemini_model" {
  type        = string
  description = "Vertex AI Gemini multimodal vision model identifier."
  default     = "gemini-3.8-flash"
}

variable "min_scale" {
  type        = number
  description = "Minimum container instances (0 for scale-to-zero cost optimization)."
  default     = 0
}

variable "max_scale" {
  type        = number
  description = "Maximum container instances (conservative ceiling for hackathon cost control)."
  default     = 2
}

variable "enable_cloud_sql" {
  type        = bool
  description = "Set to true to provision a Cloud SQL PostgreSQL instance; false to use local SQLite or external DB."
  default     = false
}
