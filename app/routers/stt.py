from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
import logging
import httpx
import os

from app.services.xai_client import XAIClient
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_xai_client() -> XAIClient:
    """Dependency to get xAI client."""
    try:
        return XAIClient()
    except Exception as e:
        logger.error(f"Failed to initialize xAI client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize xAI client: {str(e)}"
        )

@router.post(
    "/stt",
    summary="Speech-to-Text Transcription",
    description="Transcribe audio to text using Whisper API and then send it to the chat.",
    tags=["STT"]
)
async def speech_to_text(
    file: UploadFile = File(...),
    xai_client: XAIClient = Depends(get_xai_client)
):
    try:
        # Save the uploaded file temporarily
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Transcribe audio using xAI client
        transcription = await xai_client.transcribe_audio(file_path, model="whisper-1")

        os.remove(file_path)

        # Send the transcribed text to the chat endpoint
        chat_request_data = {
            "model": settings.DEFAULT_CHAT_MODEL,
            "messages": [{"role": "user", "content": transcription.get("text")}]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/chat/completions",
                json=chat_request_data,
                timeout=120.0,
            )

        return JSONResponse(content=response.json())

    except Exception as e:
        logger.error(f"STT failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"STT failed: {str(e)}"
        )
