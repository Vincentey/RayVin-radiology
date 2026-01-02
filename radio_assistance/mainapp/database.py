"""
Database configuration and session management for PostgreSQL.
"""

import os
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://rayvin:rayvin_password@localhost:5432/rayvin_db"
)

# Fix for Railway: convert postgres:// to postgresql:// (SQLAlchemy 2.0 requirement)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate settings based on database type
if DATABASE_URL.startswith("sqlite"):
    # SQLite doesn't support pool_size, max_overflow
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # PostgreSQL with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Check connection before use
        pool_size=10,
        max_overflow=20,
        echo=False  # Set to True for SQL debugging
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ==================== MODELS ====================

class User(Base):
    """User account model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user")  # user, radiologist, admin
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    studies = relationship("Study", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username='{self.username}', role='{self.role}')>"


class Study(Base):
    """DICOM study model."""
    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    modality = Column(String(10), nullable=True)  # CR, DX, CT, MR
    file_count = Column(Integer, default=0)
    file_paths = Column(JSON, nullable=True)  # List of file paths
    patient_id = Column(String(100), nullable=True)
    patient_name = Column(String(200), nullable=True)
    study_date = Column(DateTime, nullable=True)
    study_description = Column(String(500), nullable=True)
    body_part = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")  # pending, analyzing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="studies")
    analyses = relationship("AnalysisResult", back_populates="study", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Study(study_id='{self.study_id}', modality='{self.modality}')>"


class AnalysisResult(Base):
    """AI analysis result model."""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # xray, ct, mri
    
    # Findings
    findings = Column(JSON, nullable=True)  # List of findings with probabilities
    positive_findings = Column(JSON, nullable=True)  # List of positive findings
    top_predictions = Column(JSON, nullable=True)  # Top N predictions
    
    # Recommendations
    recommendations = Column(Text, nullable=True)  # GPT-4 generated report
    urgency = Column(String(20), default="routine")  # routine, semi-urgent, urgent, emergent
    
    # Metadata
    model_used = Column(String(100), nullable=True)  # e.g., "densenet121-res224-all"
    processing_time_ms = Column(Integer, nullable=True)
    confidence_threshold = Column(Float, default=0.65)
    
    # Status
    status = Column(String(20), default="completed")  # completed, failed, partial
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    study = relationship("Study", back_populates="analyses")

    def __repr__(self):
        return f"<AnalysisResult(study_id={self.study_id}, urgency='{self.urgency}')>"


class AuditLog(Base):
    """Audit log for tracking user actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False)  # login, logout, upload, analyze, etc.
    resource_type = Column(String(50), nullable=True)  # study, user, etc.
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)  # Additional details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog(action='{self.action}', user='{self.username}')>"


# ==================== DATABASE UTILITIES ====================

def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Use with FastAPI's Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize the database - create all tables.
    Call this on application startup.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")


def drop_db():
    """
    Drop all tables. Use with caution!
    """
    Base.metadata.drop_all(bind=engine)
    print("⚠️ All database tables dropped")


# ==================== CRUD OPERATIONS ====================

class UserCRUD:
    """CRUD operations for User model."""
    
    @staticmethod
    def create(db: Session, username: str, email: str, hashed_password: str, 
               full_name: str = None, role: str = "user") -> User:
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name or username,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_verification_token(db: Session, token: str) -> User | None:
        return db.query(User).filter(User.verification_token == token).first()

    @staticmethod
    def get_by_reset_token(db: Session, token: str) -> User | None:
        return db.query(User).filter(User.reset_token == token).first()

    @staticmethod
    def update(db: Session, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user: User):
        db.delete(user)
        db.commit()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()


class StudyCRUD:
    """CRUD operations for Study model."""
    
    @staticmethod
    def create(db: Session, study_id: str, user_id: int, **kwargs) -> Study:
        study = Study(study_id=study_id, user_id=user_id, **kwargs)
        db.add(study)
        db.commit()
        db.refresh(study)
        return study

    @staticmethod
    def get_by_study_id(db: Session, study_id: str) -> Study | None:
        return db.query(Study).filter(Study.study_id == study_id).first()

    @staticmethod
    def get_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Study]:
        return db.query(Study).filter(Study.user_id == user_id).order_by(
            Study.created_at.desc()
        ).offset(skip).limit(limit).all()

    @staticmethod
    def count_by_user(db: Session, user_id: int) -> int:
        return db.query(Study).filter(Study.user_id == user_id).count()

    @staticmethod
    def get_today_count(db: Session, user_id: int) -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return db.query(Study).filter(
            Study.user_id == user_id,
            Study.created_at >= today_start
        ).count()

    @staticmethod
    def get_pending_count(db: Session, user_id: int) -> int:
        return db.query(Study).filter(
            Study.user_id == user_id,
            Study.status == "pending"
        ).count()

    @staticmethod
    def update(db: Session, study: Study, **kwargs) -> Study:
        for key, value in kwargs.items():
            if hasattr(study, key):
                setattr(study, key, value)
        study.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(study)
        return study

    @staticmethod
    def delete(db: Session, study: Study):
        db.delete(study)
        db.commit()


class AnalysisResultCRUD:
    """CRUD operations for AnalysisResult model."""
    
    @staticmethod
    def create(db: Session, study_id: int, analysis_type: str, **kwargs) -> AnalysisResult:
        result = AnalysisResult(study_id=study_id, analysis_type=analysis_type, **kwargs)
        db.add(result)
        db.commit()
        db.refresh(result)
        return result

    @staticmethod
    def get_by_study(db: Session, study_id: int) -> list[AnalysisResult]:
        return db.query(AnalysisResult).filter(AnalysisResult.study_id == study_id).all()

    @staticmethod
    def get_latest_by_study(db: Session, study_id: int) -> AnalysisResult | None:
        return db.query(AnalysisResult).filter(
            AnalysisResult.study_id == study_id
        ).order_by(AnalysisResult.created_at.desc()).first()

    @staticmethod
    def get_urgent_count(db: Session, user_id: int) -> int:
        return db.query(AnalysisResult).join(Study).filter(
            Study.user_id == user_id,
            AnalysisResult.urgency.in_(["urgent", "emergent"])
        ).count()


class AuditLogCRUD:
    """CRUD operations for AuditLog model."""
    
    @staticmethod
    def create(db: Session, action: str, user_id: int = None, username: str = None, 
               resource_type: str = None, resource_id: str = None, 
               details: dict = None, ip_address: str = None, user_agent: str = None) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[AuditLog]:
        return db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(
            AuditLog.created_at.desc()
        ).offset(skip).limit(limit).all()


# Initialize on import if running directly
if __name__ == "__main__":
    print(f"Database URL: {DATABASE_URL}")
    init_db()

