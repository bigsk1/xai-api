from fastapi import APIRouter, Depends, HTTPException, status
import logging
import time

from app.models.schemas import ImageGenerationRequest, ImageGenerationResponse, ErrorResponse
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
    "/images/generate",
    response_model=ImageGenerationResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}
    },
    summary="Generate images using xAI API",
    description="Generate images based on a text prompt using xAI's image generation models. Note: quality, size, and style parameters are not currently supported by xAI API and will be ignored."
)
async def generate_image(
    request: ImageGenerationRequest,
    xai_client: XAIClient = Depends(get_xai_client)
) -> ImageGenerationResponse:
    try:
        # Prepare the request data
        request_data = request.dict(exclude_none=True)
        
        # Set default model if not provided
        if "model" not in request_data:
            request_data["model"] = settings.DEFAULT_IMAGE_GEN_MODEL
            
        model_used = request_data.get("model", settings.DEFAULT_IMAGE_GEN_MODEL)
        
        # Log warnings for unsupported parameters but keep them (xAI will ignore them)
        if "quality" in request_data:
            logger.warning("'quality' parameter is not supported by xAI API and will be ignored")
            
        if "size" in request_data:
            logger.warning("'size' parameter is not supported by xAI API and will be ignored")
            
        if "style" in request_data:
            logger.warning("'style' parameter is not supported by xAI API and will be ignored")
        
        # Make the API request
        start_time = time.time()
        response = await xai_client.generate_image(request_data)
        duration = time.time() - start_time
        
        logger.info(f"Image generation completed in {duration:.2f} seconds")
        
        # Add any missing fields required by our schema
        if "created" not in response:
            response["created"] = int(time.time())
        
        if "model" not in response:
            response["model"] = model_used
            
        return response
        
    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )

# Add alias route for OpenAI SDK compatibility
@router.post(
    "/images/generations",
    response_model=ImageGenerationResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}
    },
    summary="Generate images using xAI API (OpenAI SDK compatible endpoint)",
    description="This is an alias of the /images/generate endpoint to ensure compatibility with the OpenAI SDK."
)
async def generate_image_openai_compatible(
    request: ImageGenerationRequest,
    xai_client: XAIClient = Depends(get_xai_client)
) -> ImageGenerationResponse:
    """OpenAI SDK compatibility endpoint for image generation."""
    # Simply call the original handler
    return await generate_image(request, xai_client) 