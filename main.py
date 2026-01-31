"""
Main FastAPI application
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from contextlib import asynccontextmanager
from database import init_db
from seed_data import seed_database
from database import SessionLocal
from app.routes import auth, incidents, postmortems, corrective_actions, banks, reports
from app.services.scheduler import reminder_scheduler
from app.utils.auth import get_optional_user
from config import settings

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting application...")
    
    # Initialize database
    init_db()
    
    # Seed initial data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    
    # Start email reminder scheduler
    reminder_scheduler.start()
    
    yield
    
    # Shutdown
    print("Shutting down...")
    reminder_scheduler.shutdown()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# Static files and templates
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router)
app.include_router(incidents.router)
app.include_router(postmortems.router)
app.include_router(corrective_actions.router)
app.include_router(banks.router)
app.include_router(reports.router)

# Root redirect
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/login")

# Frontend routes
@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    """Dashboard page"""
    db = SessionLocal()
    try:
        user = get_optional_user(request, db)
        if not user:
            return RedirectResponse(url="/login")
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user": user.to_dict()
        })
    finally:
        db.close()

@app.get("/incidents-list", response_class=HTMLResponse, include_in_schema=False)
async def incidents_list_page(request: Request):
    """Incidents list page"""
    db = SessionLocal()
    try:
        user = get_optional_user(request, db)
        if not user:
            return RedirectResponse(url="/login")
        
        return templates.TemplateResponse("incidents_list.html", {
            "request": request,
            "user": user.to_dict()
        })
    finally:
        db.close()

@app.get("/incidents-detail/{incident_id}", response_class=HTMLResponse, include_in_schema=False)
async def incident_detail_page(request: Request, incident_id: int):
    """Incident detail page"""
    db = SessionLocal()
    try:
        user = get_optional_user(request, db)
        if not user:
            return RedirectResponse(url="/login")
        
        return templates.TemplateResponse("incident_detail.html", {
            "request": request,
            "user": user.to_dict(),
            "incident_id": incident_id
        })
    finally:
        db.close()

@app.get("/search", response_class=HTMLResponse, include_in_schema=False)
async def search_page(request: Request):
    """Search page"""
    db = SessionLocal()
    try:
        user = get_optional_user(request, db)
        if not user:
            return RedirectResponse(url="/login")
        
        return templates.TemplateResponse("search.html", {
            "request": request,
            "user": user.to_dict()
        })
    finally:
        db.close()

@app.get("/architecture/{bank_id}", response_class=HTMLResponse, include_in_schema=False)
async def architecture_page(request: Request, bank_id: int):
    """Bank architecture page"""
    db = SessionLocal()
    try:
        user = get_optional_user(request, db)
        if not user:
            return RedirectResponse(url="/login")
        
        return templates.TemplateResponse("architecture.html", {
            "request": request,
            "user": user.to_dict(),
            "bank_id": bank_id
        })
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.APP_HOST, port=settings.APP_PORT)
