"""
SKAILA - SQLAlchemy Database Configuration
ORM-based database setup following best practices
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator

from core.config.logging_config import setup_logger
from core.exceptions import DatabaseConnectionError

logger = setup_logger(__name__)

# Create declarative base for ORM models
Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/skaila')

# Create SQLAlchemy engine with connection pooling
try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
        echo=False  # Set to True for SQL query logging
    )
    logger.info(f"Database engine created successfully")
except Exception as e:
    logger.critical(f"Failed to create database engine: {str(e)}")
    raise DatabaseConnectionError(
        "Unable to initialize database connection",
        context={'database_url': DATABASE_URL, 'error': str(e)}
    )

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    
    Usage:
        with get_db_session() as session:
            user = session.query(User).filter_by(id=1).first()
    
    Yields:
        SQLAlchemy session
    
    Raises:
        DatabaseConnectionError: If session creation fails
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()


def init_db():
    """
    Initialize database - create all tables
    Should be called during application startup
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise DatabaseConnectionError(
            "Database initialization failed",
            context={'error': str(e)}
        )


__all__ = ['Base', 'engine', 'SessionLocal', 'get_db_session', 'init_db']
