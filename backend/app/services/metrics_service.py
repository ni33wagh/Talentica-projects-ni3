import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from ..database import get_builds_collection, get_pipelines_collection
from ..models import Metrics, Build, Pipeline, PipelineHealth, BuildTrend, PipelineAdvice
from ..config import settings

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for calculating and managing pipeline metrics."""
    
    def __init__(self):
        self.builds_collection = get_builds_collection()
        self.pipelines_collection = get_pipelines_collection()
    
    async def calculate_pipeline_metrics(self, pipeline_id: str) -> Optional[Metrics]:
        """Calculate comprehensive metrics for a pipeline."""
        try:
            # Get pipeline information
            pipeline_doc = await self.pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
            if not pipeline_doc:
                return None
            
            pipeline_name = pipeline_doc["name"]
            
            # Get all builds for this pipeline
            builds_cursor = self.builds_collection.find({"pipeline_name": pipeline_name})
            builds = await builds_cursor.to_list(length=None)
            
            if not builds:
                return self._create_empty_metrics(pipeline_id, pipeline_name)
            
            # Calculate basic metrics
            total_builds = len(builds)
            success_count = sum(1 for build in builds if build["status"] == "SUCCESS")
            failure_count = sum(1 for build in builds if build["status"] in ["FAILURE", "ABORTED", "UNSTABLE"])
            
            success_rate = (success_count / total_builds) * 100 if total_builds > 0 else 0
            failure_rate = (failure_count / total_builds) * 100 if total_builds > 0 else 0
            
            # Calculate average duration
            durations = [build["duration"] for build in builds if build.get("duration")]
            average_duration = sum(durations) / len(durations) if durations else 0
            
            # Calculate recent build counts
            now = datetime.utcnow()
            builds_24h = sum(1 for build in builds if 
                           build["timestamp"] >= now - timedelta(days=1))
            builds_7d = sum(1 for build in builds if 
                           build["timestamp"] >= now - timedelta(days=7))
            
            # Determine health status
            health_status = self._determine_health_status(
                failure_rate, average_duration, pipeline_doc.get("failure_rate_threshold", 0.2)
            )
            
            # Get last build
            last_build = None
            if builds:
                latest_build = max(builds, key=lambda x: x["timestamp"])
                last_build = Build(
                    id=str(latest_build["_id"]),
                    pipeline_name=latest_build["pipeline_name"],
                    build_number=latest_build["build_number"],
                    status=latest_build["status"],
                    duration=latest_build.get("duration"),
                    timestamp=latest_build["timestamp"],
                    triggered_by=latest_build["triggered_by"],
                    branch=latest_build.get("branch"),
                    commit_hash=latest_build.get("commit_hash"),
                    url=latest_build.get("url"),
                    console_output=latest_build.get("console_output"),
                    parameters=latest_build.get("parameters"),
                    created_at=latest_build.get("created_at", now),
                    updated_at=latest_build.get("updated_at", now)
                )
            
            return Metrics(
                pipeline_id=pipeline_id,
                pipeline_name=pipeline_name,
                success_rate=success_rate,
                failure_rate=failure_rate,
                average_duration=average_duration,
                total_builds=total_builds,
                builds_last_24h=builds_24h,
                builds_last_7d=builds_7d,
                health_status=health_status,
                last_build=last_build
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics for pipeline {pipeline_id}: {e}")
            return None
    
    def _create_empty_metrics(self, pipeline_id: str, pipeline_name: str) -> Metrics:
        """Create empty metrics for a pipeline with no builds."""
        return Metrics(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            success_rate=0.0,
            failure_rate=0.0,
            average_duration=0.0,
            total_builds=0,
            builds_last_24h=0,
            builds_last_7d=0,
            health_status=PipelineHealth.HEALTHY,
            last_build=None
        )
    
    def _determine_health_status(self, failure_rate: float, avg_duration: float, threshold: float) -> PipelineHealth:
        """Determine pipeline health status based on metrics."""
        # Convert threshold to percentage
        threshold_percent = threshold * 100
        
        if failure_rate > threshold_percent:
            return PipelineHealth.UNHEALTHY
        elif failure_rate > threshold_percent * 0.7 or avg_duration > settings.build_time_threshold_minutes * 60:
            return PipelineHealth.WARNING
        else:
            return PipelineHealth.HEALTHY
    
    async def get_build_trends(self, pipeline_id: str, limit: int = 50) -> List[BuildTrend]:
        """Get build trends for chart visualization."""
        try:
            # Get pipeline name
            pipeline_doc = await self.pipelines_collection.find_one({"_id": ObjectId(pipeline_id)})
            if not pipeline_doc:
                return []
            
            pipeline_name = pipeline_doc["name"]
            
            # Get recent builds sorted by timestamp
            builds_cursor = self.builds_collection.find(
                {"pipeline_name": pipeline_name}
            ).sort("timestamp", -1).limit(limit)
            
            builds = await builds_cursor.to_list(length=limit)
            
            trends = []
            for build in builds:
                trends.append(BuildTrend(
                    timestamp=build["timestamp"],
                    duration=build.get("duration", 0),
                    status=build["status"],
                    build_number=build["build_number"]
                ))
            
            # Reverse to show chronological order
            return list(reversed(trends))
            
        except Exception as e:
            logger.error(f"Failed to get build trends for pipeline {pipeline_id}: {e}")
            return []
    
    async def get_overall_metrics(self) -> Dict[str, Any]:
        """Get overall metrics across all pipelines."""
        try:
            # Get all pipelines
            pipelines_cursor = self.pipelines_collection.find({})
            pipelines = await pipelines_cursor.to_list(length=None)
            
            total_pipelines = len(pipelines)
            healthy_pipelines = sum(1 for p in pipelines if p.get("health_status") == "HEALTHY")
            unhealthy_pipelines = sum(1 for p in pipelines if p.get("health_status") == "UNHEALTHY")
            
            # Get all builds for overall stats
            builds_cursor = self.builds_collection.find({})
            builds = await builds_cursor.to_list(length=None)
            
            total_builds = len(builds)
            success_count = sum(1 for build in builds if build["status"] == "SUCCESS")
            failure_count = sum(1 for build in builds if build["status"] in ["FAILURE", "ABORTED", "UNSTABLE"])
            
            overall_success_rate = (success_count / total_builds) * 100 if total_builds > 0 else 0
            
            # Calculate average build duration
            durations = [build["duration"] for build in builds if build.get("duration")]
            overall_avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Recent activity
            now = datetime.utcnow()
            builds_24h = sum(1 for build in builds if 
                           build["timestamp"] >= now - timedelta(days=1))
            builds_7d = sum(1 for build in builds if 
                           build["timestamp"] >= now - timedelta(days=7))
            
            return {
                "total_pipelines": total_pipelines,
                "healthy_pipelines": healthy_pipelines,
                "unhealthy_pipelines": unhealthy_pipelines,
                "total_builds": total_builds,
                "success_count": success_count,
                "failure_count": failure_count,
                "overall_success_rate": overall_success_rate,
                "overall_avg_duration": overall_avg_duration,
                "builds_last_24h": builds_24h,
                "builds_last_7d": builds_7d
            }
            
        except Exception as e:
            logger.error(f"Failed to get overall metrics: {e}")
            return {}
    
    async def generate_pipeline_advice(self, pipeline_id: str) -> List[PipelineAdvice]:
        """Generate improvement advice for a pipeline."""
        try:
            metrics = await self.calculate_pipeline_metrics(pipeline_id)
            if not metrics:
                return []
            
            advice_list = []
            
            # Check failure rate
            if metrics.failure_rate > 20:
                advice_list.append(PipelineAdvice(
                    pipeline_id=pipeline_id,
                    category="Reliability",
                    title="High Failure Rate Detected",
                    description=f"Pipeline has a {metrics.failure_rate:.1f}% failure rate, which is above the recommended threshold.",
                    priority="High",
                    action_items=[
                        "Review recent build failures and identify common patterns",
                        "Check for flaky tests and implement retry mechanisms",
                        "Review dependency management and version conflicts",
                        "Consider implementing better error handling in build scripts"
                    ],
                    documentation_links=[
                        "https://jenkins.io/doc/book/pipeline/best-practices/",
                        "https://www.jenkins.io/doc/book/pipeline/troubleshooting/"
                    ]
                ))
            
            # Check build duration
            if metrics.average_duration > 1800:  # 30 minutes
                advice_list.append(PipelineAdvice(
                    pipeline_id=pipeline_id,
                    category="Performance",
                    title="Long Build Duration",
                    description=f"Average build duration is {metrics.average_duration/60:.1f} minutes, which may impact development velocity.",
                    priority="Medium",
                    action_items=[
                        "Analyze build steps and identify bottlenecks",
                        "Consider parallelizing independent build steps",
                        "Review test execution time and optimize slow tests",
                        "Implement build caching for dependencies"
                    ],
                    documentation_links=[
                        "https://jenkins.io/doc/book/pipeline/best-practices/#parallel",
                        "https://www.jenkins.io/doc/book/pipeline/syntax/#parallel"
                    ]
                ))
            
            # Check recent activity
            if metrics.builds_last_24h == 0:
                advice_list.append(PipelineAdvice(
                    pipeline_id=pipeline_id,
                    category="Activity",
                    title="No Recent Build Activity",
                    description="No builds have been triggered in the last 24 hours.",
                    priority="Low",
                    action_items=[
                        "Verify the pipeline is still needed and active",
                        "Check if there are any issues preventing builds",
                        "Review pipeline configuration and triggers"
                    ],
                    documentation_links=[
                        "https://jenkins.io/doc/book/pipeline/syntax/#triggers"
                    ]
                ))
            
            # Check health status
            if metrics.health_status == PipelineHealth.UNHEALTHY:
                advice_list.append(PipelineAdvice(
                    pipeline_id=pipeline_id,
                    category="Health",
                    title="Pipeline Health Issues",
                    description="Pipeline is marked as unhealthy due to poor performance or reliability metrics.",
                    priority="High",
                    action_items=[
                        "Immediately review and address the root causes",
                        "Implement additional monitoring and alerting",
                        "Consider temporarily disabling the pipeline if critical",
                        "Plan for pipeline refactoring or replacement"
                    ],
                    documentation_links=[
                        "https://jenkins.io/doc/book/pipeline/best-practices/",
                        "https://www.jenkins.io/doc/book/pipeline/troubleshooting/"
                    ]
                ))
            
            return advice_list
            
        except Exception as e:
            logger.error(f"Failed to generate advice for pipeline {pipeline_id}: {e}")
            return []
    
    async def update_pipeline_health_status(self, pipeline_id: str) -> bool:
        """Update pipeline health status based on current metrics."""
        try:
            metrics = await self.calculate_pipeline_metrics(pipeline_id)
            if not metrics:
                return False
            
            # Update pipeline document with new health status and metrics
            await self.pipelines_collection.update_one(
                {"_id": ObjectId(pipeline_id)},
                {
                    "$set": {
                        "health_status": metrics.health_status.value,
                        "total_builds": metrics.total_builds,
                        "success_count": metrics.total_builds - int(metrics.failure_rate * metrics.total_builds / 100),
                        "failure_count": int(metrics.failure_rate * metrics.total_builds / 100),
                        "average_duration": metrics.average_duration,
                        "last_build_status": metrics.last_build.status if metrics.last_build else None,
                        "last_build_timestamp": metrics.last_build.timestamp if metrics.last_build else None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update health status for pipeline {pipeline_id}: {e}")
            return False


# Global metrics service instance
metrics_service = MetricsService()


