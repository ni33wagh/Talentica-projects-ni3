import httpx
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..config import settings
from ..models import Build, Pipeline, BuildStatus

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via Slack and Email."""
    
    def __init__(self):
        self.slack_webhook_url = settings.slack_webhook_url
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
        self.to_email = settings.to_email
        self._sent_notifications = set()  # Track sent notifications to avoid duplicates
    
    async def send_slack_notification(self, build: Build, pipeline: Pipeline, message: str) -> bool:
        """Send notification to Slack."""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        try:
            # Create Slack message with rich formatting
            slack_message = self._format_slack_message(build, pipeline, message)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.slack_webhook_url,
                    json=slack_message,
                    timeout=30.0
                )
                response.raise_for_status()
                logger.info(f"Slack notification sent for build {build.build_number}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    def send_email_notification(self, build: Build, pipeline: Pipeline, message: str, recipients: List[str]) -> bool:
        """Send notification via email."""
        if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
            logger.warning("SMTP configuration incomplete")
            return False
        
        try:
            # Create email content
            subject, html_content, text_content = self._format_email_content(build, pipeline, message)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = ', '.join(recipients)
            
            # Attach both HTML and text versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent for build {build.build_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _format_slack_message(self, build: Build, pipeline: Pipeline, message: str) -> Dict[str, Any]:
        """Format message for Slack with rich formatting."""
        # Determine color based on build status
        color_map = {
            BuildStatus.SUCCESS: "good",
            BuildStatus.FAILURE: "danger",
            BuildStatus.ABORTED: "warning",
            BuildStatus.UNSTABLE: "warning",
            BuildStatus.IN_PROGRESS: "#439FE0",
            BuildStatus.QUEUED: "#95A5A6"
        }
        
        color = color_map.get(build.status, "#95A5A6")
        
        # Format duration
        duration_str = "N/A"
        if build.duration:
            minutes = build.duration // 60
            seconds = build.duration % 60
            duration_str = f"{minutes}m {seconds}s"
        
        # Create fields for Slack attachment
        fields = [
            {
                "title": "Pipeline",
                "value": pipeline.name,
                "short": True
            },
            {
                "title": "Build Number",
                "value": str(build.build_number),
                "short": True
            },
            {
                "title": "Status",
                "value": build.status.value,
                "short": True
            },
            {
                "title": "Duration",
                "value": duration_str,
                "short": True
            },
            {
                "title": "Triggered By",
                "value": build.triggered_by,
                "short": True
            },
            {
                "title": "Branch",
                "value": build.branch or "N/A",
                "short": True
            }
        ]
        
        # Add timestamp
        timestamp = int(build.timestamp.timestamp())
        
        attachment = {
            "color": color,
            "title": f"Build #{build.build_number} - {build.status.value}",
            "title_link": build.url,
            "text": message,
            "fields": fields,
            "footer": "CI/CD Health Dashboard",
            "ts": timestamp
        }
        
        return {
            "attachments": [attachment]
        }
    
    def _format_email_content(self, build: Build, pipeline: Pipeline, message: str) -> tuple:
        """Format email content with HTML and text versions."""
        # Determine status color
        status_colors = {
            BuildStatus.SUCCESS: "#28a745",
            BuildStatus.FAILURE: "#dc3545",
            BuildStatus.ABORTED: "#ffc107",
            BuildStatus.UNSTABLE: "#fd7e14",
            BuildStatus.IN_PROGRESS: "#17a2b8",
            BuildStatus.QUEUED: "#6c757d"
        }
        
        status_color = status_colors.get(build.status, "#6c757d")
        
        # Format duration
        duration_str = "N/A"
        if build.duration:
            minutes = build.duration // 60
            seconds = build.duration % 60
            duration_str = f"{minutes}m {seconds}s"
        
        # HTML version
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .status {{ display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }}
                .details {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .detail-label {{ font-weight: bold; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>CI/CD Build Notification</h1>
                    <p>{message}</p>
                </div>
                
                <div class="details">
                    <div class="detail-row">
                        <span class="detail-label">Pipeline:</span>
                        <span>{pipeline.name}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Build Number:</span>
                        <span>#{build.build_number}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Status:</span>
                        <span class="status" style="background-color: {status_color};">{build.status.value}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Duration:</span>
                        <span>{duration_str}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Triggered By:</span>
                        <span>{build.triggered_by}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Branch:</span>
                        <span>{build.branch or 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Timestamp:</span>
                        <span>{build.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
                    </div>
                </div>
                
                {f'<a href="{build.url}" class="button">View Build Details</a>' if build.url else ''}
                
                <div class="footer">
                    <p>This notification was sent by the CI/CD Health Dashboard.</p>
                    <p>Build ID: {build.id}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Text version
        text_content = f"""
CI/CD Build Notification

{message}

