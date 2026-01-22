from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
from pathlib import Path

from app.database import init_db, get_settings
from app.utils.logger import setup_logging
from app.routes import auth, games, users, casino
from app.routes import referrals

# Setup logging
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="Mine Gambling Game",
    description="A gambling mine sweeper game with user authentication",
    version="1.0.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths for static files and templates (code root dir)
base_path = Path(__file__).resolve().parent
static_path = base_path / "static"
templates_path = base_path / "templates"
index_file = templates_path / "index.html"

# Mount static files
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(games.router)
app.include_router(users.router)
app.include_router(casino.router)
app.include_router(referrals.router)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting up application")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application")

@app.get("/")
async def root():
    """Serve main SPA or fallback to API info JSON"""
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "message": "Mine Gambling Game API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Application is running"
    }

@app.get("/api/status")
async def status():
    """API status endpoint"""
    return {
        "status": "online",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower()
    )
