"""
FastAPI Endpoints for DICOM Processing and Radiology AI Analysis

Provides REST API endpoints for:
- Authentication (OAuth2/JWT)
- Uploading DICOM files
- Running AI analysis (X-ray, CT, MRI)
- Retrieving radiology reports with recommendations
- PostgreSQL database persistence
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy.orm import Session
import shutil
import uuid
import re
import logging
from typing import List, Optional
from pydantic import BaseModel, field_validator
from datetime import timedelta, datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_FILE_SIZE_MB = 500  # Maximum file size in MB
MAX_FILES_PER_REQUEST = 1000  # Maximum number of files per upload
ALLOWED_EXTENSIONS = {'.dcm', '.dicom', ''}  # Empty string for files without extension

# Rate limiting (simple in-memory - for production use Redis)
from collections import defaultdict
import time

class RateLimiter:
    """Simple rate limiter for login attempts."""
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.attempts = defaultdict(list)
        self.max_attempts = max_attempts
        self.window = window_seconds
    
    def is_allowed(self, key: str) -> bool:
        now = time.time()
        # Clean old attempts
        self.attempts[key] = [t for t in self.attempts[key] if now - t < self.window]
        return len(self.attempts[key]) < self.max_attempts
    
    def record_attempt(self, key: str):
        self.attempts[key].append(time.time())
    
    def get_remaining_time(self, key: str) -> int:
        if not self.attempts[key]:
            return 0
        oldest = min(self.attempts[key])
        return max(0, int(self.window - (time.time() - oldest)))

login_limiter = RateLimiter(max_attempts=5, window_seconds=300)  # 5 attempts per 5 minutes

# Import workflow and auth
from .the_nodes import wapp, extract_output
from .auth import (
    Token, User, UserCreate, PasswordReset, PasswordResetConfirm, EmailVerification,
    authenticate_user, create_access_token, create_user,
    get_current_active_user, require_user, require_radiologist, require_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES, get_user_by_email, update_user_password,
    verify_user_email, is_email_verified, initialize_auth_database, update_last_login,
    log_action
)
from .email_service import (
    send_password_reset_email, send_verification_email, send_welcome_email,
    verify_password_reset_token, verify_email_verification_token,
    get_email_service
)
from .database import (
    get_db, init_db, StudyCRUD, AnalysisResultCRUD,
    Study as DBStudy, AnalysisResult as DBAnalysisResult
)

app = FastAPI(
    title="RayVin - Radiology AI Assistant API",
    description="AI-powered DICOM analysis with clinical recommendations",
    version="1.0.0"
)


# Startup event - initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database and create default users on startup."""
    try:
        logger.info("Initializing database...")
        initialize_auth_database()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.warning("Application will continue but database features may not work")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )

# CORS middleware - Configure for production
import os
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Infrastructure
upload_root = Path("uploads")
upload_root.mkdir(parents=True, exist_ok=True)

# Static files for frontend
frontend_path = Path(__file__).resolve().parents[2] / "frontend"
if frontend_path.exists():
    app.mount("/css", StaticFiles(directory=frontend_path / "css"), name="css")
    app.mount("/js", StaticFiles(directory=frontend_path / "js"), name="js")
    app.mount("/assets", StaticFiles(directory=frontend_path / "assets"), name="assets")


# Response Models
class AnalysisResponse(BaseModel):
    study_id: str
    modality: Optional[str]
    findings: Optional[List[dict]]
    recommendations: Optional[str]
    urgency: Optional[str]
    status: str


class HealthResponse(BaseModel):
    status: str
    version: str


# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/token", response_model=Token, tags=["Authentication"])
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 token endpoint.
    
    Authenticates user and returns JWT access token.
    Users must have verified their email before logging in.
    
    Rate limited to 5 attempts per 5 minutes per IP address.
    """
    # Rate limiting by IP
    client_ip = request.client.host if request.client else "unknown"
    
    if not login_limiter.is_allowed(client_ip):
        remaining = login_limiter.get_remaining_time(client_ip)
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Please try again in {remaining} seconds.",
            headers={"Retry-After": str(remaining)}
        )
    
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        login_limiter.record_attempt(client_ip)
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if email is verified
    if not is_email_verified(user.username, db):
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please check your email and click the verification link.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time
    update_last_login(user.username, db)
    
    # Log the action
    log_action("login", user, request=request, db=db)
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "user_id": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.post("/api/auth/signup", tags=["Authentication"])
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - username: unique username (required, 3-50 chars, alphanumeric)
    - password: password (required, min 8 chars)
    - email: email address (required for verification)
    - full_name: display name (optional)
    - role: 'user' or 'radiologist' (defaults to 'user')
    
    A verification email will be sent to the provided email address.
    Note: Admin accounts can only be created by existing admins.
    """
    # Input validation
    username = user_data.username.strip()
    
    # Username validation
    if len(username) < 3 or len(username) > 50:
        raise HTTPException(status_code=400, detail="Username must be 3-50 characters")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, underscores, and hyphens")
    
    # Password validation
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Email validation (required)
    if not user_data.email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', user_data.email):
        raise HTTPException(status_code=400, detail="Valid email address is required")
    
    # Validate role - only user/radiologist allowed via signup
    if user_data.role not in ["user", "radiologist"]:
        user_data.role = "user"
    
    try:
        # Create user with email verification required
        new_user = create_user(user_data, db=db, require_verification=True)
        
        if not new_user:
            raise HTTPException(
                status_code=400,
                detail="Username or email already exists"
            )
        
        # Send verification email
        email_result = send_verification_email(new_user.email, new_user.username)
        
        logger.info(f"New user registered: {new_user.username} (role: {new_user.role})")
        
        return {
            "message": "Account created successfully. Please check your email to verify your account.",
            "user": {
                "username": new_user.username,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "role": new_user.role,
                "email_verified": False
            },
            "email_sent": email_result.get("success", False),
            "note": "You must verify your email before logging in." if email_result.get("success") else "Email service not configured. Please contact admin to verify your account."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")


@app.get("/api/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user info."""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "email_verified": is_email_verified(current_user.username)
    }


# ==================== PASSWORD RESET ENDPOINTS ====================

@app.post("/api/auth/forgot-password", tags=["Authentication"])
async def forgot_password(request: PasswordReset):
    """
    Request a password reset link.
    
    Sends an email with a password reset link to the user's email address.
    The link expires in 30 minutes.
    
    For security, this endpoint always returns success even if the email doesn't exist.
    """
    user = get_user_by_email(request.email)
    
    if user:
        # Send password reset email
        result = send_password_reset_email(user.email, user.username)
        logger.info(f"Password reset requested for: {user.username}")
    else:
        # Don't reveal if email exists
        logger.info(f"Password reset requested for non-existent email: {request.email}")
    
    # Always return success for security (don't reveal if email exists)
    return {
        "message": "If an account with that email exists, a password reset link has been sent.",
        "note": "The link expires in 30 minutes."
    }


@app.post("/api/auth/reset-password", tags=["Authentication"])
async def reset_password(request: PasswordResetConfirm):
    """
    Reset password using the token from the email link.
    
    - token: The reset token from the email link
    - new_password: The new password (min 8 characters)
    """
    # Validate password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Verify token
    email = verify_password_reset_token(request.token)
    
    if not email:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token. Please request a new password reset."
        )
    
    # Find user by email
    user = get_user_by_email(email)
    
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Update password
    success = update_user_password(user.username, request.new_password)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    logger.info(f"Password reset successful for: {user.username}")
    
    return {
        "message": "Password has been reset successfully. You can now log in with your new password."
    }


# ==================== EMAIL VERIFICATION ENDPOINTS ====================

