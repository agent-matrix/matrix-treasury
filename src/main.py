"""
Main FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from src.api.routes import router
from src.api.autonomous_routes import router as autonomous_router
from src.api.mission_control_routes import router as mission_control_router
from src.db.connection import init_db, get_db
from src.db.seed import seed_if_needed
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

    # Fail-closed in production/staging if token missing (matches Matrix-Hub posture)
    from src.core.config import Environment
    if config.environment in (Environment.PRODUCTION, Environment.STAGING):
        if not config.security.api_token:
            raise RuntimeError("Missing MATRIX_TREASURY_TOKEN (or API_TOKEN/ADMIN_TOKEN) in production/staging")

    # Initialize database
    init_db()

    # Seed database with default data
    logger.info("Seeding database...")
    db = next(get_db())
    try:
        seed_if_needed(db)
    finally:
        db.close()

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
origins = config.security.cors_allow_origins or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # In production you typically want false unless you use cookies.
    allow_credentials=config.security.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(mission_control_router)  # Mission Control (production endpoints)
app.include_router(router, prefix="/api/v1")  # Core treasury API
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
