from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "AI Coaching Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # AI Model API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    DEEPSEEK_API_KEY: str = ""

    # ChromaDB
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000

    # Analysis Configuration
    ANALYSIS_INTERVAL_DAYS: int = 7
    MIN_SESSIONS_FOR_ANALYSIS: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
