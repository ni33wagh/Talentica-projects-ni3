from fastapi import HTTPException, status
from ..config import settings

def check_jenkins_config():
    """Check if Jenkins configuration is available."""
    if not all([settings.jenkins_url, settings.jenkins_username, settings.jenkins_api_token]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Jenkins configuration not available"
        )
