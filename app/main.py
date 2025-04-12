from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from app.routers import image_generation, image_vision, chat
from app.core.config import settings
from app.core.middleware import RequestLoggerMiddleware, RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="xAI Grok API",
    description="API for xAI Grok services including image generation, image understanding, and chat",
    version="0.1.0",
)

# Add middlewares
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(RateLimitMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(image_generation.router, prefix="/api/v1", tags=["Image Generation"])
app.include_router(image_vision.router, prefix="/api/v1", tags=["Image Vision"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 