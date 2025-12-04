"""DataFlow Studio - FastAPI Application Entry Point.

This is the main entry point for the backend API.
Run with: uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router, UPLOAD_DIR, OUTPUT_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("DataFlow Studio starting up...")
    logger.info(f"Upload directory: {UPLOAD_DIR.absolute()}")
    logger.info(f"Output directory: {OUTPUT_DIR.absolute()}")
    
    yield
    
    # Shutdown
    logger.info("DataFlow Studio shutting down...")


# Create FastAPI application
app = FastAPI(
    title="DataFlow Studio API",
    description="Visual data workflow builder API - Build data pipelines with drag-and-drop nodes",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "DataFlow Studio API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
