"""
Authentication Module - OAuth2 with JWT tokens

Provides:
- JWT token generation and validation
- Password hashing with pbkdf2
- OAuth2 password flow
- Role-based access control
- Email verification
- Password reset functionality
- PostgreSQL database integration
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Import database components
from .database import (
    get_db, User as DBUser, UserCRUD, AuditLogCRUD, init_db
)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing (pbkdf2 avoids bcrypt backend issues on Py3.14)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Database session dependency for auth functions
_db_session: Optional[Session] = None


# ==================== PYDANTIC MODELS ====================

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None


class User(BaseModel):
    """User response model (no sensitive data)."""
    id: Optional[int] = None
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "user"  # user, radiologist, admin
    disabled: bool = False
    email_verified: bool = False

    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with hashed password (internal use only)."""
    hashed_password: str


class UserCreate(BaseModel):
    """Model for user registration."""
    username: str
    password: str
    email: str  # Required for email verification
    full_name: Optional[str] = None
    role: str = "user"  # Default role for new signups
    
    @validator('username')
    def username_valid(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be 3-50 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores and hyphens allowed)')
        return v
    
    @validator('password')
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @validator('email')
    def email_valid(cls, v):
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class PasswordReset(BaseModel):
    """Model for password reset request."""
    email: str


class PasswordResetConfirm(BaseModel):
    """Model for password reset confirmation."""
    token: str
    new_password: str
    
    @validator('new_password')
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class EmailVerification(BaseModel):
    """Model for email verification."""
    token: str


# ==================== PASSWORD UTILITIES ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


# ==================== USER OPERATIONS (DATABASE) ====================

def get_user(username: str, db: Session = None) -> Optional[UserInDB]:
    """
    Get user by username from database.
    """
    if db is None:
        # Create a temporary session
        from .database import SessionLocal
        db = SessionLocal()
        try:
            return _get_user_from_db(username, db)
        finally:
            db.close()
    return _get_user_from_db(username, db)


def _get_user_from_db(username: str, db: Session) -> Optional[UserInDB]:
    """Internal function to get user from database."""
    db_user = UserCRUD.get_by_username(db, username)
    if db_user:
        return UserInDB(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            full_name=db_user.full_name,
            role=db_user.role,
            disabled=not db_user.is_active,
            email_verified=db_user.email_verified,
            hashed_password=db_user.hashed_password
        )
    return None


def get_user_by_id(user_id: int, db: Session) -> Optional[UserInDB]:
    """Get user by ID from database."""
    db_user = UserCRUD.get_by_id(db, user_id)
    if db_user:
        return UserInDB(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            full_name=db_user.full_name,
            role=db_user.role,
            disabled=not db_user.is_active,
            email_verified=db_user.email_verified,
            hashed_password=db_user.hashed_password
        )
    return None


def authenticate_user(username: str, password: str, db: Session = None) -> Optional[UserInDB]:
    """
    Authenticate a user with username and password.
    """
    user = get_user(username, db)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_user(user_data: UserCreate, db: Session = None, require_verification: bool = True) -> Optional[UserInDB]:
    """
    Create a new user in the database.
    
    Args:
        user_data: User registration data
        db: Database session
        require_verification: If True, user starts with email_verified=False
        
    Returns:
        UserInDB if successful, None if user already exists
    """
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        # Check if username exists
        if UserCRUD.get_by_username(db, user_data.username):
            return None
        
        # Check if email exists
        if user_data.email and UserCRUD.get_by_email(db, user_data.email):
            return None
        
        # Create user
        db_user = UserCRUD.create(
            db=db,
            username=user_data.username,
            email=user_data.email.lower() if user_data.email else None,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name or user_data.username,
            role=user_data.role if user_data.role in ["user", "radiologist"] else "user"
        )
        
        # Set email verification status
        if not require_verification:
            UserCRUD.update(db, db_user, email_verified=True)
        
        return UserInDB(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            full_name=db_user.full_name,
            role=db_user.role,
            disabled=not db_user.is_active,
            email_verified=db_user.email_verified,
            hashed_password=db_user.hashed_password
        )
    finally:
        if close_db:
            db.close()


def get_user_by_email(email: str, db: Session = None) -> Optional[UserInDB]:
    """Get user by email address."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_email(db, email.lower())
        if db_user:
            return UserInDB(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                full_name=db_user.full_name,
                role=db_user.role,
                disabled=not db_user.is_active,
                email_verified=db_user.email_verified,
                hashed_password=db_user.hashed_password
            )
        return None
    finally:
        if close_db:
            db.close()


def update_user_password(username: str, new_password: str, db: Session = None) -> bool:
    """
    Update a user's password.
    
    Args:
        username: Username to update
        new_password: New plain text password
        db: Database session
        
    Returns:
        True if successful, False if user not found
    """
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_username(db, username)
        if not db_user:
            return False
        
        UserCRUD.update(db, db_user, hashed_password=get_password_hash(new_password))
        return True
    finally:
        if close_db:
            db.close()


def verify_user_email(username: str, db: Session = None) -> bool:
    """
    Mark a user's email as verified.
    
    Args:
        username: Username to verify
        db: Database session
        
    Returns:
        True if successful, False if user not found
    """
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_username(db, username)
        if not db_user:
            return False
        
        UserCRUD.update(db, db_user, email_verified=True, verification_token=None)
        return True
    finally:
        if close_db:
            db.close()


def is_email_verified(username: str, db: Session = None) -> bool:
    """Check if user's email is verified."""
    user = get_user(username, db)
    return user.email_verified if user else False


