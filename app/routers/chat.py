from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse, JSONResponse
import logging
import time
import json
import uuid
from typing import AsyncGenerator, Optional

from app.models.schemas import ChatCompletionResponse, ErrorResponse, ChatCompletionRequest, Tool
from app.services.xai_client import XAIClient
from app.core.config import settings
from app.utils.tool_validation import validate_tools, validate_tool_choice, ToolValidationError

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

async def process_stream_response(stream_generator, model_used: str) -> AsyncGenerator[str, None]:
    """Process streaming response from xAI API and format it as SSE."""
    try:
        async for chunk in stream_generator:
            # Check if the chunk indicates an error
            if chunk.get("error", False):
                error_message = json.dumps({"error": chunk.get("message", "Unknown error")})
                yield f"data: {error_message}\n\n"
                return
                
            # Format the chunk as SSE
            # Add any missing fields required by our schema
            if "created" not in chunk:
                chunk["created"] = int(time.time())
            
            if "model" not in chunk:
                chunk["model"] = model_used
                
            if "id" not in chunk:
                chunk["id"] = f"chatcmpl-{str(uuid.uuid4())[:8]}"
                
            if "object" not in chunk:
                chunk["object"] = "chat.completion.chunk"
            
            # Clean up the choices to match OpenAI format
            if "choices" in chunk:
                for choice in chunk["choices"]:
                    # Check if there's a delta with reasoning_content
                    if "delta" in choice and "reasoning_content" in choice["delta"]:
                        # Filter out reasoning_content from client response
                        # This is internal processing data and shouldn't be sent to clients
                        if "content" not in choice["delta"]:
                            # If there's no content but there is reasoning, add an empty content
                            # this prevents client-side errors with libraries expecting content
                            choice["delta"]["content"] = ""
                        choice["delta"].pop("reasoning_content", None)
                        
                    # Handle empty delta cases
                    if "delta" in choice and not choice["delta"]:
                        choice["delta"] = {"content": ""}
            
            # Format the JSON and yield as SSE data
            chunk_str = json.dumps(chunk)
            yield f"data: {chunk_str}\n\n"
            
        # Send a final [DONE] event to signal the end of the stream
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Error processing stream: {str(e)}")
        error_message = json.dumps({"error": str(e)})
        yield f"data: {error_message}\n\n"

@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
        status.HTTP_200_OK: {
            "content": {"text/event-stream": {}},
            "description": "Streaming response (when stream=true)"
        }
    },
    summary="Generate chat completions using xAI API",
    description="Generate chat completions based on provided conversation messages using xAI's language models. Set stream=true to receive a streaming response."
)
async def chat_completion(
    request: Request,  # Keep raw request for flexibility
    chat_request: Optional[ChatCompletionRequest] = None,  # Add for OpenAPI documentation
    xai_client: XAIClient = Depends(get_xai_client)
) -> ChatCompletionResponse:
    try:
        # Get raw request data
        request_data = await request.json()
        
        # Set default model if not provided
        if "model" not in request_data:
            request_data["model"] = settings.DEFAULT_CHAT_MODEL
            
        model_used = request_data.get("model", settings.DEFAULT_CHAT_MODEL)
        
        # Sanitize empty tools array - REMOVE the key entirely
        if "tools" in request_data:
            if request_data["tools"] is None or len(request_data["tools"]) == 0:
                logger.debug("Empty/None tools array received, removing key entirely")
                del request_data["tools"]  # Remove entirely, not just set to None
        
        # If tools key doesn't exist but tool_choice is set, remove tool_choice
        if "tools" not in request_data and "tool_choice" in request_data:
            logger.debug("No tools provided but tool_choice set, removing tool_choice")
            del request_data["tool_choice"]
        
        # Handle tools parameter based on XAI_TOOLS_ENABLED setting
        if "tools" in request_data or "tool_choice" in request_data:
            if not settings.XAI_TOOLS_ENABLED:
                logger.warning("Tool calling requested but XAI_TOOLS_ENABLED is false - removing tools from request")
                request_data.pop("tools", None)
                request_data.pop("tool_choice", None)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tool calling is disabled on this server. Set XAI_TOOLS_ENABLED=true to enable."
                )
            else:
                # Validate tools if provided
                try:
                    tools = None
                    if "tools" in request_data:
                        # Parse tools into Pydantic models for validation
                        tools = [Tool(**tool) for tool in request_data["tools"]]
                        validate_tools(tools)
                        logger.info(f"Validated {len(tools)} tools for request")
                    
                    # Validate tool_choice if provided
                    if "tool_choice" in request_data:
                        validate_tool_choice(request_data["tool_choice"], tools)
                        logger.info(f"Validated tool_choice: {request_data['tool_choice']}")
                        
                except ToolValidationError as e:
                    logger.error(f"Tool validation failed: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Tool validation failed: {str(e)}"
                    )
                except Exception as e:
                    logger.error(f"Error parsing tools: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid tool format: {str(e)}"
                    )
        
        # Check if streaming is requested
        is_streaming = request_data.get("stream", False)
        
        # Check if this is a vision request (OpenAI SDK format)
        is_vision_request = False
        if "messages" in request_data and len(request_data["messages"]) > 0:
            for message in request_data["messages"]:
                if "content" in message and isinstance(message["content"], list):
                    is_vision_request = True
                    logger.info("Detected vision request in OpenAI SDK format")
                    break
        
        # Handle streaming for non-vision requests
        if is_streaming and not is_vision_request:
            logger.info(f"Processing streaming chat completion with model {model_used}")
            stream_generator = await xai_client.chat_completion(request_data)
            return StreamingResponse(
                process_stream_response(stream_generator, model_used),
                media_type="text/event-stream"
            )
                
        # For streaming vision requests, we don't support it yet - fall back to non-streaming
        if is_streaming and is_vision_request:
            logger.warning("Streaming for vision requests is not supported by this API implementation. Converting to non-streaming request.")
            # Set stream to false in the request
            request_data["stream"] = False
            # Add a header to indicate fallback occurred
            headers = {"X-Stream-Fallback": "Vision requests don't support streaming - converted to non-streaming"}
        else:
            headers = {}
        
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
            
            # After processing the request, check if this was a fallback case and add headers to response
            if is_streaming and is_vision_request:
                # Create the response with the headers
                return JSONResponse(content=chat_response, headers=headers)
            
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