# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from .config import settings
from .database import init_db, close_db
from .api.endpoints import jenkins, analytics
from .services.job_monitor import job_monitor

# Try to import the dashboard router from common locations without breaking existing code
try:
    # Preferred: consistent with your existing endpoints layout
    from .api.endpoints import dashboard as dashboard_router  # type: ignore
except Exception:
    try:
        # Fallback to absolute import path as in your snippet
        from app.routers import dashboard as dashboard_router  # type: ignore
    except Exception:
        dashboard_router = None  # Router not present; we'll include it conditionally

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="CI/CD Health Dashboard API"
)

from app.routers import dashboard as dashboard_router
app.include_router(dashboard_router.router)

from app.routers import stream as stream_router
app.include_router(stream_router.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    # Start job monitoring service
    await job_monitor.start_monitoring()

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown."""
    await job_monitor.stop_monitoring()
    close_db()

# CORS middleware for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "backend"
    }

@app.get("/api/version")
async def get_version():
    """Get API version information."""
    return {
        "version": settings.app_version,
        "name": settings.app_name,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CI/CD Health Dashboard API",
        "version": settings.app_version,
        "docs": "/docs"
    }

# EXISTING routers (keep)
app.include_router(jenkins.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")

# --- Added exactly as requested (with /api prefix to match your API shape) ---
from app.routers import dashboard as dashboard_router  # type: ignore
app.include_router(dashboard_router.router, prefix="/api")
setattr(dashboard_router, "_included", True)
# ---------------------------------------------------------------------------

# NEW: dashboard router (included only if import succeeded and not already included)
if dashboard_router and hasattr(dashboard_router, "router") and not getattr(dashboard_router, "_included", False):
    app.include_router(dashboard_router.router, prefix="/api")

# === Compat router for legacy frontend endpoints ===
from app.routers import compat as compat_router  # type: ignore
app.include_router(compat_router.router)
# ===================================================