def set_verification_token(username: str, token: str, db: Session = None) -> bool:
    """Set email verification token for a user."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_username(db, username)
        if not db_user:
            return False
        
        UserCRUD.update(db, db_user, verification_token=token)
        return True
    finally:
        if close_db:
            db.close()


def get_user_by_verification_token(token: str, db: Session = None) -> Optional[UserInDB]:
    """Get user by verification token."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_verification_token(db, token)
        if db_user:
            return UserInDB(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                full_name=db_user.full_name,
                role=db_user.role,
                disabled=not db_user.is_active,
                email_verified=db_user.email_verified,
                hashed_password=db_user.hashed_password
            )
        return None
    finally:
        if close_db:
            db.close()


def set_reset_token(username: str, token: str, expires_hours: int = 24, db: Session = None) -> bool:
    """Set password reset token for a user."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_username(db, username)
        if not db_user:
            return False
        
        UserCRUD.update(
            db, db_user, 
            reset_token=token,
            reset_token_expires=datetime.utcnow() + timedelta(hours=expires_hours)
        )
        return True
    finally:
        if close_db:
            db.close()


def get_user_by_reset_token(token: str, db: Session = None) -> Optional[UserInDB]:
    """Get user by reset token if not expired."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_reset_token(db, token)
        if db_user:
            # Check if token is expired
            if db_user.reset_token_expires and db_user.reset_token_expires < datetime.utcnow():
                return None
            
            return UserInDB(
                id=db_user.id,
                username=db_user.username,
                email=db_user.email,
                full_name=db_user.full_name,
                role=db_user.role,
                disabled=not db_user.is_active,
                email_verified=db_user.email_verified,
                hashed_password=db_user.hashed_password
            )
        return None
    finally:
        if close_db:
            db.close()


def clear_reset_token(username: str, db: Session = None) -> bool:
    """Clear password reset token after use."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_username(db, username)
        if not db_user:
            return False
        
        UserCRUD.update(db, db_user, reset_token=None, reset_token_expires=None)
        return True
    finally:
        if close_db:
            db.close()


def update_last_login(username: str, db: Session = None) -> bool:
    """Update user's last login timestamp."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        db_user = UserCRUD.get_by_username(db, username)
        if not db_user:
            return False
        
        UserCRUD.update(db, db_user, last_login=datetime.utcnow())
        return True
    finally:
        if close_db:
            db.close()


# ==================== JWT TOKEN OPERATIONS ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_email_verification_token(username: str) -> str:
    """Create a token for email verification."""
    return create_access_token(
        data={"sub": username, "type": "email_verification"},
        expires_delta=timedelta(hours=48)
    )


def create_password_reset_token(username: str) -> str:
    """Create a token for password reset."""
    return create_access_token(
        data={"sub": username, "type": "password_reset"},
        expires_delta=timedelta(hours=24)
    )


def verify_token(token: str, token_type: str) -> Optional[str]:
    """Verify a token and return the username if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if payload.get("type") != token_type:
            return None
        return username
    except JWTError:
        return None


# ==================== FASTAPI DEPENDENCIES ====================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(
            username=username, 
            role=payload.get("role"),
            user_id=payload.get("user_id")
        )
    except JWTError:
        raise credentials_exception
    
    user = get_user(token_data.username, db)
    if user is None:
        raise credentials_exception
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        disabled=user.disabled,
        email_verified=user.email_verified
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active (not disabled) user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_role(allowed_roles: list):
    """Dependency to require specific roles."""
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not authorized. Required: {allowed_roles}"
            )
        return current_user
    return role_checker


# Role shortcuts
require_admin = require_role(["admin"])
require_radiologist = require_role(["admin", "radiologist"])
require_user = require_role(["admin", "radiologist", "user"])


# ==================== AUDIT LOGGING ====================

def log_action(
    action: str,
    user: User = None,
    resource_type: str = None,
    resource_id: str = None,
    details: dict = None,
    request: Request = None,
    db: Session = None
):
    """Log an action to the audit log."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        AuditLogCRUD.create(
            db=db,
            action=action,
            user_id=user.id if user else None,
            username=user.username if user else None,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    finally:
        if close_db:
            db.close()


# ==================== DATABASE INITIALIZATION ====================

def create_default_users(db: Session = None):
    """Create default admin user if no users exist."""
    if db is None:
        from .database import SessionLocal
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        # Check if any users exist
        existing = UserCRUD.get_by_username(db, "admin")
        if existing:
            return  # Users already exist
        
        # Get admin password from environment (REQUIRED in production)
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not admin_password:
            # In development, use default but warn
            admin_password = "admin123"
            print("⚠️  WARNING: Using default admin password. Set ADMIN_PASSWORD in production!")
        
        admin_email = os.getenv("ADMIN_EMAIL", "admin@hospital.org")
        
        UserCRUD.create(
            db=db,
            username="admin",
            email=admin_email,
            hashed_password=get_password_hash(admin_password),
            full_name="System Administrator",
            role="admin"
        )
        admin = UserCRUD.get_by_username(db, "admin")
        if admin:
            UserCRUD.update(db, admin, email_verified=True)
        
        print("✅ Default admin user created (username: admin)")
    finally:
        if close_db:
            db.close()


def initialize_auth_database():
    """Initialize the database and create default users."""
    init_db()
    create_default_users()
