"""ClassLens FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import uuid
from services.api.config import settings
from services.api.routers import assessments, auth, cohort, dashboard, dev, responses

is_dev = settings.environment == "development"
settings.validate_production_configuration()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent multimodal math diagnostic platform for Singapore secondary education",
    docs_url="/docs" if is_dev else None,
    redoc_url="/redoc" if is_dev else None,
)


@app.middleware("http")
async def correlation_id_and_security_headers(request: Request, call_next):
    """Enriches requests with correlation IDs and attaches defense-in-depth security headers."""
    correlation_id = (
        request.headers.get("X-Correlation-ID")
        or request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )
    request.state.correlation_id = correlation_id

    response = await call_next(request)

    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(cohort.router, prefix="/api/v1")
app.include_router(responses.router, prefix="/api/v1")
app.include_router(dev.router, prefix="/api/v1")


@app.api_route("/health", methods=["GET", "HEAD"])
@app.api_route("/api/v1/health", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint for liveness, readiness, and post-deployment verification probes."""
    from services.api.repository.memory_repo import memory_repo

    db_backend = "postgresql" if memory_repo.db_manager.__class__.__name__ == "PostgresDatabaseManager" else "sqlite"
    db_healthy = True
    schema_version = "1.0.0"
    try:
        if hasattr(memory_repo.db_manager, "check_health"):
            db_healthy = bool(memory_repo.db_manager.check_health())
        sv = memory_repo.db_manager.get_metadata("schema_version")
        if sv:
            schema_version = sv
    except Exception:
        db_healthy = False

    storage_backend = "gcs" if settings.gcs_bucket else "local"

    return {
        "status": "ok" if db_healthy else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "queue_type": settings.queue_type,
        "ai_mode": settings.ai_mode,
        "is_live_authorized": settings.is_live_authorized(),
        "gemini_model": settings.gemini_model,
        "google_cloud_project": settings.google_cloud_project,
        "database_backend": db_backend,
        "database_healthy": db_healthy,
        "schema_version": schema_version,
        "storage_backend": storage_backend,
    }
