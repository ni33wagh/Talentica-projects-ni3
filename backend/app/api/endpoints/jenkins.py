from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from ...services.jenkins import jenkins_client
from ...config import settings

router = APIRouter(prefix="/jenkins", tags=["jenkins"])


async def check_jenkins_config():
    """Check if Jenkins is properly configured."""
    if not all([settings.jenkins_url, settings.jenkins_username, settings.jenkins_api_token]):
        raise HTTPException(
            status_code=503,
            detail="Jenkins not configured. Please set JENKINS_URL, JENKINS_USERNAME, and JENKINS_API_TOKEN"
        )


@router.get("/jobs", response_model=List[Dict[str, Any]])
async def get_jobs(_: None = Depends(check_jenkins_config)):
    """Get list of all Jenkins jobs."""
    try:
        jobs = await jenkins_client.list_jobs()
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")


@router.get("/jobs/{job_name}/builds", response_model=List[Dict[str, Any]])
async def get_job_builds(
    job_name: str, 
    limit: int = 25,
    _: None = Depends(check_jenkins_config)
):
    """Get builds for a specific job."""
    if limit > 100:
        limit = 100  # Cap at 100 builds
    
    try:
        builds = await jenkins_client.list_builds(job_name, limit)
        return builds
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch builds for job {job_name}: {str(e)}"
        )


@router.get("/jobs/{job_name}/builds/{build_number}", response_model=Dict[str, Any])
async def get_build(
    job_name: str, 
    build_number: int,
    _: None = Depends(check_jenkins_config)
):
    """Get detailed information about a specific build."""
    try:
        build = await jenkins_client.get_build(job_name, build_number)
        if not build:
            raise HTTPException(
                status_code=404, 
                detail=f"Build {build_number} not found for job {job_name}"
            )
        return build
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch build {build_number} for job {job_name}: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache(_: None = Depends(check_jenkins_config)):
    """Clear the Jenkins cache."""
    try:
        jenkins_client.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
