from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timedelta
from ...models import Build, BuildCreate, PaginationParams, PaginatedResponse
from ...database import get_builds_collection
from ...services.metrics_service import metrics_service

router = APIRouter(prefix="/builds", tags=["builds"])


@router.get("/", response_model=PaginatedResponse)
async def get_builds(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    pipeline_name: Optional[str] = Query(None, description="Filter by pipeline name"),
    status: Optional[str] = Query(None, description="Filter by build status"),
    triggered_by: Optional[str] = Query(None, description="Filter by user who triggered"),
    start_date: Optional[datetime] = Query(None, description="Filter builds after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter builds before this date"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)")
):
    """Get paginated list of builds with optional filtering."""
    try:
        builds_collection = get_builds_collection()
        
        # Build filter query
        filter_query = {}
        if pipeline_name:
            filter_query["pipeline_name"] = pipeline_name
        if status:
            filter_query["status"] = status
        if triggered_by:
            filter_query["triggered_by"] = triggered_by
        if start_date or end_date:
            filter_query["timestamp"] = {}
            if start_date:
                filter_query["timestamp"]["$gte"] = start_date
            if end_date:
                filter_query["timestamp"]["$lte"] = end_date
        
        # Calculate skip value for pagination
        skip = (page - 1) * size
        
        # Determine sort order
        sort_direction = -1 if sort_order.lower() == "desc" else 1
        
        # Get total count
        total = await builds_collection.count_documents(filter_query)
        
        # Get builds with pagination
        builds_cursor = builds_collection.find(filter_query).sort(sort_by, sort_direction).skip(skip).limit(size)
        builds = await builds_cursor.to_list(length=size)
        
        # Convert to response models
        build_models = []
        for build in builds:
            build_models.append(Build(
                id=str(build["_id"]),
                pipeline_name=build["pipeline_name"],
                build_number=build["build_number"],
                status=build["status"],
                duration=build.get("duration"),
                timestamp=build["timestamp"],
                triggered_by=build["triggered_by"],
                branch=build.get("branch"),
                commit_hash=build.get("commit_hash"),
                url=build.get("url"),
                console_output=build.get("console_output"),
                parameters=build.get("parameters"),
                created_at=build.get("created_at", datetime.utcnow()),
                updated_at=build.get("updated_at", datetime.utcnow())
            ))
        
        # Calculate pagination info
        pages = (total + size - 1) // size
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedResponse(
            items=build_models,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve builds: {str(e)}")


@router.get("/{build_id}", response_model=Build)
async def get_build(build_id: str):
    """Get a specific build by ID."""
    try:
        builds_collection = get_builds_collection()
        
        build = await builds_collection.find_one({"_id": ObjectId(build_id)})
        if not build:
            raise HTTPException(status_code=404, detail="Build not found")
        
        return Build(
            id=str(build["_id"]),
            pipeline_name=build["pipeline_name"],
            build_number=build["build_number"],
            status=build["status"],
            duration=build.get("duration"),
            timestamp=build["timestamp"],
            triggered_by=build["triggered_by"],
            branch=build.get("branch"),
            commit_hash=build.get("commit_hash"),
            url=build.get("url"),
            console_output=build.get("console_output"),
            parameters=build.get("parameters"),
            created_at=build.get("created_at", datetime.utcnow()),
            updated_at=build.get("updated_at", datetime.utcnow())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve build: {str(e)}")


@router.post("/", response_model=Build)
async def create_build(build: BuildCreate):
    """Create a new build record."""
    try:
        builds_collection = get_builds_collection()
        
        # Check if build already exists
        existing_build = await builds_collection.find_one({
            "pipeline_name": build.pipeline_name,
            "build_number": build.build_number
        })
        
        if existing_build:
            raise HTTPException(status_code=409, detail="Build already exists")
        
        # Prepare build document
        build_doc = build.dict()
        build_doc["created_at"] = datetime.utcnow()
        build_doc["updated_at"] = datetime.utcnow()
        
        # Insert build
        result = await builds_collection.insert_one(build_doc)
        
        # Get the created build
        created_build = await builds_collection.find_one({"_id": result.inserted_id})
        
        return Build(
            id=str(created_build["_id"]),
            pipeline_name=created_build["pipeline_name"],
            build_number=created_build["build_number"],
            status=created_build["status"],
            duration=created_build.get("duration"),
            timestamp=created_build["timestamp"],
            triggered_by=created_build["triggered_by"],
            branch=created_build.get("branch"),
            commit_hash=created_build.get("commit_hash"),
            url=created_build.get("url"),
            console_output=created_build.get("console_output"),
            parameters=created_build.get("parameters"),
            created_at=created_build["created_at"],
            updated_at=created_build["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create build: {str(e)}")


@router.put("/{build_id}", response_model=Build)
async def update_build(build_id: str, build_update: BuildCreate):
    """Update an existing build record."""
    try:
        builds_collection = get_builds_collection()
        
        # Check if build exists
        existing_build = await builds_collection.find_one({"_id": ObjectId(build_id)})
        if not existing_build:
            raise HTTPException(status_code=404, detail="Build not found")
        
        # Prepare update document
        update_doc = build_update.dict()
        update_doc["updated_at"] = datetime.utcnow()
        
        # Update build
        await builds_collection.update_one(
            {"_id": ObjectId(build_id)},
            {"$set": update_doc}
        )
        
        # Get the updated build
        updated_build = await builds_collection.find_one({"_id": ObjectId(build_id)})
        
        return Build(
            id=str(updated_build["_id"]),
            pipeline_name=updated_build["pipeline_name"],
            build_number=updated_build["build_number"],
            status=updated_build["status"],
            duration=updated_build.get("duration"),
            timestamp=updated_build["timestamp"],
            triggered_by=updated_build["triggered_by"],
            branch=updated_build.get("branch"),
            commit_hash=updated_build.get("commit_hash"),
            url=updated_build.get("url"),
            console_output=updated_build.get("console_output"),
            parameters=updated_build.get("parameters"),
            created_at=updated_build["created_at"],
            updated_at=updated_build["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update build: {str(e)}")


@router.delete("/{build_id}")
async def delete_build(build_id: str):
    """Delete a build record."""
    try:
        builds_collection = get_builds_collection()
        
        result = await builds_collection.delete_one({"_id": ObjectId(build_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Build not found")
        
        return {"message": "Build deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete build: {str(e)}")


@router.get("/pipeline/{pipeline_name}/recent", response_model=List[Build])
async def get_recent_builds(
    pipeline_name: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recent builds to return")
):
    """Get recent builds for a specific pipeline."""
    try:
        builds_collection = get_builds_collection()
        
        builds_cursor = builds_collection.find(
            {"pipeline_name": pipeline_name}
        ).sort("timestamp", -1).limit(limit)
        
        builds = await builds_cursor.to_list(length=limit)
        
        build_models = []
        for build in builds:
            build_models.append(Build(
                id=str(build["_id"]),
                pipeline_name=build["pipeline_name"],
                build_number=build["build_number"],
                status=build["status"],
                duration=build.get("duration"),
                timestamp=build["timestamp"],
                triggered_by=build["triggered_by"],
                branch=build.get("branch"),
                commit_hash=build.get("commit_hash"),
                url=build.get("url"),
                console_output=build.get("console_output"),
                parameters=build.get("parameters"),
                created_at=build.get("created_at", datetime.utcnow()),
                updated_at=build.get("updated_at", datetime.utcnow())
            ))
        
        return build_models
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve recent builds: {str(e)}")


@router.get("/stats/overview")
async def get_build_stats():
    """Get overall build statistics."""
    try:
        builds_collection = get_builds_collection()
        
        # Get total builds
        total_builds = await builds_collection.count_documents({})
        
        # Get builds by status
        success_count = await builds_collection.count_documents({"status": "SUCCESS"})
        failure_count = await builds_collection.count_documents({"status": {"$in": ["FAILURE", "ABORTED", "UNSTABLE"]}})
        
        # Get recent activity
        now = datetime.utcnow()
        builds_24h = await builds_collection.count_documents({
            "timestamp": {"$gte": now - timedelta(days=1)}
        })
        builds_7d = await builds_collection.count_documents({
            "timestamp": {"$gte": now - timedelta(days=7)}
        })
        
        # Calculate success rate
        success_rate = (success_count / total_builds * 100) if total_builds > 0 else 0
        
        return {
            "total_builds": total_builds,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": round(success_rate, 2),
            "builds_last_24h": builds_24h,
            "builds_last_7d": builds_7d
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve build stats: {str(e)}")


