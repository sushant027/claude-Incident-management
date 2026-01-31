"""
Application configuration
"""
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./incident_platform.db")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    SESSION_COOKIE_NAME = "session_id"
    SESSION_EXPIRE_HOURS = 24
    
    # Gmail SMTP
    GMAIL_USER = os.getenv("GMAIL_USER", "")
    GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    
    # Google Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = "gemini-pro"
    
    # Application
    APP_NAME = os.getenv("APP_NAME", "Enterprise Incident Management Platform")
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    
    # Email Reminder Schedule
    EMAIL_REMINDER_HOUR = 9  # 9 AM daily
    EMAIL_REMINDER_MINUTE = 0
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    @property
    def email_enabled(self):
        return bool(self.GMAIL_USER and self.GMAIL_APP_PASSWORD)
    
    @property
    def ai_enabled(self):
        return bool(self.GEMINI_API_KEY)

settings = Settings()
