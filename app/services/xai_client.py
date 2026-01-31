import time
import logging
import json
from typing import Dict, Any, Optional, AsyncGenerator, Union
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class XAIClient:
    def __init__(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        self.api_key = api_key or settings.XAI_API_KEY
        self.api_base = api_base or settings.XAI_API_BASE
        if not self.api_key:
            raise ValueError("XAI API key is required")

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, 
                           params: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generic method to make HTTP requests to the xAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                if method.lower() == "get":
                    response = await client.get(url, headers=headers, params=params)
                elif method.lower() == "delete":
                    response = await client.delete(url, headers=headers)
                elif method.lower() == "post":
                    if files:
                        response = await client.post(url, headers=headers, data=data, files=files)
                    else:
                        headers["Content-Type"] = "application/json"
                        response = await client.post(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            try:
                error_data = e.response.json()
                raise Exception(f"API error: {error_data.get('error', {}).get('message', str(e))}")
            except Exception:
                raise Exception(f"API error: {str(e)}")
                
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Request error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")

    async def _make_streaming_request(self, endpoint: str, data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Make a streaming request to the xAI API using SSE."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }
        
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    
                    # Process the SSE stream
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        
                        # Process complete SSE messages (may contain multiple events)
                        while "\n\n" in buffer:
                            message, buffer = buffer.split("\n\n", 1)
                            
                            # Skip empty messages and heartbeats
                            if not message.strip() or message.strip() == "data: [DONE]":
                                continue
                                
                            # Parse the SSE format (data: {...})
                            if message.startswith("data: "):
                                try:
                                    json_data = json.loads(message[6:])  # Skip 'data: ' prefix
                                    yield json_data
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse SSE message: {e}")
                                    continue
                                    
                    # Process any remaining data in the buffer
                    if buffer.strip() and buffer.strip() != "data: [DONE]" and buffer.startswith("data: "):
                        try:
                            json_data = json.loads(buffer[6:])  # Skip 'data: ' prefix
                            yield json_data
                        except json.JSONDecodeError:
                            pass
                            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during streaming: {e.response.status_code} - {e.response.text}")
            try:
                error_data = e.response.json()
                error_msg = error_data.get('error', {}).get('message', str(e))
            except Exception:
                error_msg = str(e)
            # Yield an error object
            yield {"error": True, "message": f"API error: {error_msg}"}
                
        except httpx.RequestError as e:
            logger.error(f"Request error during streaming: {str(e)}")
            yield {"error": True, "message": f"Request error: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Unexpected error during streaming: {str(e)}")
            yield {"error": True, "message": f"Unexpected error: {str(e)}"}

    async def generate_image(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an image using the xAI image generation API."""
        # Use "/images/generations" for consistency with how OpenAI SDK expects it
        # The FastAPI app has routes for both "/images/generate" and "/images/generations"
        return await self._make_request("post", "/images/generations", data=request_data)

    async def analyze_image(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze an image using the xAI vision API.
        Note: xAI processes vision through the chat completions endpoint with special message formatting
        """
        # Extract relevant data
        model = request_data.get("model", settings.DEFAULT_VISION_MODEL)
        max_tokens = request_data.get("max_tokens", 1024)
        temperature = request_data.get("temperature", 0.01)
        
        # Prepare the image content
        image_data = request_data.get("image", {})
        
        # Build message content
        content = []
        
        # Add image
        if "url" in image_data:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_data["url"],
                    "detail": request_data.get("detail", "high")
                }
            })
        elif "b64_json" in image_data:
            # Format base64 image as data URL
            b64_data = image_data["b64_json"]
            if not b64_data.startswith("data:"):
                b64_data = f"data:image/jpeg;base64,{b64_data}"
            
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": b64_data,
                    "detail": request_data.get("detail", "high")
                }
            })
        
        # Add text prompt
        content.append({
            "type": "text",
            "text": request_data.get("prompt", "What's in this image?")
        })
        
        # Format as chat completion request
        chat_request = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Send as chat completion
        chat_response = await self._make_request("post", "/chat/completions", data=chat_request)
        
        # Extract and reformat response to match our expected format
        try:
            response_content = chat_response["choices"][0]["message"]["content"]
            
            # Format to match our expected schema
            return {
                "model": model,
                "created": chat_response.get("created", int(time.time())),
                "content": response_content,
                "usage": chat_response.get("usage", {})
            }
        except Exception as e:
            logger.error(f"Failed to process vision response: {str(e)}")
            # Return the original response
            return chat_response

    async def chat_completion(self, request_data: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """Get chat completion using the xAI chat API.
        
        If stream=True is in the request_data, returns an async generator that yields chunks of the response.
        Otherwise, returns the complete response as a dictionary.
        """
        # Check if streaming is requested
        if request_data.get("stream", False):
            return self._make_streaming_request("/chat/completions", request_data)
        else:
            # Use the existing non-streaming method
            return await self._make_request("post", "/chat/completions", data=request_data)
    
    async def create_response(self, request_data: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """Create a response using the xAI Responses API (new agentic tools API).
        
        This endpoint supports:
        - Server-side agentic tools (web_search, x_search, code_execution)
        - Server-side conversation storage with previous_response_id
        - Automatic caching and optimization
        
        If stream=True is in the request_data, returns an async generator that yields chunks of the response.
        Otherwise, returns the complete response as a dictionary.
        """
        # Check if streaming is requested
        if request_data.get("stream", False):
            return self._make_streaming_request("/responses", request_data)
        else:
            # Use the existing non-streaming method
            return await self._make_request("post", "/responses", data=request_data)
    
    async def retrieve_response(self, response_id: str) -> Dict[str, Any]:
        """Retrieve a previously stored response by ID.
        
        Args:
            response_id: The ID of the response to retrieve
            
        Returns:
            The response object with all its content
        """
        return await self._make_request("get", f"/responses/{response_id}")
    
    async def delete_response(self, response_id: str) -> Dict[str, Any]:
        """Delete a previously stored response by ID.
        
        Args:
            response_id: The ID of the response to delete
            
        Returns:
            Confirmation of deletion
        """
        return await self._make_request("delete", f"/responses/{response_id}") 