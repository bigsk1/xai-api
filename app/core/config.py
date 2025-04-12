from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Keys
    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    
    # API Base URLs
    XAI_API_BASE: str = os.getenv("XAI_API_BASE", "https://api.x.ai/v1")
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:8000",
        "http://localhost:3000",
        "https://localhost",
        "https://localhost:8000",
        "https://localhost:3000",
    ]
    
    # Default models
    DEFAULT_CHAT_MODEL: str = os.getenv("DEFAULT_CHAT_MODEL", "grok-3-mini-beta")
    DEFAULT_IMAGE_GEN_MODEL: str = os.getenv("DEFAULT_IMAGE_GEN_MODEL", "grok-2-image")
    DEFAULT_VISION_MODEL: str = os.getenv("DEFAULT_VISION_MODEL", "grok-2-vision-latest")
    
    # Other configuration parameters
    DEFAULT_IMAGE_SIZE: str = os.getenv("DEFAULT_IMAGE_SIZE", "1024x1024")
    DEFAULT_IMAGE_QUALITY: str = os.getenv("DEFAULT_IMAGE_QUALITY", "standard")
    DEFAULT_IMAGE_STYLE: str = os.getenv("DEFAULT_IMAGE_STYLE", "natural")
    
    # Security and rate limiting
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "100"))
    API_RATE_LIMIT_PERIOD: int = int(os.getenv("API_RATE_LIMIT_PERIOD", "3600"))  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings() 