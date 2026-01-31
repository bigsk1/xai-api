from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse, JSONResponse
import logging
import time
import json
import uuid
from typing import AsyncGenerator, Optional

from app.models.schemas import (
    ResponsesResponse, 
    ErrorResponse, 
    ResponsesRequest,
    ServerSideTool
)
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

async def process_response_stream(stream_generator, model_used: str) -> AsyncGenerator[str, None]:
    """Process streaming response from xAI Responses API and format it as SSE."""
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
                chunk["id"] = f"resp-{str(uuid.uuid4())[:8]}"
                
            if "object" not in chunk:
                chunk["object"] = "response.chunk"
            
            # Format the JSON and yield as SSE data
            chunk_str = json.dumps(chunk)
            yield f"data: {chunk_str}\n\n"
            
        # Send a final [DONE] event to signal the end of the stream
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Error processing response stream: {str(e)}")
        error_message = json.dumps({"error": str(e)})
        yield f"data: {error_message}\n\n"

@router.post(
    "",
    response_model=ResponsesResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
        status.HTTP_200_OK: {
            "content": {"text/event-stream": {}},
            "description": "Streaming response (when stream=true)"
        }
    },
    summary="Create response using xAI Responses API with native agentic tools",
    description="""
    Create a response using xAI's new Responses API. This endpoint supports:
    
    - **Native Agentic Tools**: web_search, x_search, code_execution (executed by xAI's servers)
    - **Server-side Storage**: Conversations stored for 30 days with automatic caching
    - **Stateful Conversations**: Use previous_response_id to continue conversations
    - **Citations**: Automatic citations from web and X searches
    - **Mixed Tools**: Combine server-side tools with client-side function calling
    
    Set stream=true to receive a streaming response. Set XAI_NATIVE_TOOLS_ENABLED=true to enable server-side tools.
    """
)
async def create_response(
    request: Request,
    xai_client: XAIClient = Depends(get_xai_client)
):
    try:
        # Get raw request data
        request_data = await request.json()
        
        # Validate required fields
        if "model" not in request_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model field is required for Responses API"
            )
        
        if "input" not in request_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input field is required for Responses API (use 'input' instead of 'messages')"
            )
            
        model_used = request_data.get("model")
        
        # Check if server-side tools are requested
        has_server_tools = False
        if "tools" in request_data:
            for tool in request_data["tools"]:
                tool_type = tool.get("type", "")
                if tool_type in ["web_search", "x_search", "code_execution"]:
                    has_server_tools = True
                    break
        
        # Validate native tools are enabled if server-side tools are requested
        if has_server_tools and not settings.XAI_NATIVE_TOOLS_ENABLED:
            logger.warning("Server-side tools requested but XAI_NATIVE_TOOLS_ENABLED is false")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Native agentic tools are disabled on this server. Set XAI_NATIVE_TOOLS_ENABLED=true to enable."
            )
        
        # Check if streaming is requested
        is_streaming = request_data.get("stream", False)
        
        # Handle streaming
        if is_streaming:
            logger.info(f"Processing streaming response with model {model_used}")
            stream_generator = await xai_client.create_response(request_data)
            return StreamingResponse(
                process_response_stream(stream_generator, model_used),
                media_type="text/event-stream"
            )
        
        # Make the API request (non-streaming)
        start_time = time.time()
        response_result = await xai_client.create_response(request_data)
        
        # Ensure we got a dict, not a generator
        if not isinstance(response_result, dict):
            logger.error(f"Expected dict but got {type(response_result)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected response type from xAI API"
            )
        
        duration = time.time() - start_time
        logger.info(f"Response generated in {duration:.2f} seconds")
        
        # Add any missing fields required by our schema
        if "created" not in response_result:
            response_result["created"] = int(time.time())
        
        if "model" not in response_result:
            response_result["model"] = model_used
            
        if "id" not in response_result:
            response_result["id"] = f"resp-{str(uuid.uuid4())[:8]}"
            
        if "object" not in response_result:
            response_result["object"] = "response"
        
        # Log response structure for debugging
        logger.debug(f"Response structure: {json.dumps(response_result, default=str)}")
        
        return response_result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Response creation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response creation failed: {str(e)}"
        )

@router.get(
    "/{response_id}",
    response_model=ResponsesResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
    summary="Retrieve a previously stored response",
    description="""
    Retrieve a response that was previously created with store=true.
    
    Responses are stored for 30 days on xAI's servers. Use this to:
    - Retrieve conversation history
    - Continue conversations without resending full history
    - Access responses from different sessions
    
    The response_id is returned in the 'id' field when you create a response.
    """
)
async def retrieve_response(
    response_id: str,
    xai_client: XAIClient = Depends(get_xai_client)
):
    try:
        logger.info(f"Retrieving response: {response_id}")
        response = await xai_client.retrieve_response(response_id)
        
        logger.debug(f"Retrieved response structure: {json.dumps(response, default=str)}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to retrieve response {response_id}: {str(e)}", exc_info=True)
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Response not found: {response_id}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve response: {str(e)}"
        )

@router.delete(
    "/{response_id}",
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
    summary="Delete a previously stored response",
    description="""
    Delete a response that was previously stored on xAI's servers.
    
    Use this to:
    - Clean up conversation history
    - Remove sensitive information
    - Manage storage usage
    
    Once deleted, the response cannot be retrieved or used with previous_response_id.
    """
)
async def delete_response(
    response_id: str,
    xai_client: XAIClient = Depends(get_xai_client)
):
    try:
        logger.info(f"Deleting response: {response_id}")
        result = await xai_client.delete_response(response_id)
        
        return {
            "id": response_id,
            "deleted": True,
            "object": "response.deleted"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete response {response_id}: {str(e)}", exc_info=True)
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Response not found: {response_id}"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete response: {str(e)}"
        )
