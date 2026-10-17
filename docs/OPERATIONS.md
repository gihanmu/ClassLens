# ClassLens Operations & Observability Guide

## System Health & Probes

### Health Check Endpoint
- **Path**: `GET /health`
- **Port**: 8000 (proxied via Load Balancer)
- **Response Format**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "environment": "production"
  }
```
- **Probe Configuration**:
  - Initial delay: 5 seconds
  - Period: 15 seconds
  - Timeout: 3 seconds
  - Unhealthy threshold: 3 failures

---

## Logging & Distributed Tracing

### 1. Structured Logging
The application formats log output to stdout/stderr in Cloud Logging compatible format:
- Request method, path, status code, latency.
- Component namespace (e.g. `services.api.analysis.math_verifier`).
- Error stack traces with safe redaction (credentials, tokens, and PII are never logged).

### 2. Request Correlation IDs
Every incoming HTTP request is assigned a unique UUID4 correlation ID via `CorrelationIdMiddleware`:
- Injected into response headers as `X-Correlation-ID`.
- Accessible in Cloud Logging by querying:
  ```
  resource.type="cloud_run_revision"
  jsonPayload.correlation_id="<ID>"
  ```

### 3. Cloud Trace Integration
When enabled, trace context propagates from the Load Balancer through Cloud Run revisions to downstream Vertex AI calls, permitting end-to-end latency waterfall inspection.

---

## Recommended Alerting Policies (Terraform PromQL / Cloud Monitoring)

1. **High 5xx Server Error Rate**:
   - Condition: Error rate > 2% of total requests over a 5-minute window.
   - Severity: Critical (Page on-call).
2. **Elevated Request Latency**:
   - Condition: 95th percentile latency > 2,500ms over 10 minutes.
   - Severity: Warning (High AI inference load or cold starts).
3. **Container Instance Saturation**:
   - Condition: CPU or memory utilization > 80% for 5 consecutive minutes.
   - Severity: Warning (Autoscaling max instances may require increase).
4. **Login Brute Force Anomalies**:
   - Condition: 429 response count > 50 in 5 minutes.
   - Severity: Warning (Potential credential stuffing attempt).

---

## Backup & Disaster Recovery

### 1. Worksheet Uploads (GCS)
- Private GCS bucket configured with Object Versioning (30-day retention).
- Soft-delete enabled (7-day recovery window for accidentally removed objects).

### 2. Database Backup (Cloud SQL)
- Automated daily backups enabled.
- Point-in-time recovery (PITR) with binary logging enabled.

---

## Revision Rollbacks

To revert to a previous stable revision in Google Cloud Run:

```bash
# Interactive or automatic rollback:
./scripts/gcp/rollback.sh --service backend
./scripts/gcp/rollback.sh --service frontend
```

Or via direct Google Cloud CLI:
```bash
gcloud run services update-traffic classlens-backend \
  --to-revisions=classlens-backend-00004-xyz=100 \
  --region=asia-southeast1
```
Traffic switch is instantaneous (<100ms) with zero dropped connections.
