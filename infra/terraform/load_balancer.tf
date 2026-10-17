# ==============================================================================
# External HTTPS Application Load Balancer with Unified Path-Based Routing
# ==============================================================================

# 1. Global External Reserved IPv4 Address
resource "google_compute_global_address" "lb_ip" {
  name        = "${var.app_name}-lb-ip"
  description = "Static external IP for ClassLens HTTPS Application Load Balancer"
}

# 2. Backend Service for Next.js Frontend Serverless NEG
resource "google_compute_backend_service" "frontend" {
  name        = "${var.app_name}-frontend-backend-service"
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 60
  enable_cdn  = true

  backend {
    group = google_compute_region_network_endpoint_group.frontend_neg.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# 3. Backend Service for FastAPI Backend Serverless NEG
resource "google_compute_backend_service" "backend" {
  name        = "${var.app_name}-backend-backend-service"
  protocol    = "HTTPS"
  port_name   = "http"
  timeout_sec = 300 # Allow long multimodal analysis requests

  backend {
    group = google_compute_region_network_endpoint_group.backend_neg.id
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# 4. URL Map with Path-Based Unified Routing:
#    /        -> Next.js Frontend
#    /api/*   -> FastAPI Backend
#    /health  -> FastAPI Backend
resource "google_compute_url_map" "default" {
  name            = "${var.app_name}-url-map"
  default_service = google_compute_backend_service.frontend.id

  host_rule {
    hosts        = ["*"]
    path_matcher = "classlens-paths"
  }

  path_matcher {
    name            = "classlens-paths"
    default_service = google_compute_backend_service.frontend.id

    path_rule {
      paths   = ["/api/*", "/api", "/health"]
      service = google_compute_backend_service.backend.id
    }
  }
}

# 5. SSL Certificate Configuration
# If domain_name is provided, provision Google-managed cert. Otherwise provision a fallback self-managed cert.
resource "google_compute_managed_ssl_certificate" "managed_cert" {
  count = var.domain_name != "" ? 1 : 0
  name  = "${var.app_name}-managed-ssl-cert"

  managed {
    domains = [var.domain_name]
  }
}

resource "tls_private_key" "fallback" {
  count     = var.domain_name == "" ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_self_signed_cert" "fallback" {
  count           = var.domain_name == "" ? 1 : 0
  private_key_pem = tls_private_key.fallback[0].private_key_pem

  subject {
    common_name  = "classlens.demo"
    organization = "ClassLens EdTech"
  }

  validity_period_hours = 8760 # 1 year

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}

resource "google_compute_ssl_certificate" "self_signed" {
  count       = var.domain_name == "" ? 1 : 0
  name        = "${var.app_name}-self-signed-ssl-cert"
  private_key = tls_private_key.fallback[0].private_key_pem
  certificate = tls_self_signed_cert.fallback[0].cert_pem
}

# 6. Target HTTPS Proxy
resource "google_compute_target_https_proxy" "https_proxy" {
  name    = "${var.app_name}-https-proxy"
  url_map = google_compute_url_map.default.id
  ssl_certificates = var.domain_name != "" ? [
    google_compute_managed_ssl_certificate.managed_cert[0].id
    ] : [
    google_compute_ssl_certificate.self_signed[0].id
  ]
}

# 7. Global Forwarding Rule for HTTPS Traffic (Port 443)
resource "google_compute_global_forwarding_rule" "https" {
  name       = "${var.app_name}-https-forwarding-rule"
  target     = google_compute_target_https_proxy.https_proxy.id
  port_range = "443"
  ip_address = google_compute_global_address.lb_ip.address
}

# 8. HTTP-to-HTTPS Automatic Redirect
resource "google_compute_url_map" "http_redirect" {
  name = "${var.app_name}-http-redirect"

  default_url_redirect {
    https_redirect         = true
    strip_query            = false
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
  }
}

resource "google_compute_target_http_proxy" "http_proxy" {
  name    = "${var.app_name}-http-proxy"
  url_map = google_compute_url_map.http_redirect.id
}

resource "google_compute_global_forwarding_rule" "http" {
  name       = "${var.app_name}-http-forwarding-rule"
  target     = google_compute_target_http_proxy.http_proxy.id
  port_range = "80"
  ip_address = google_compute_global_address.lb_ip.address
}