Pipeline: {pipeline.name}
Build Number: #{build.build_number}
Status: {build.status.value}
Duration: {duration_str}
Triggered By: {build.triggered_by}
Branch: {build.branch or 'N/A'}
Timestamp: {build.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

{f'View Build Details: {build.url}' if build.url else ''}

---
This notification was sent by the CI/CD Health Dashboard.
Build ID: {build.id}
        """
        
        subject = f"Build #{build.build_number} - {build.status.value} - {pipeline.name}"
        
        return subject, html_content, text_content
    
    def _get_remediation_advice(self, build: Build, pipeline: Pipeline) -> str:
        """Get remediation advice based on build status and pipeline health."""
        if build.status == BuildStatus.SUCCESS:
            return "Build completed successfully!"
        
        advice = []
        
        if build.status == BuildStatus.FAILURE:
            advice.append("• Check the build logs for specific error messages")
            advice.append("• Verify that all dependencies are available")
            advice.append("• Review recent code changes that might have caused the failure")
        
        if build.status == BuildStatus.TIMEOUT:
            advice.append("• Consider optimizing build performance")
            advice.append("• Review resource allocation for the build")
            advice.append("• Check for long-running tests or processes")
        
        if build.duration and build.duration > pipeline.build_time_threshold:
            advice.append("• Build duration exceeds threshold - consider optimization")
            advice.append("• Review test execution time and parallelization")
            advice.append("• Check for unnecessary dependencies or steps")
        
        if pipeline.health_status.value == "UNHEALTHY":
            advice.append("• Pipeline health is poor - review recent failures")
            advice.append("• Consider implementing additional monitoring")
            advice.append("• Review pipeline configuration and dependencies")
        
        return "\n".join(advice) if advice else "No specific advice available."
    
    async def send_build_notification(self, build: Build, pipeline: Pipeline, notification_type: str = "all") -> bool:
        """Send notification for a build based on configuration."""
        success = True
        
        # Determine if we should send notifications
        should_notify = (
            build.status in [BuildStatus.FAILURE, BuildStatus.ABORTED, BuildStatus.UNSTABLE] or
            (build.duration and build.duration > pipeline.build_time_threshold)
        )
        
        if not should_notify:
            return True
        
        # Create notification message
        message = f"Build #{build.build_number} for {pipeline.name} has {build.status.value.lower()}"
        
        # Add remediation advice
        advice = self._get_remediation_advice(build, pipeline)
        if advice:
            message += f"\n\nRemediation Advice:\n{advice}"
        
        # Send Slack notification
        if notification_type in ["all", "slack"] and "slack" in pipeline.notification_channels:
            slack_success = await self.send_slack_notification(build, pipeline, message)
            success = success and slack_success
        
        # Send email notification
        if notification_type in ["all", "email"] and "email" in pipeline.notification_channels:
            # For demo purposes, use a default recipient list
            # In production, this would come from pipeline configuration
            recipients = ["team@example.com"]
            email_success = self.send_email_notification(build, pipeline, message, recipients)
            success = success and email_success
        
        return success

    def _create_email_content(self, job_name: str, build_number: int, build_url: str, 
                            failure_reason: str = "Unknown") -> str:
        """Create HTML email content for job failure notification."""
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; }}
                .button {{ background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                .details {{ background-color: white; padding: 10px; border-radius: 5px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Jenkins Job Failure Alert</h2>
            </div>
            <div class="content">
                <h3>Job Details:</h3>
                <div class="details">
                    <p><strong>Job Name:</strong> {job_name}</p>
                    <p><strong>Build Number:</strong> #{build_number}</p>
                    <p><strong>Failure Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Failure Reason:</strong> {failure_reason}</p>
                </div>
                <p style="margin-top: 20px;">
                    <a href="{build_url}" class="button">View Build Details</a>
                </p>
                <p style="margin-top: 20px; font-size: 12px; color: #666;">
                    This is an automated notification from your CI/CD Health Dashboard.
                </p>
            </div>
        </body>
        </html>
        """
        return html_content

    async def send_job_failure_notification(self, job_name: str, build_number: int, 
                                          build_url: str, failure_reason: str = "Unknown") -> bool:
        """Send email notification for job failure."""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.from_email, self.to_email]):
            logger.warning("Email notification not configured - missing SMTP settings")
            return False

        # Create unique notification key to avoid duplicates
        notification_key = f"{job_name}_{build_number}"
        if notification_key in self._sent_notifications:
            logger.info(f"Notification already sent for {notification_key}")
            return True

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 Jenkins Job Failed: {job_name} #{build_number}"
            msg['From'] = self.from_email
            msg['To'] = self.to_email

            # Create HTML content
            html_content = self._create_email_content(job_name, build_number, build_url, failure_reason)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            # Mark as sent
            self._sent_notifications.add(notification_key)
            logger.info(f"Job failure notification sent for {job_name} #{build_number}")
            return True

        except Exception as e:
            logger.error(f"Failed to send job failure notification: {e}")
            return False

    def clear_sent_notifications(self):
        """Clear the sent notifications cache."""
        self._sent_notifications.clear()
        logger.info("Sent notifications cache cleared")

# Global notification service instance
notification_service = NotificationService()

