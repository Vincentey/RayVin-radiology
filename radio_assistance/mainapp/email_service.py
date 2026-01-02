"""
Email Service Module

Handles sending emails for:
- Password reset links
- Email verification after registration
- Notifications

Supports:
- Gmail API with OAuth 2.0 (recommended for production)
- SMTP fallback (for other providers)
"""

import os
import base64
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict
from pathlib import Path
from dotenv import load_dotenv
from jose import jwt

# Load environment variables
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

# Email Configuration
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "gmail_api")  # gmail_api or smtp
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Radiology AI Assistant")

# Gmail API paths
GMAIL_CREDENTIALS_PATH = Path(__file__).resolve().parents[2] / "credentials.json"
GMAIL_TOKEN_PATH = Path(__file__).resolve().parents[2] / "token.json"

# Token settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
PASSWORD_RESET_EXPIRE_MINUTES = 30
EMAIL_VERIFICATION_EXPIRE_HOURS = 24

# Base URL for links
BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")


class GmailAPIService:
    """Gmail API with OAuth 2.0 - No passwords needed."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self):
        self.creds = None
        self.service = None
        self._is_configured = GMAIL_CREDENTIALS_PATH.exists()
    
    def _get_credentials(self):
        """Get or refresh OAuth credentials."""
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        
        if GMAIL_TOKEN_PATH.exists():
            self.creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH), self.SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not GMAIL_CREDENTIALS_PATH.exists():
                    raise FileNotFoundError(
                        f"credentials.json not found at {GMAIL_CREDENTIALS_PATH}. "
                        "Download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(GMAIL_CREDENTIALS_PATH), self.SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save token for future use
            with open(GMAIL_TOKEN_PATH, 'w') as token:
                token.write(self.creds.to_json())
        
        return self.creds
    
    def _get_service(self):
        """Get Gmail API service."""
        if self.service is None:
            from googleapiclient.discovery import build
            creds = self._get_credentials()
            self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> Dict:
        """Send email via Gmail API."""
        try:
            service = self._get_service()
            
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{SMTP_FROM_NAME} <me>"
            msg["To"] = to_email
            
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            
            service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            print(f"[GMAIL API] Email sent to {to_email}")
            return {"success": True, "message": "Email sent via Gmail API"}
            
        except Exception as e:
            print(f"[GMAIL API] Error: {e}")
            return {"success": False, "message": str(e)}


class SMTPService:
    """SMTP fallback for non-Gmail providers."""
    
    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME
        self._is_configured = bool(SMTP_USER and SMTP_PASSWORD)
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> Dict:
        """Send email via SMTP."""
        import smtplib
        import ssl
        
        if not self._is_configured:
            return {"success": False, "message": "SMTP not configured"}
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Use SSL for port 465, TLS for port 587
            if self.smtp_port == 465:
                # SSL connection
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_email, to_email, msg.as_string())
            else:
                # TLS connection (port 587)
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_email, to_email, msg.as_string())
            
            print(f"[SMTP] Email sent to {to_email}")
            return {"success": True, "message": "Email sent via SMTP"}
            
        except Exception as e:
            print(f"[SMTP] Error: {e}")
            return {"success": False, "message": str(e)}


class EmailService:
    """Unified email service - uses Gmail API or SMTP based on config."""
    
    def __init__(self):
        self.provider = EMAIL_PROVIDER
        self._gmail = None
        self._smtp = None
        
        if self.provider == "gmail_api" and GMAIL_CREDENTIALS_PATH.exists():
            self._gmail = GmailAPIService()
            self._is_configured = True
            print("[EMAIL] Using Gmail API with OAuth 2.0")
        elif SMTP_USER and SMTP_PASSWORD:
            self._smtp = SMTPService()
            self._is_configured = True
            print("[EMAIL] Using SMTP")
        else:
            self._is_configured = False
            print("[EMAIL] Not configured - set up Gmail API or SMTP")
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return self._is_configured
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> Dict:
        """Send email using configured provider."""
        if not self._is_configured:
            print(f"[EMAIL] Not configured. Would send to {to_email}: {subject}")
            return {"success": False, "message": "Email not configured. Run: python -m radio_assistance.mainapp.email_service"}
        
        if self._gmail:
            return self._gmail.send_email(to_email, subject, html_content, text_content)
        elif self._smtp:
            return self._smtp.send_email(to_email, subject, html_content, text_content)
        
        return {"success": False, "message": "No email provider available"}


def create_password_reset_token(email: str) -> str:
    """
    Create a JWT token for password reset.
    
    Args:
        email: User's email address
        
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    to_encode = {
        "sub": email,
        "type": "password_reset",
        "exp": expire,
        "jti": secrets.token_hex(16)  # Unique token ID
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify a password reset token.
    
    Args:
        token: JWT token string
        
    Returns:
        Email address if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        print("[TOKEN] Password reset token expired")
        return None
    except jwt.JWTError as e:
        print(f"[TOKEN] Invalid token: {e}")
        return None


def create_email_verification_token(email: str, username: str) -> str:
    """
    Create a JWT token for email verification.
    
    Args:
        email: User's email address
        username: User's username
        
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
    to_encode = {
        "sub": email,
        "username": username,
        "type": "email_verification",
        "exp": expire,
        "jti": secrets.token_hex(16)
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_email_verification_token(token: str) -> Optional[Dict]:
    """
    Verify an email verification token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dict with email and username if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "email_verification":
            return None
        return {
            "email": payload.get("sub"),
            "username": payload.get("username")
        }
    except jwt.ExpiredSignatureError:
        print("[TOKEN] Email verification token expired")
        return None
    except jwt.JWTError as e:
        print(f"[TOKEN] Invalid token: {e}")
        return None


def send_password_reset_email(email: str, username: str) -> Dict:
    """
    Send password reset email with reset link.
    
    Args:
        email: User's email address
        username: User's username for personalization
        
    Returns:
        Dict with success status and message
    """
    token = create_password_reset_token(email)
    reset_link = f"{BASE_URL}/reset-password.html?token={token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f7fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: #3182ce; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; }}
            .button:hover {{ background: #2c5282; }}
            .footer {{ text-align: center; color: #718096; font-size: 12px; margin-top: 20px; }}
            .warning {{ background: #fed7d7; border-left: 4px solid #c53030; padding: 12px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Radiology AI Assistant</h1>
                <p>Password Reset Request</p>
            </div>
            <div class="content">
                <p>Hello <strong>{username}</strong>,</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_link}" class="button">Reset My Password</a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: #edf2f7; padding: 10px; border-radius: 4px; font-size: 12px;">
                    {reset_link}
                </p>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong><br>
                    This link expires in {PASSWORD_RESET_EXPIRE_MINUTES} minutes. If you didn't request this reset, please ignore this email or contact support.
                </div>
                
                <p>Best regards,<br>The Radiology AI Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>© 2026 Radiology AI Assistant. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    Hello {username},
    
    We received a request to reset your password. Click the link below to create a new password:
    
    {reset_link}
    
    This link expires in {PASSWORD_RESET_EXPIRE_MINUTES} minutes.
    
    If you didn't request this reset, please ignore this email.
    
    Best regards,
    The Radiology AI Team
    """
    
    service = EmailService()
    return service._send_email(
        to_email=email,
        subject="Password Reset - Radiology AI Assistant",
        html_content=html_content,
        text_content=text_content
    )


def send_verification_email(email: str, username: str) -> Dict:
    """
    Send email verification after registration.
    
    Args:
        email: User's email address
        username: User's username
        
    Returns:
        Dict with success status and message
    """
    token = create_email_verification_token(email, username)
    verify_link = f"{BASE_URL}/verify-email.html?token={token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f7fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: #38a169; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; }}
            .button:hover {{ background: #2f855a; }}
            .footer {{ text-align: center; color: #718096; font-size: 12px; margin-top: 20px; }}
            .features {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .feature {{ display: flex; align-items: center; margin: 10px 0; }}
            .feature-icon {{ font-size: 24px; margin-right: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Radiology AI Assistant</h1>
                <p>Welcome to the Team!</p>
            </div>
            <div class="content">
                <p>Hello <strong>{username}</strong>,</p>
                <p>Thank you for registering with Radiology AI Assistant! Please verify your email address to activate your account:</p>
                
                <div style="text-align: center;">
                    <a href="{verify_link}" class="button">✓ Verify My Email</a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: #edf2f7; padding: 10px; border-radius: 4px; font-size: 12px;">
                    {verify_link}
                </p>
                
                <div class="features">
                    <h3>What You Can Do:</h3>
                    <div class="feature">
                        <span class="feature-icon">📊</span>
                        <span>Analyze X-ray, CT, and MRI scans with AI</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">📋</span>
                        <span>Get clinical recommendations based on findings</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🔒</span>
                        <span>Secure, HIPAA-compliant processing</span>
                    </div>
                </div>
                
                <p>This verification link expires in {EMAIL_VERIFICATION_EXPIRE_HOURS} hours.</p>
                
                <p>Best regards,<br>The Radiology AI Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>© 2026 Radiology AI Assistant. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to Radiology AI Assistant!
    
    Hello {username},
    
    Thank you for registering! Please verify your email address by clicking the link below:
    
    {verify_link}
    
    This link expires in {EMAIL_VERIFICATION_EXPIRE_HOURS} hours.
    
    What You Can Do:
    - Analyze X-ray, CT, and MRI scans with AI
    - Get clinical recommendations based on findings
    - Secure, HIPAA-compliant processing
    
    Best regards,
    The Radiology AI Team
    """
    
    service = EmailService()
    return service._send_email(
        to_email=email,
        subject="Verify Your Email - Radiology AI Assistant",
        html_content=html_content,
        text_content=text_content
    )


def send_welcome_email(email: str, username: str) -> Dict:
    """
    Send welcome email after email verification.
    
    Args:
        email: User's email address
        username: User's username
        
    Returns:
        Dict with success status and message
    """
    login_link = f"{BASE_URL}/index.html"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #38a169 0%, #2f855a 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f7fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
            .button {{ display: inline-block; background: #3182ce; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: bold; }}
            .footer {{ text-align: center; color: #718096; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>✅ Email Verified!</h1>
                <p>Your account is now active</p>
            </div>
            <div class="content">
                <p>Hello <strong>{username}</strong>,</p>
                <p>Your email has been successfully verified! You can now log in and start using Radiology AI Assistant.</p>
                
                <div style="text-align: center;">
                    <a href="{login_link}" class="button">Go to Login</a>
                </div>
                
                <p>If you have any questions, please contact our support team.</p>
                
                <p>Best regards,<br>The Radiology AI Team</p>
            </div>
            <div class="footer">
                <p>© 2026 Radiology AI Assistant. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    service = EmailService()
    return service._send_email(
        to_email=email,
        subject="Welcome to Radiology AI Assistant!",
        html_content=html_content
    )


# Singleton instance
_email_service: Optional[EmailService] = None

def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def setup_gmail_oauth():
    """
    Interactive setup for Gmail API OAuth 2.0.
    
    Run this once: python -m radio_assistance.mainapp.email_service
    """
    print("=" * 60)
    print("Gmail API OAuth 2.0 Setup")
    print("=" * 60)
    print()
    
    if not GMAIL_CREDENTIALS_PATH.exists():
        print("❌ credentials.json not found!")
        print()
        print("Steps to get credentials.json:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create a new project (or select existing)")
        print("3. Enable Gmail API:")
        print("   - Go to 'APIs & Services' > 'Library'")
        print("   - Search 'Gmail API' and enable it")
        print("4. Create OAuth credentials:")
        print("   - Go to 'APIs & Services' > 'Credentials'")
        print("   - Click 'Create Credentials' > 'OAuth client ID'")
        print("   - Choose 'Desktop app'")
        print("   - Download the JSON file")
        print(f"5. Rename it to 'credentials.json' and place in:")
        print(f"   {GMAIL_CREDENTIALS_PATH.parent}")
        print()
        print("After placing credentials.json, run this again.")
        return
    
    print("✅ credentials.json found!")
    print()
    print("Authorizing Gmail API...")
    print("(A browser window will open for authorization)")
    print()
    
    try:
        gmail = GmailAPIService()
        gmail._get_credentials()
        print()
        print("✅ Gmail API authorized successfully!")
        print(f"   Token saved to: {GMAIL_TOKEN_PATH}")
        print()
        print("Email service is now ready to use.")
        
        # Test send
        test = input("Send a test email? (y/n): ").strip().lower()
        if test == 'y':
            to_email = input("Enter your email address: ").strip()
            result = gmail.send_email(
                to_email=to_email,
                subject="Test Email - Radiology AI Assistant",
                html_content="<h1>It works!</h1><p>Gmail API is configured correctly.</p>",
                text_content="It works! Gmail API is configured correctly."
            )
            if result["success"]:
                print(f"✅ Test email sent to {to_email}")
            else:
                print(f"❌ Failed: {result['message']}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    setup_gmail_oauth()

