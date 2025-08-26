from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ...database import get_db
from ...services.jenkins import jenkins_client
from ...services.notification_service import notification_service
from ...services.job_monitor import job_monitor
from ...api.dependencies import check_jenkins_config
from ...config import settings

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/stats")
async def get_overall_stats(db: Session = Depends(get_db)):
    """Get overall Jenkins statistics and analytics."""
    try:
        stats = await jenkins_client.get_overall_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": "2025-08-26T03:30:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/trends")
async def get_build_trends(days: int = 30, db: Session = Depends(get_db)):
    """Get build trends and distribution data."""
    try:
        trends = await jenkins_client.get_build_trends(days=days)
        return {
            "success": True,
            "data": trends,
            "timestamp": "2025-08-26T03:30:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")

@router.get("/node-health")
async def get_node_health(db: Session = Depends(get_db)):
    """Get Jenkins node health information."""
    try:
        node_info = await jenkins_client.get_node_info()
        if not node_info:
            return {
                "success": True,
                "data": {
                    "nodes": [],
                    "total_nodes": 0,
                    "online_nodes": 0,
                    "offline_nodes": 0
                },
                "timestamp": "2025-08-26T03:30:00Z"
            }
        
        computers = node_info.get("computer", [])
        total_nodes = len(computers)
        online_nodes = sum(1 for node in computers if not node.get("offline", True))
        offline_nodes = total_nodes - online_nodes
        
        return {
            "success": True,
            "data": {
                "nodes": computers,
                "total_nodes": total_nodes,
                "online_nodes": online_nodes,
                "offline_nodes": offline_nodes
            },
            "timestamp": "2025-08-26T03:30:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node health: {str(e)}")

@router.get("/dashboard-summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get comprehensive dashboard summary with all key metrics."""
    try:
        # Get overall stats
        stats = await jenkins_client.get_overall_stats()
        
        # Get node health
        node_info = await jenkins_client.get_node_info()
        computers = node_info.get("computer", []) if node_info else []
        total_nodes = len(computers)
        online_nodes = sum(1 for node in computers if not node.get("offline", True))
        
        # Get recent trends
        trends = await jenkins_client.get_build_trends(days=7)
        
        summary = {
            "metrics": {
                "total_pipelines": stats.get("total_pipelines", 0),
                "total_builds": stats.get("total_builds", 0),
                "jobs_in_progress": stats.get("jobs_in_progress", 0),
                "successful_jobs": stats.get("successful_jobs", 0),
                "failed_jobs": stats.get("failed_jobs", 0),
                "avg_build_time": round(stats.get("avg_build_time", 0), 2),
                "success_rate": round(stats.get("success_rate", 0), 2),
                "failure_rate": round(stats.get("failure_rate", 0), 2)
            },
            "node_health": {
                "total_nodes": total_nodes,
                "online_nodes": online_nodes,
                "offline_nodes": total_nodes - online_nodes,
                "health_percentage": round((online_nodes / total_nodes * 100) if total_nodes > 0 else 0, 2)
            },
            "trends": trends,
            "last_updated": "2025-08-26T03:30:00Z"
        }
        
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard summary: {str(e)}")

@router.post("/notifications/test-email")
async def test_email_notification(db: Session = Depends(get_db)):
    """Test email notification functionality."""
    try:
        success = await notification_service.send_job_failure_notification(
            job_name="test-job",
            build_number=1,
            build_url="http://localhost:8080/job/test-job/1/",
            failure_reason="Test notification"
        )
        
        return {
            "success": success,
            "message": "Test email notification sent successfully" if success else "Failed to send test email"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")

@router.post("/notifications/clear-cache")
async def clear_notification_cache(db: Session = Depends(get_db)):
    """Clear notification cache."""
    try:
        notification_service.clear_sent_notifications()
        return {
            "success": True,
            "message": "Notification cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.post("/monitoring/start")
async def start_job_monitoring(db: Session = Depends(get_db)):
    """Start job monitoring service."""
    try:
        await job_monitor.start_monitoring()
        return {
            "success": True,
            "message": "Job monitoring started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.post("/monitoring/stop")
async def stop_job_monitoring(db: Session = Depends(get_db)):
    """Stop job monitoring service."""
    try:
        await job_monitor.stop_monitoring()
        return {
            "success": True,
            "message": "Job monitoring stopped successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

@router.get("/monitoring/status")
async def get_monitoring_status(db: Session = Depends(get_db)):
    """Get job monitoring status."""
    try:
        status = await job_monitor.get_monitoring_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")

@router.get("/config/debug")
async def get_config_debug():
    """Debug endpoint to check configuration."""
    return {
        "success": True,
        "data": {
            "smtp_server": settings.smtp_server,
            "smtp_port": settings.smtp_port,
            "smtp_username": settings.smtp_username,
            "smtp_password": "***" if settings.smtp_password else None,
            "from_email": settings.from_email,
            "to_email": settings.to_email,
            "jenkins_url": settings.jenkins_url,
            "jenkins_username": settings.jenkins_username,
            "jenkins_api_token": "***" if settings.jenkins_api_token else None
        }
    }
