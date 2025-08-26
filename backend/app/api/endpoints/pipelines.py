from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from ...models import Pipeline, PipelineCreate, Metrics, BuildTrend, PipelineAdvice, PaginatedResponse
from ...database import get_pipelines_collection
from ...services.metrics_service import metrics_service
from ...services.jenkins_service import jenkins_service

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("/", response_model=PaginatedResponse)
async def get_pipelines(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    health_status: Optional[str] = Query(None, description="Filter by health status"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)")
):
    """Get paginated list of pipelines with optional filtering."""
    try:
        pipelines_collection = get_pipelines_collection()
        
        # Build filter query
        filter_query = {}
        if health_status:
            filter_query["health_status"] = health_status
        
        # Calculate skip value for pagination
        skip = (page - 1) * size
        
        # Determine sort order
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get total count
        total = await pipelines_collection.count_documents(filter_query)
        
        # Get pipelines with pagination
        pipelines_cursor = pipelines_collection.find(filter_query).sort(sort_by, sort_direction).skip(skip).limit(size)
        pipelines = await pipelines_cursor.to_list(length=size)
        
        # Convert to response models
        pipeline_models = []
        for pipeline in pipelines:
            pipeline_models.append(Pipeline(
                id=str(pipeline["_id"]),
                name=pipeline["name"],
                description=pipeline.get("description"),
                jenkins_job_name=pipeline.get("jenkins_job_name"),
                health_status=pipeline.get("health_status", "HEALTHY"),
                failure_rate_threshold=pipeline.get("failure_rate_threshold", 0.2),
                build_time_threshold=pipeline.get("build_time_threshold", 1800),
                notification_channels=pipeline.get("notification_channels", ["email"]),
                created_at=pipeline.get("created_at", datetime.utcnow()),
                updated_at=pipeline.get("updated_at", datetime.utcnow()),
                total_builds=pipeline.get("total_builds", 0),
                success_count=pipeline.get("success_count", 0),
                failure_count=pipeline.get("failure_count", 0),
                average_duration=pipeline.get("average_duration"),
                last_build_status=pipeline.get("last_build_status"),
                last_build_timestamp=pipeline.get("last_build_timestamp")
            ))
        
        # Calculate pagination info
        pages = (total + size - 1) // size
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedResponse(
            items=pipeline_models,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pipelines: {str(e)}")


@router.get("/{pipeline_id}", response_model=Pipeline)
async def get_pipeline(pipeline_id: str):
    """Get a specific pipeline by ID."""
    try:
        pipelines_collection = get_pipelines_collection()
        
        pipeline = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        return Pipeline(
            id=str(pipeline["_id"]),
            name=pipeline["name"],
            description=pipeline.get("description"),
            jenkins_job_name=pipeline.get("jenkins_job_name"),
            health_status=pipeline.get("health_status", "HEALTHY"),
            failure_rate_threshold=pipeline.get("failure_rate_threshold", 0.2),
            build_time_threshold=pipeline.get("build_time_threshold", 1800),
            notification_channels=pipeline.get("notification_channels", ["email"]),
            created_at=pipeline.get("created_at", datetime.utcnow()),
            updated_at=pipeline.get("updated_at", datetime.utcnow()),
            total_builds=pipeline.get("total_builds", 0),
            success_count=pipeline.get("success_count", 0),
            failure_count=pipeline.get("failure_count", 0),
            average_duration=pipeline.get("average_duration"),
            last_build_status=pipeline.get("last_build_status"),
            last_build_timestamp=pipeline.get("last_build_timestamp")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pipeline: {str(e)}")


@router.post("/", response_model=Pipeline)
async def create_pipeline(pipeline: PipelineCreate):
    """Create a new pipeline."""
    try:
        pipelines_collection = get_pipelines_collection()
        
        # Check if pipeline already exists
        existing_pipeline = await pipelines_collection.find_one({"name": pipeline.name})
        if existing_pipeline:
            raise HTTPException(status_code=409, detail="Pipeline already exists")
        
        # Prepare pipeline document
        pipeline_doc = pipeline.dict()
        pipeline_doc["created_at"] = datetime.utcnow()
        pipeline_doc["updated_at"] = datetime.utcnow()
        
        # Insert pipeline
        result = await pipelines_collection.insert_one(pipeline_doc)
        
        # Get the created pipeline
        created_pipeline = await pipelines_collection.find_one({"_id": result.inserted_id})
        
        return Pipeline(
            id=str(created_pipeline["_id"]),
            name=created_pipeline["name"],
            description=created_pipeline.get("description"),
            jenkins_job_name=created_pipeline.get("jenkins_job_name"),
            health_status=created_pipeline.get("health_status", "HEALTHY"),
            failure_rate_threshold=created_pipeline.get("failure_rate_threshold", 0.2),
            build_time_threshold=created_pipeline.get("build_time_threshold", 1800),
            notification_channels=created_pipeline.get("notification_channels", ["email"]),
            created_at=created_pipeline["created_at"],
            updated_at=created_pipeline["updated_at"],
            total_builds=0,
            success_count=0,
            failure_count=0,
            average_duration=None,
            last_build_status=None,
            last_build_timestamp=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pipeline: {str(e)}")


@router.put("/{pipeline_id}", response_model=Pipeline)
async def update_pipeline(pipeline_id: str, pipeline_update: PipelineCreate):
    """Update an existing pipeline."""
    try:
        pipelines_collection = get_pipelines_collection()
        
        # Check if pipeline exists
        existing_pipeline = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
        if not existing_pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Prepare update document
        update_doc = pipeline_update.dict()
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update pipeline
        await pipelines_collection.update_one(
            {"_id": ObjectId(pipeline_id)},
            {"$set": update_doc}
        )
        
        # Get the updated pipeline
        updated_pipeline = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
        
        return Pipeline(
            id=str(updated_pipeline["_id"]),
            name=updated_pipeline["name"],
            description=updated_pipeline.get("description"),
            jenkins_job_name=updated_pipeline.get("jenkins_job_name"),
            health_status=updated_pipeline.get("health_status", "HEALTHY"),
            failure_rate_threshold=updated_pipeline.get("failure_rate_threshold", 0.2),
            build_time_threshold=updated_pipeline.get("build_time_threshold", 1800),
            notification_channels=updated_pipeline.get("notification_channels", ["email"]),
            created_at=updated_pipeline["created_at"],
            updated_at=updated_pipeline["updated_at"],
            total_builds=updated_pipeline.get("total_builds", 0),
            success_count=updated_pipeline.get("success_count", 0),
            failure_count=updated_pipeline.get("failure_count", 0),
            average_duration=updated_pipeline.get("average_duration"),
            last_build_status=updated_pipeline.get("last_build_status"),
            last_build_timestamp=updated_pipeline.get("last_build_timestamp")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update pipeline: {str(e)}")


@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str):
    """Delete a pipeline."""
    try:
        pipelines_collection = get_pipelines_collection()
        
        result = await pipelines_collection.delete_one({"_id": ObjectId(pipeline_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        return {"message": "Pipeline deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete pipeline: {str(e)}")


@router.get("/{pipeline_id}/metrics", response_model=Metrics)
async def get_pipeline_metrics(pipeline_id: str):
    """Get metrics for a specific pipeline."""
    try:
        metrics = await metrics_service.calculate_pipeline_metrics(pipeline_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pipeline metrics: {str(e)}")


@router.get("/{pipeline_id}/trends", response_model=List[BuildTrend])
async def get_pipeline_trends(
    pipeline_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of builds to include in trends")
):
    """Get build trends for a specific pipeline."""
    try:
        trends = await metrics_service.get_build_trends(pipeline_id, limit)
        return trends
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pipeline trends: {str(e)}")


@router.get("/{pipeline_id}/advice", response_model=List[PipelineAdvice])
async def get_pipeline_advice(pipeline_id: str):
    """Get improvement advice for a specific pipeline."""
    try:
        advice = await metrics_service.generate_pipeline_advice(pipeline_id)
        return advice
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pipeline advice: {str(e)}")


@router.post("/{pipeline_id}/sync")
async def sync_pipeline_builds(pipeline_id: str):
    """Sync builds from Jenkins for a specific pipeline."""
    try:
        pipelines_collection = get_pipelines_collection()
        
        # Get pipeline information
        pipeline = await pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        jenkins_job_name = pipeline.get("jenkins_job_name")
        if not jenkins_job_name:
            raise HTTPException(status_code=400, detail="Pipeline not configured with Jenkins job name")
        
        # Sync builds from Jenkins
        builds = await jenkins_service.sync_job_builds(jenkins_job_name)
        
        # Update pipeline health status
        await metrics_service.update_pipeline_health_status(pipeline_id)
        
        return {
            "message": f"Successfully synced {len(builds)} builds from Jenkins",
            "builds_synced": len(builds)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync pipeline builds: {str(e)}")


@router.post("/{pipeline_id}/refresh")
async def refresh_pipeline_metrics(pipeline_id: str):
    """Refresh metrics and health status for a specific pipeline."""
    try:
        success = await metrics_service.update_pipeline_health_status(pipeline_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        return {"message": "Pipeline metrics refreshed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh pipeline metrics: {str(e)}")


@router.get("/stats/overview")
async def get_pipeline_stats():
    """Get overall pipeline statistics."""
    try:
        overall_metrics = await metrics_service.get_overall_metrics()
        return overall_metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pipeline stats: {str(e)}")


@router.get("/health/summary")
async def get_pipeline_health_summary():
    """Get summary of pipeline health statuses."""
    try:
        pipelines_collection = get_pipelines_collection()
        
        # Get pipelines by health status
        healthy_count = await pipelines_collection.count_documents({"health_status": "HEALTHY"})
        unhealthy_count = await pipelines_collection.count_documents({"health_status": "UNHEALTHY"})
        warning_count = await pipelines_collection.count_documents({"health_status": "WARNING"})
        total_count = await pipelines_collection.count_documents({})
        
        return {
            "total_pipelines": total_count,
            "healthy_pipelines": healthy_count,
            "unhealthy_pipelines": unhealthy_count,
            "warning_pipelines": warning_count,
            "health_percentage": round((healthy_count / total_count * 100), 2) if total_count > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve health summary: {str(e)}")


