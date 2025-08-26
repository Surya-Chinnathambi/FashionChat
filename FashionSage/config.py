import os
from typing import Optional

class Settings:
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://fashionsage_user:surya1234@localhost:5432/fashionsage"
    )
    
    # OpenRouter API
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # ChromaDB (running in Docker, not embedded)
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "chroma")   # service name in docker-compose
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", 8002))  # exposed port

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ]

settings = Settings()
