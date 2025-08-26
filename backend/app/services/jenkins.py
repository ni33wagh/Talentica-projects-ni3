import httpx
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import os  # <-- added
from ..config import settings

logger = logging.getLogger(__name__)

class JenkinsClient:
    def __init__(self):
        self.base_url = settings.jenkins_url.rstrip('/')
        self.username = settings.jenkins_username
        self.api_token = settings.jenkins_api_token
        self._crumb = None
        self._crumb_field = None
        self._cache = {}
        self._cache_ttl = 5  # 5 seconds TTL

        # --- added: public URL for outward-facing links (e.g., browser/Slack) ---
        # Uses env var directly so we don't have to change your settings module.
        self.public_base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/") if os.getenv("PUBLIC_BASE_URL") else ""

    def _get_auth(self) -> tuple:
        """Get authentication credentials."""
        return (self.username, self.api_token)

    def _build_url(self, endpoint: str) -> str:
        """Build full URL for Jenkins API endpoint."""
        return f"{self.base_url}{endpoint}"

    def _get_cache_key(self, endpoint: str) -> str:
        """Generate cache key for endpoint."""
        return f"{self.base_url}{endpoint}"

    def _get_cached_response(self, key: str) -> Optional[Dict]:
        """Get cached response if not expired."""
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[key]
        return None

    def _set_cached_response(self, key: str, data: Dict):
        """Cache response with timestamp."""
        self._cache[key] = (time.time(), data)

    # ------------------------ URL REWRITE HELPERS (added) ------------------------
    def _rewrite_url(self, url: Optional[str]) -> Optional[str]:
        """
        Replace internal Jenkins URL prefix (self.base_url) with public_base_url once.
        No-op if PUBLIC_BASE_URL is unset or url doesn't start with internal base.
        """
        if not url:
            return url
        if self.public_base_url and self.base_url and url.startswith(self.base_url):
            return url.replace(self.base_url, self.public_base_url, 1)
        return url

    def _rewrite_job(self, job: Dict) -> Dict:
        if not isinstance(job, dict):
            return job
        if "url" in job:
            job["url"] = self._rewrite_url(job["url"])
        for k in ("lastBuild", "lastSuccessfulBuild", "lastFailedBuild"):
            v = job.get(k)
            if isinstance(v, dict) and "url" in v:
                v["url"] = self._rewrite_url(v["url"])
        return job

    def _rewrite_build(self, build: Dict) -> Dict:
        if not isinstance(build, dict):
            return build
        if "url" in build:
            build["url"] = self._rewrite_url(build["url"])
        return build
    # ---------------------------------------------------------------------------

    async def get_crumb(self) -> Optional[Dict]:
        """Get CSRF crumb for Jenkins API."""
        if self._crumb is None:
            try:
                url = self._build_url("/crumbIssuer/api/json")
                auth = self._get_auth()
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, auth=auth, timeout=10.0)
                    if response.status_code == 200:
                        crumb_data = response.json()
                        self._crumb = crumb_data.get("crumb")
                        self._crumb_field = crumb_data.get("crumbRequestField")
                        logger.info("CSRF crumb obtained successfully")
                    else:
                        logger.warning(f"Failed to get crumb: {response.status_code}")
            except Exception as e:
                logger.error(f"Error getting crumb: {e}")
        return {"crumb": self._crumb, "crumbRequestField": self._crumb_field}

    def _get_headers(self, include_crumb: bool = False) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if include_crumb and self._crumb and self._crumb_field:
            headers[self._crumb_field] = self._crumb
        return headers

    async def _make_request(self, endpoint: str, method: str = "GET", 
                          data: Optional[Dict] = None, include_crumb: bool = False) -> Optional[Dict]:
        """Make HTTP request to Jenkins API with retry logic."""
        url = self._build_url(endpoint)
        auth = self._get_auth()
        headers = self._get_headers(include_crumb)
        
        try:
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(url, auth=auth, headers=headers, timeout=10.0)
                elif method.upper() == "POST":
                    response = await client.post(url, auth=auth, headers=headers, json=data, timeout=10.0)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code == 403 and not include_crumb:
                    # Retry with crumb
                    await self.get_crumb()
                    headers = self._get_headers(include_crumb=True)
                    if method.upper() == "GET":
                        response = await client.get(url, auth=auth, headers=headers, timeout=10.0)
                    elif method.upper() == "POST":
                        response = await client.post(url, auth=auth, headers=headers, json=data, timeout=10.0)

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Jenkins API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error making request to {endpoint}: {e}")
            return None

    async def list_jobs(self) -> List[Dict]:
        """List all Jenkins jobs."""
        cache_key = self._get_cache_key("/api/json?tree=jobs[name,url,color,lastBuild,lastSuccessfulBuild,lastFailedBuild]")
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached

        result = await self._make_request("/api/json?tree=jobs[name,url,color,lastBuild,lastSuccessfulBuild,lastFailedBuild]")
        if result:
            jobs = result.get("jobs", [])
            # --- added: rewrite outgoing URLs ---
            jobs = [self._rewrite_job(j) for j in jobs]
            self._set_cached_response(cache_key, jobs)
            return jobs
        return []

    async def list_builds(self, job_name: str, limit: int = 25) -> List[Dict]:
        """List builds for a specific job."""
        cache_key = self._get_cache_key(f"/job/{job_name}/api/json?tree=builds[number,url,result,timestamp,duration,executor,description]&limit={limit}")
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached

        result = await self._make_request(f"/job/{job_name}/api/json?tree=builds[number,url,result,timestamp,duration,executor,description]&limit={limit}")
        if result:
            builds = result.get("builds", [])
            # --- added: rewrite outgoing URLs ---
            builds = [self._rewrite_build(b) for b in builds]
            self._set_cached_response(cache_key, builds)
            return builds
        return []

    async def get_build(self, job_name: str, build_number: int) -> Optional[Dict]:
        """Get detailed information for a specific build."""
        cache_key = self._get_cache_key(f"/job/{job_name}/{build_number}/api/json")
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached

        result = await self._make_request(f"/job/{job_name}/{build_number}/api/json")
        if result:
            # --- added: rewrite outgoing URL if present ---
            if isinstance(result, dict) and "url" in result:
                result["url"] = self._rewrite_url(result["url"])
            self._set_cached_response(cache_key, result)
            return result
        return None

    async def get_node_info(self) -> Optional[Dict]:
        """Get Jenkins node information and health."""
        cache_key = self._get_cache_key("/computer/api/json?tree=computer[displayName,offline,executors,monitorData]")
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached

        result = await self._make_request("/computer/api/json?tree=computer[displayName,offline,executors,monitorData]")
        if result:
            self._set_cached_response(cache_key, result)
            return result
        return None

    async def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall Jenkins statistics and analytics."""
        cache_key = self._get_cache_key("/api/json?tree=jobs[name,color,lastBuild,lastSuccessfulBuild,lastFailedBuild]")
        cached = self._get_cached_response(cache_key)
        if cached:
            return cached

        result = await self._make_request("/api/json?tree=jobs[name,color,lastBuild,lastSuccessfulBuild,lastFailedBuild]")
        if not result:
            return {}

        jobs = result.get("jobs", [])
        # --- added: make stats consistent with public URLs if needed ---
        jobs = [self._rewrite_job(j) for j in jobs]
        
        # Calculate statistics
        total_pipelines = len(jobs)
        total_builds = 0
        jobs_in_progress = 0
        successful_jobs = 0
        failed_jobs = 0
        build_times = []
        
        for job in jobs:
            color = job.get("color", "")
            last_build = job.get("lastBuild")
            
            if last_build:
                total_builds += 1
                if last_build.get("duration"):
                    build_times.append(last_build.get("duration", 0) / 1000)  # Convert to seconds
            
            if "anime" in color:  # Job is building
                jobs_in_progress += 1
            elif "blue" in color:  # Successful
                successful_jobs += 1
            elif "red" in color:  # Failed
                failed_jobs += 1

        # Calculate averages and rates
        avg_build_time = sum(build_times) / len(build_times) if build_times else 0
        success_rate = (successful_jobs / total_pipelines * 100) if total_pipelines > 0 else 0
        failure_rate = (failed_jobs / total_pipelines * 100) if total_pipelines > 0 else 0

        stats = {
            "total_pipelines": total_pipelines,
            "total_builds": total_builds,
            "jobs_in_progress": jobs_in_progress,
            "successful_jobs": successful_jobs,
            "failed_jobs": failed_jobs,
            "avg_build_time": avg_build_time,
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "build_times": build_times
        }
        
        self._set_cached_response(cache_key, stats)
        return stats

    async def get_build_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get build trends over time."""
        jobs = await self.list_jobs()
        trends = {
            "build_status_distribution": {},
            "job_distribution": {},
            "build_duration_trend": []
        }
        
        # Collect build data
        for job in jobs:
            job_name = job.get("name", "")
            builds = await self.list_builds(job_name, limit=50)
            
            for build in builds:
                result = build.get("result")
                if result:
                    trends["build_status_distribution"][result] = trends["build_status_distribution"].get(result, 0) + 1
                
                duration = build.get("duration", 0)
                if duration > 0:
                    trends["build_duration_trend"].append({
                        "job": job_name,
                        "build": build.get("number"),
                        "duration": duration / 1000,  # Convert to seconds
                        "timestamp": build.get("timestamp", 0)
                    })
            
            # Job distribution
            color = job.get("color", "")
            if "blue" in color:
                trends["job_distribution"]["success"] = trends["job_distribution"].get("success", 0) + 1
            elif "red" in color:
                trends["job_distribution"]["failed"] = trends["job_distribution"].get("failed", 0) + 1
            elif "anime" in color:
                trends["job_distribution"]["building"] = trends["job_distribution"].get("building", 0) + 1
            else:
                trends["job_distribution"]["not_built"] = trends["job_distribution"].get("not_built", 0) + 1

        return trends

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()
        self._crumb = None
        self._crumb_field = None
        logger.info("Jenkins client cache cleared")

# Global Jenkins client instance
jenkins_client = JenkinsClient()

