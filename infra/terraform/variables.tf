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

variable "image_tag" {
  type        = string
  description = "Immutable container image tag (e.g. sha-<git_commit>). Mutable 'latest' is prohibited."
  default     = "sha-initial"

  validation {
    condition     = var.image_tag != "latest" && length(trimspace(var.image_tag)) > 0
    error_message = "Mutable 'latest' image tag is prohibited in production. Provide an immutable Git SHA tag."
  }
}

variable "frontend_image" {
  type        = string
  description = "Container image URI for the Next.js frontend (must use immutable tag or @sha256 digest)."
  default     = ""

  validation {
    condition     = var.frontend_image == "" || !endswith(var.frontend_image, ":latest")
    error_message = "frontend_image must not use a mutable ':latest' tag."
  }
}

variable "backend_image" {
  type        = string
  description = "Container image URI for the FastAPI backend (must use immutable tag or @sha256 digest)."
  default     = ""

  validation {
    condition     = var.backend_image == "" || !endswith(var.backend_image, ":latest")
    error_message = "backend_image must not use a mutable ':latest' tag."
  }
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
  description = "Provisions a managed Cloud SQL PostgreSQL instance (required for durable production persistence)."
  default     = true
}
