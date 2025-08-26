from fastapi import APIRouter, HTTPException
from datetime import datetime
import redis
from ...models import HealthCheck
from ...config import settings
from ...database import Database

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthCheck)
async def health_check():
    """Get overall system health status."""
    try:
        # Check database connection
        db_status = "healthy"
        try:
            await Database.client.admin.command('ping')
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check Redis connection
        redis_status = "healthy"
        try:
            redis_client = redis.from_url(settings.redis_url)
            redis_client.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
        
        # Determine overall status
        overall_status = "healthy"
        if "unhealthy" in db_status or "unhealthy" in redis_status:
            overall_status = "unhealthy"
        
        return HealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            database=db_status,
            redis=redis_status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/database")
async def database_health():
    """Check database connection specifically."""
    try:
        await Database.client.admin.command('ping')
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "database": "MongoDB",
            "message": "Database connection successful"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database health check failed: {str(e)}")


@router.get("/redis")
async def redis_health():
    """Check Redis connection specifically."""
    try:
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "service": "Redis",
            "message": "Redis connection successful"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis health check failed: {str(e)}")


@router.get("/jenkins")
async def jenkins_health():
    """Check Jenkins connection specifically."""
    try:
        from ...services.jenkins_service import jenkins_service
        
        if not jenkins_service.base_url:
            return {
                "status": "not_configured",
                "timestamp": datetime.utcnow(),
                "service": "Jenkins",
                "message": "Jenkins URL not configured"
            }
        
        # Try to get Jenkins info
        jobs = await jenkins_service.get_all_jobs()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "service": "Jenkins",
            "message": f"Jenkins connection successful, found {len(jobs)} jobs"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "service": "Jenkins",
            "message": f"Jenkins connection failed: {str(e)}"
        }


@router.get("/metrics")
async def system_metrics():
    """Get system metrics and performance data."""
    try:
        from ...services.metrics_service import metrics_service
        
        # Get overall metrics
        overall_metrics = await metrics_service.get_overall_metrics()
        
        # Get database stats
        db_stats = {}
        try:
            db = Database.get_database()
            db_stats = await db.command("dbStats")
        except Exception:
            db_stats = {"error": "Could not retrieve database stats"}
        
        return {
            "timestamp": datetime.utcnow(),
            "overall_metrics": overall_metrics,
            "database_stats": {
                "collections": db_stats.get("collections", 0),
                "data_size": db_stats.get("dataSize", 0),
                "storage_size": db_stats.get("storageSize", 0),
                "indexes": db_stats.get("indexes", 0),
                "index_size": db_stats.get("indexSize", 0)
            },
            "system_info": {
                "app_version": settings.app_version,
                "debug_mode": settings.debug,
                "mongodb_uri": settings.mongodb_uri.split("@")[-1] if "@" in settings.mongodb_uri else "configured",
                "redis_url": settings.redis_url.split("@")[-1] if "@" in settings.redis_url else "configured"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system metrics: {str(e)}")


@router.get("/ready")
async def readiness_check():
    """Check if the application is ready to serve requests."""
    try:
        # Check database
        await Database.client.admin.command('ping')
        
        # Check Redis
        redis_client = redis.from_url(settings.redis_url)
        redis_client.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
            "message": "Application is ready to serve requests"
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Application not ready: {str(e)}")


@router.get("/live")
async def liveness_check():
    """Check if the application is alive and running."""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow(),
        "message": "Application is alive"
    }


