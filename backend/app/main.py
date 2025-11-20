from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from .config import settings
from .database import async_engine, Base
from .routers import auth, chat, lessons, teams, progress, admin_lessons


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application"""
    logger.info("Starting AI Coaching Platform...")

    # Create tables (in production, use Alembic migrations)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized")
    yield
    logger.info("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered coaching platform with multi-model support",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(lessons.router)
app.include_router(admin_lessons.router)
app.include_router(teams.router)
app.include_router(progress.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )
