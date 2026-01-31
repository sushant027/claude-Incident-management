"""
Application entry point
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
