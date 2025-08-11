# my_fastapi_angular_backend/app/database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings # Import your settings for DATABASE_URL

# SQLAlchemy database connection URL from your settings
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create the SQLAlchemy engine. 'pool_pre_ping=True' helps with lost connections.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True # Helps prevent stale connections
)

# Configure a SessionLocal class for database interactions.
# 'autocommit=False' means you have to explicitly call db.commit().
# 'autoflush=False' means objects are not flushed until commit or query.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for your SQLAlchemy ORM models.
Base = declarative_base()

# Dependency function to get a database session.
# This pattern is used by FastAPI's Depends() for dependency injection.
def get_db():
    db = SessionLocal()
    try:
        yield db # Provides the database session to the endpoint/dependency
    finally:
        db.close() # Ensures the session is closed after the request is processed