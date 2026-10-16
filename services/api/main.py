"""ClassLens FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.api.config import settings
from services.api.routers import assessments, auth, cohort, dashboard, dev, responses

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent multimodal math diagnostic platform for Singapore secondary education",
    docs_url="/docs",
    redoc_url="/redoc",
)

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


@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for liveness and readiness probes."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "queue_type": settings.queue_type,
        "ai_mode": settings.ai_mode,
        "is_live_authorized": settings.is_live_authorized(),
        "gemini_model": settings.gemini_model,
        "google_cloud_project": settings.google_cloud_project,
    }
