import asyncio
import logging
from typing import Dict, Set
from datetime import datetime
from .jenkins import jenkins_client
from .notification_service import notification_service

logger = logging.getLogger(__name__)

class JobMonitor:
    def __init__(self):
        self.previous_job_states: Dict[str, Dict] = {}
        self.monitoring = False
        self.monitor_task = None

    async def start_monitoring(self):
        """Start monitoring Jenkins jobs for failures."""
        if self.monitoring:
            logger.info("Job monitoring is already running")
            return
        
        self.monitoring = True
        logger.info("Starting job monitoring service")
        
        # Start monitoring in background
        self.monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop monitoring Jenkins jobs."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Job monitoring service stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                await self._check_job_status()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in job monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _check_job_status(self):
        """Check for job status changes and send notifications."""
        try:
            # Get current job states
            jobs = await jenkins_client.list_jobs()
            current_states = {}
            
            for job in jobs:
                job_name = job.get('name')
                if not job_name:
                    continue
                
                current_states[job_name] = {
                    'color': job.get('color', ''),
                    'last_build': job.get('lastBuild'),
                    'last_successful': job.get('lastSuccessfulBuild'),
                    'last_failed': job.get('lastFailedBuild')
                }
                
                # Check if this is a new failure
                await self._check_job_failure(job_name, current_states[job_name])
            
            # Update previous states
            self.previous_job_states = current_states
            
        except Exception as e:
            logger.error(f"Error checking job status: {e}")

    async def _check_job_failure(self, job_name: str, current_state: Dict):
        """Check if a job has failed and send notification."""
        previous_state = self.previous_job_states.get(job_name)
        
        if not previous_state:
            # First time seeing this job, just record the state
            return
        
        current_color = current_state.get('color', '')
        previous_color = previous_state.get('color', '')
        
        # Check if job transitioned to failed state
        if (previous_color != 'red' and current_color == 'red' and 
            current_state.get('last_failed') and 
            current_state['last_failed'].get('number')):
            
            # Job has failed, send notification
            build_number = current_state['last_failed']['number']
            build_url = current_state['last_failed'].get('url', '')
            
            logger.info(f"Job {job_name} failed at build #{build_number}, sending notification")
            
            # Send email notification
            success = await notification_service.send_job_failure_notification(
                job_name=job_name,
                build_number=build_number,
                build_url=build_url,
                failure_reason="Build failed"
            )
            
            if success:
                logger.info(f"Failure notification sent for {job_name} #{build_number}")
            else:
                logger.error(f"Failed to send notification for {job_name} #{build_number}")

    async def get_monitoring_status(self) -> Dict:
        """Get current monitoring status."""
        return {
            "monitoring": self.monitoring,
            "jobs_tracked": len(self.previous_job_states),
            "last_check": datetime.now().isoformat()
        }

# Global job monitor instance
job_monitor = JobMonitor()
