from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
import logging
import time
import json
import uuid

from app.models.schemas import ChatCompletionRequest, ChatCompletionResponse, ErrorResponse
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
    "/chat/completions",
    response_model=ChatCompletionResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse}
    },
    summary="Generate chat completions using xAI API",
    description="Generate chat completions based on provided conversation messages using xAI's language models"
)
async def chat_completion(
    request: Request,  # Use raw request to handle both standard and vision formats
    xai_client: XAIClient = Depends(get_xai_client)
) -> ChatCompletionResponse:
    try:
        # Get raw request data
        request_data = await request.json()
        
        # Set default model if not provided
        if "model" not in request_data:
            request_data["model"] = settings.DEFAULT_CHAT_MODEL
            
        model_used = request_data.get("model", settings.DEFAULT_CHAT_MODEL)
        
        # Check if this is a vision request (OpenAI SDK format)
        is_vision_request = False
        if "messages" in request_data and len(request_data["messages"]) > 0:
            for message in request_data["messages"]:
                if "content" in message and isinstance(message["content"], list):
                    is_vision_request = True
                    logger.info("Detected vision request in OpenAI SDK format")
                    break
        
        # Make the API request
        start_time = time.time()
        if is_vision_request:
            # This is a vision request through chat completions
            # First, transform the request to our vision API format
            vision_data = {
                "model": model_used
            }
            
            # Extract the first message with the vision content
            for message in request_data["messages"]:
                if isinstance(message.get("content"), list):
                    content_array = message.get("content", [])
                    
                    # Extract image and text
                    for item in content_array:
                        if item.get("type") == "image_url":
                            image_data = item.get("image_url", {})
                            vision_data["image"] = {
                                "url": image_data.get("url")
                            }
                            
                            # Add detail level if present
                            if "detail" in image_data:
                                vision_data["detail"] = image_data.get("detail")
                        
                        elif item.get("type") == "text":
                            vision_data["prompt"] = item.get("text", "What's in this image?")
            
            # Add additional parameters if present
            if "temperature" in request_data:
                vision_data["temperature"] = request_data.get("temperature")
                
            if "max_tokens" in request_data:
                vision_data["max_tokens"] = request_data.get("max_tokens")
            
            # Process the vision request
            response = await xai_client.analyze_image(vision_data)
            
            # Convert vision response format to chat completion format
            chat_response = {
                "id": f"chatcmpl-{str(uuid.uuid4())[:8]}",
                "object": "chat.completion",
                "created": response.get("created", int(time.time())),
                "model": response.get("model", model_used),
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.get("content", "")
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": response.get("usage", {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                })
            }
            
            duration = time.time() - start_time
            logger.info(f"Vision request processed in {duration:.2f} seconds")
            
            return chat_response
        else:
            # Regular chat completion
            response = await xai_client.chat_completion(request_data)
            duration = time.time() - start_time
            
            logger.info(f"Chat completion generated in {duration:.2f} seconds")
            
            # Add any missing fields required by our schema
            if "created" not in response:
                response["created"] = int(time.time())
            
            if "model" not in response:
                response["model"] = model_used
                
            if "id" not in response:
                response["id"] = f"chatcmpl-{str(uuid.uuid4())[:8]}"
                
            if "object" not in response:
                response["object"] = "chat.completion"
                
            # Keep any usage data as-is without trying to modify its structure
            if "usage" not in response:
                response["usage"] = {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            
            # Log the response structure for debugging purposes
            logger.debug(f"Chat completion response structure: {json.dumps(response, default=str)}")
            
            return response
        
    except Exception as e:
        logger.error(f"Chat completion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat completion failed: {str(e)}"
        ) 