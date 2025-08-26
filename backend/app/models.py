from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from .database import Base


class BuildStatus(str, Enum):
    """Build status enumeration."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    ABORTED = "ABORTED"
    UNSTABLE = "UNSTABLE"
    IN_PROGRESS = "IN_PROGRESS"
    QUEUED = "QUEUED"


class PipelineHealth(str, Enum):
    """Pipeline health status."""
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    WARNING = "WARNING"


class Build(Base):
    """Build model for storing CI/CD build data."""
    __tablename__ = "builds"
    
    id = Column(Integer, primary_key=True, index=True)
    build_number = Column(Integer, nullable=False)
    pipeline_name = Column(String(255), nullable=False, index=True)
    status = Column(SQLEnum(BuildStatus), nullable=False, index=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    triggered_by = Column(String(255), nullable=False, index=True)
    branch = Column(String(255), nullable=True)
    commit_hash = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)
    console_output = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    notifications = relationship("Notification", back_populates="build")


class Pipeline(Base):
    """Pipeline model for storing pipeline configuration and metrics."""
    __tablename__ = "pipelines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    jenkins_job_name = Column(String(255), nullable=True)
    health_status = Column(SQLEnum(PipelineHealth), default=PipelineHealth.HEALTHY, index=True)
    failure_rate_threshold = Column(Float, default=0.2)
    build_time_threshold = Column(Integer, default=1800)  # 30 minutes in seconds
    notification_channels = Column(Text, nullable=True)  # JSON string
    total_builds = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    average_duration = Column(Float, nullable=True)
    last_build_status = Column(SQLEnum(BuildStatus), nullable=True)
    last_build_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Notification(Base):
    """Notification model for storing alert history."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=True)
    build_id = Column(Integer, ForeignKey("builds.id"), nullable=False)
    type = Column(String(50), nullable=False)  # email, slack
    status = Column(String(50), default="pending")  # pending, sent, failed
    message = Column(Text, nullable=False)
    recipients = Column(Text, nullable=True)  # JSON string
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    build = relationship("Build", back_populates="notifications")
    pipeline = relationship("Pipeline")

