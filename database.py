"""
Database configuration and models
"""

import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# Patch for CockroachDB version detection
import sqlalchemy.dialects.postgresql.base as postgresql_base

original_get_server_version_info = postgresql_base.PGDialect._get_server_version_info

def patched_get_server_version_info(self, connection):
    """Patched version to handle CockroachDB version strings"""
    try:
        return original_get_server_version_info(self, connection)
    except AssertionError as e:
        if "CockroachDB" in str(e):
            # Return a fake PostgreSQL version for CockroachDB
            return (13, 0, 0)  # PostgreSQL 13 compatible
        raise

postgresql_base.PGDialect._get_server_version_info = patched_get_server_version_info

# Database setup
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(String, default="true")  # Using string for CockroachDB compatibility

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    product_name = Column(String, nullable=False)
    product_id = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=False)
    domain = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    product_id = Column(String, nullable=False)
    current_question = Column(Integer, default=1)
    questions_data = Column(Text)  # JSON string
    responses = Column(Text)  # JSON string
    scores = Column(Text)  # JSON string
    final_score = Column(Float, default=0.0)
    status = Column(String, default="active")  # active, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()