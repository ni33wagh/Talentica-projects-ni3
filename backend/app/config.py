from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "CI/CD Health Dashboard"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # Database - SQLAlchemy with SQLite for dev, PostgreSQL for prod
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_name: str = Field(default="cicd_dashboard", env="DATABASE_NAME")
    
    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000", 
        env="CORS_ORIGINS"
    )
    
    # Jenkins Integration
    jenkins_url: Optional[str] = Field(default=None, env="JENKINS_URL")
    jenkins_username: Optional[str] = Field(default=None, env="JENKINS_USERNAME")
    jenkins_api_token: Optional[str] = Field(default=None, env="JENKINS_API_TOKEN")
    
    # Notifications
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    
    # Email notification settings
    smtp_server: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="ni33wagh@gmail.com", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    from_email: str = Field(default="ni33wagh@gmail.com", env="FROM_EMAIL")
    to_email: str = Field(default="ni33wagh@gmail.com", env="TO_EMAIL")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    
    # Redis (for Celery and caching)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Health Check Thresholds
    failure_rate_threshold: float = Field(default=0.2, env="FAILURE_RATE_THRESHOLD")
    build_time_threshold_minutes: int = Field(default=30, env="BUILD_TIME_THRESHOLD_MINUTES")
    
    # Pagination
    default_page_size: int = Field(default=50, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(default=100, env="MAX_PAGE_SIZE")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(',')]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
