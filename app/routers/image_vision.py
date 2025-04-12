from fastapi import APIRouter, Depends, HTTPException, status
import logging
import time

from app.models.schemas import ImageVisionRequest, ImageVisionResponse, ErrorResponse
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
    "/vision/analyze",
    response_model=ImageVisionResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}
    },
    summary="Analyze images using xAI Vision API",
    description="Analyze and understand image content using xAI's vision models"
)
async def analyze_image(
    request: ImageVisionRequest,
    xai_client: XAIClient = Depends(get_xai_client)
) -> ImageVisionResponse:
    try:
        # Validate that at least one image source is provided
        if not request.image.url and not request.image.b64_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either image URL or base64 encoded image data must be provided"
            )
        
        # Prepare the request data
        request_data = request.dict(exclude_none=True)
        
        # Set default model if not provided
        if "model" not in request_data:
            request_data["model"] = settings.DEFAULT_VISION_MODEL
            
        model_used = request_data.get("model", settings.DEFAULT_VISION_MODEL)
            
        # Make the API request
        start_time = time.time()
        response = await xai_client.analyze_image(request_data)
        duration = time.time() - start_time
        
        logger.info(f"Image analysis completed in {duration:.2f} seconds")
        
        # Add any missing fields required by our schema
        if "created" not in response:
            response["created"] = int(time.time())
        
        if "model" not in response:
            response["model"] = model_used
            
        if "usage" not in response:
            response["usage"] = {}
        
        return response
        
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {str(e)}"
        ) 