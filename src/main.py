"""
Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.api.routes import router
from src.api.autonomous_routes import router as autonomous_router
from src.db.connection import init_db
from src.core.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.api.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management"""
    logger.info("Starting Matrix Treasury...")
    
    # Initialize database
    init_db()
    
    logger.info("Matrix Treasury started successfully")
    yield
    logger.info("Shutting down Matrix Treasury...")

# Create FastAPI app
app = FastAPI(
    title="Matrix Treasury",
    description="The Definitive Thermo-Economic Engine for Agent-Matrix Ecosystem",
    version="4.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1")
app.include_router(autonomous_router)  # Autonomous routes (already have /api/v1 prefix)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        log_level=config.api.log_level
    )
