from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import logging

from app.models.schemas import TTSRequest
from app.services.xai_client import XAIClient

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
    "/tts",
    summary="Text-to-Speech",
    description="Convert text to speech using xAI's TTS API.",
    tags=["TTS"]
)
async def text_to_speech(
    request: TTSRequest,
    xai_client: XAIClient = Depends(get_xai_client)
):
    try:
        audio_stream = await xai_client.text_to_speech(
            text=request.text,
            model=request.model,
            voice=request.voice
        )

        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    except Exception as e:
        logger.error(f"TTS failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS failed: {str(e)}"
        )