@app.post("/api/auth/verify-email", tags=["Authentication"])
async def verify_email(request: EmailVerification):
    """
    Verify email address using the token from the verification email.
    
    - token: The verification token from the email link
    """
    # Verify token
    token_data = verify_email_verification_token(request.token)
    
    if not token_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token. Please request a new verification email."
        )
    
    username = token_data.get("username")
    email = token_data.get("email")
    
    # Verify the email
    success = verify_user_email(username)
    
    if not success:
        raise HTTPException(status_code=400, detail="User not found")
    
    # Send welcome email
    send_welcome_email(email, username)
    
    logger.info(f"Email verified for: {username}")
    
    # Create access token for automatic login
    access_token = create_access_token(
        data={"sub": username, "role": "user"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "message": "Email verified successfully! You are now logged in.",
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/api/auth/resend-verification", tags=["Authentication"])
async def resend_verification_email(request: PasswordReset):
    """
    Resend the email verification link.
    
    - email: The email address to send verification to
    """
    user = get_user_by_email(request.email)
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If an account with that email exists, a verification email has been sent."}
    
    if is_email_verified(user.username):
        return {"message": "This email is already verified. You can log in."}
    
    # Send verification email
    result = send_verification_email(user.email, user.username)
    
    logger.info(f"Verification email resent for: {user.username}")
    
    return {
        "message": "Verification email has been sent. Please check your inbox.",
        "email_sent": result.get("success", False)
    }


@app.get("/api/auth/email-status", tags=["Authentication"])
async def check_email_service():
    """
    Check if email service is configured and working.
    
    Returns the configuration status without revealing sensitive details.
    """
    service = get_email_service()
    return {
        "configured": service.is_configured(),
        "note": "Email service is configured and ready." if service.is_configured() else "Email service not configured. Set SMTP_USER and SMTP_PASSWORD in .env"
    }


# ==================== PUBLIC ENDPOINTS ====================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint (no auth required).
    
    Verifies that the API is running and database is connected.
    """
    from sqlalchemy import text
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "version": "1.0.0"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "version": "1.0.0", "error": "Database connection failed"}
        )


# ==================== PROTECTED ENDPOINTS ====================

def validate_dicom_file(filename: str) -> bool:
    """Validate that file appears to be a DICOM file."""
    if not filename:
        return False
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


@app.post("/api/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_dicom(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze DICOM files.
    
    Requires: user, radiologist, or admin role
    
    Supports:
    - X-Ray (CR, DX): 2D chest radiograph analysis
    - CT: 3D computed tomography analysis
    - MRI (MR): 3D magnetic resonance imaging analysis
    
    Limits:
    - Max file size: 500MB per file
    - Max files: 1000 per request
    """
    # Validation
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files received")
    
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=400, 
            detail=f"Too many files. Maximum {MAX_FILES_PER_REQUEST} files per request"
        )
    
    study_id = str(uuid.uuid4())
    study_dir = upload_root / study_id
    study_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths: List[str] = []
    total_size = 0
    
    try:
        for file in files:
            if not file.filename:
                continue
            
            # Validate file extension
            if not validate_dicom_file(file.filename):
                logger.warning(f"Skipping non-DICOM file: {file.filename}")
                continue
            
            # Sanitize filename to prevent path traversal
            safe_filename = Path(file.filename).name
            if not safe_filename or safe_filename.startswith('.'):
                continue
            
            file_path = study_dir / safe_filename
            
            # Read and check file size
            content = await file.read()
            file_size = len(content)
            
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {safe_filename} exceeds maximum size of {MAX_FILE_SIZE_MB}MB"
                )
            
            total_size += file_size
            
            # Write file
            with file_path.open("wb") as out:
                out.write(content)
            
            saved_paths.append(str(file_path))
            
    except HTTPException:
        shutil.rmtree(study_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(study_dir, ignore_errors=True)
        logger.error(f"File save error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save files")
    
    if not saved_paths:
        shutil.rmtree(study_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="No valid DICOM files found")
    
    logger.info(f"Study {study_id}: {len(saved_paths)} files, {total_size/1024/1024:.1f}MB by {current_user.username}")
    
    # Create study record in database
    db_study = StudyCRUD.create(
        db=db,
        study_id=study_id,
        user_id=current_user.id,
        file_count=len(saved_paths),
        file_paths=saved_paths,
        status="analyzing"
    )
    
    try:
        result = wapp.invoke({"dicom_path": saved_paths})
        output = extract_output(result)
        
        modality = result.get("modality")
        findings = output.get("findings")
        recommendations = output.get("recommendations")
        urgency = output.get("urgency", "routine")
        
        # Update study record
        StudyCRUD.update(db, db_study, modality=modality, status="completed")
        
        # Create analysis result record
        AnalysisResultCRUD.create(
            db=db,
            study_id=db_study.id,
            analysis_type=modality.lower() if modality else "unknown",
            findings=findings,
            positive_findings=[f.get("positive_findings", []) for f in (findings or [])],
            recommendations=recommendations,
            urgency=urgency,
            model_used="densenet121-res224-all",
            status="completed"
        )
        
        return AnalysisResponse(
            study_id=study_id,
            modality=modality,
            findings=findings,
            recommendations=recommendations,
            urgency=urgency,
            status="completed"
        )
    except Exception as e:
        logger.error(f"Analysis error for study {study_id}: {e}")
        # Update study status to failed
        StudyCRUD.update(db, db_study, status="failed")
        return AnalysisResponse(
            study_id=study_id,
            modality=None,
            findings=None,
            recommendations=None,
            urgency=None,
            status=f"error: Analysis failed - please try again"
        )


@app.post("/api/upload", tags=["Upload"])
async def upload_dicom(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_user)
):
    """
    Upload DICOM files without immediate analysis.
    
    Requires: user, radiologist, or admin role
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files received")
    
    study_id = str(uuid.uuid4())
    study_dir = upload_root / study_id
    study_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for file in files:
        if file.filename:
            file_path = study_dir / file.filename
            with file_path.open("wb") as out:
                shutil.copyfileobj(file.file, out)
            saved_files.append(file.filename)
            file.file.close()
    
    return {
        "study_id": study_id,
        "files_uploaded": len(saved_files),
        "filenames": saved_files,
        "uploaded_by": current_user.username
    }


@app.post("/api/analyze/{study_id}", tags=["Analysis"])
async def analyze_existing_study(
    study_id: str,
    current_user: User = Depends(require_radiologist)
):
    """
    Analyze previously uploaded DICOM study.
    
    Requires: radiologist or admin role
    """
    study_dir = upload_root / study_id
    
    if not study_dir.exists():
        raise HTTPException(status_code=404, detail="Study not found")
    
    dicom_paths = [str(p) for p in study_dir.glob("*.dcm")]
    if not dicom_paths:
        dicom_paths = [str(p) for p in study_dir.iterdir() if p.is_file()]
    
    if not dicom_paths:
        raise HTTPException(status_code=400, detail="No DICOM files in study")
    
    try:
        result = wapp.invoke({"dicom_path": dicom_paths})
        output = extract_output(result)
        
        return {
            "study_id": study_id,
            "modality": result.get("modality"),
            "findings": output.get("findings"),
            "recommendations": output.get("recommendations"),
            "urgency": output.get("urgency"),
            "status": "completed",
            "analyzed_by": current_user.username
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/studies", tags=["Studies"])
async def list_studies(
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db)
):
    """
    List all studies for the current user.
    
    Requires: user, radiologist, or admin role
    
    Admins and radiologists can see all studies.
    Regular users see only their own studies.
    """
    # Get studies from database
    if current_user.role in ["admin", "radiologist"]:
        # Admins and radiologists see all studies
        db_studies = db.query(DBStudy).order_by(DBStudy.created_at.desc()).limit(100).all()
    else:
        # Regular users see only their own studies
        db_studies = StudyCRUD.get_by_user(db, current_user.id, limit=100)
    
    studies = []
    for study in db_studies:
        # Get latest analysis result for urgency
        latest_analysis = AnalysisResultCRUD.get_latest_by_study(db, study.id)
        
        studies.append({
            "study_id": study.study_id,
            "file_count": study.file_count,
            "modality": study.modality,
            "status": study.status,
            "urgency": latest_analysis.urgency if latest_analysis else None,
            "created_at": study.created_at.isoformat() if study.created_at else None,
            "timestamp": study.created_at.isoformat() if study.created_at else None
        })
    
    # Calculate stats
    total = len(studies)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    analyzed_today = sum(1 for s in db_studies if s.created_at and s.created_at >= today_start)
    pending = sum(1 for s in studies if s.get("status") == "pending")
    urgent = sum(1 for s in studies if s.get("urgency") in ["urgent", "emergent"])
    
    return {
        "studies": studies, 
        "total": total,
        "analyzed_today": analyzed_today,
        "pending": pending,
        "urgent": urgent
    }


@app.delete("/api/study/{study_id}", tags=["Admin"])
async def delete_study(
    study_id: str,
    current_user: User = Depends(require_admin)
):
    """
    Delete uploaded study and associated files.
    
    Requires: admin role
    """
    study_dir = upload_root / study_id
    
    if not study_dir.exists():
        raise HTTPException(status_code=404, detail="Study not found")
    
    shutil.rmtree(study_dir)
    return {"status": "deleted", "study_id": study_id, "deleted_by": current_user.username}


# ==================== FRONTEND ROUTES ====================

@app.get("/", tags=["Frontend"])
async def serve_index():
    """Serve the login/signup page."""
    return FileResponse(frontend_path / "index.html")


@app.get("/dashboard.html", tags=["Frontend"])
async def serve_dashboard():
    """Serve the dashboard page."""
    return FileResponse(frontend_path / "dashboard.html")


@app.get("/analysis.html", tags=["Frontend"])
async def serve_analysis():
    """Serve the analysis page."""
    return FileResponse(frontend_path / "analysis.html")


@app.get("/reset-password.html", tags=["Frontend"])
async def serve_reset_password():
    """Serve the password reset page."""
    return FileResponse(frontend_path / "reset-password.html")


@app.get("/verify-email.html", tags=["Frontend"])
async def serve_verify_email():
    """Serve the email verification page."""
    return FileResponse(frontend_path / "verify-email.html")
