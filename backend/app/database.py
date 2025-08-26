from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
Base = declarative_base()

# Database engine and session
engine = None
SessionLocal = None


def get_database_url():
    """Get database URL based on environment."""
    if settings.database_url:
        return settings.database_url
    
    # Default to SQLite for development
    return f"sqlite:///./{settings.database_name}.db"


def create_database_engine():
    """Create database engine with appropriate configuration."""
    global engine, SessionLocal
    
    database_url = get_database_url()
    
    if database_url.startswith("sqlite"):
        # SQLite configuration for development
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.debug
        )
    else:
        # PostgreSQL/MySQL configuration for production
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.debug
        )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"Database engine created: {database_url}")


def get_db():
    """Get database session."""
    if not SessionLocal:
        create_database_engine()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    if not engine:
        create_database_engine()
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def close_db():
    """Close database connections."""
    if engine:
        engine.dispose()
        logger.info("Database connections closed")

