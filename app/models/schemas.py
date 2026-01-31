from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

# Image Generation Models
class ImageGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text description of the image to generate")
    model: Optional[str] = Field(None, description="Model to use for image generation (e.g., grok-2, grok-3-beta)")
    n: Optional[int] = Field(1, description="Number of images to generate", ge=1, le=10)
    size: Optional[str] = Field(None, description="Size of the generated image (e.g., 1024x1024, 512x512)")
    quality: Optional[str] = Field(None, description="Quality of the generated image (standard or hd)")
    style: Optional[str] = Field(None, description="Style of the generated image (e.g., natural, vivid)")
    response_format: Optional[str] = Field(None, description="The format in which the generated images are returned (url or b64_json)")
    user: Optional[str] = Field(None, description="A unique identifier for the end-user")

class ImageGenerationResponseData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None

class ImageGenerationResponse(BaseModel):
    created: Optional[int] = None
    data: List[ImageGenerationResponseData]
    model: Optional[str] = None

# Image Vision/Understanding Models
class ImageForVision(BaseModel):
    url: Optional[str] = Field(None, description="URL of the image to analyze")
    b64_json: Optional[str] = Field(None, description="Base64 encoded image data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/image.jpg"
            }
        }

class ImageVisionRequest(BaseModel):
    model: Optional[str] = Field(None, description="Model to use for image analysis")
    image: ImageForVision
    prompt: Optional[str] = Field("What's in this image?", description="Text prompt to ask about the image")
    detail: Optional[str] = Field("high", description="Level of detail for image analysis (auto, low, high)")
    max_tokens: Optional[int] = Field(1024, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.01, description="Sampling temperature")
    user: Optional[str] = Field(None, description="A unique identifier for the end-user")

class ImageVisionResponse(BaseModel):
    model: Optional[str] = None
    created: Optional[int] = None
    content: str
    usage: Optional[Dict[str, Any]] = None

# Tool/Function Calling Models
class FunctionParameters(BaseModel):
    type: str = Field("object", description="Parameter type, typically 'object'")
    properties: Dict[str, Any] = Field(..., description="Parameter properties as a JSON Schema object")
    required: Optional[List[str]] = Field(None, description="List of required parameter names")
    additionalProperties: Optional[bool] = Field(None, description="Whether additional properties are allowed")

class Function(BaseModel):
    name: str = Field(..., description="Function name", max_length=64, pattern="^[a-zA-Z0-9_-]+$")
    description: str = Field(..., description="Function description", max_length=1024)
    parameters: FunctionParameters = Field(..., description="Function parameters as JSON Schema")

class Tool(BaseModel):
    type: str = Field("function", description="Tool type, currently only 'function' is supported")
    function: Function = Field(..., description="Function definition")

class ToolCall(BaseModel):
    id: str = Field(..., description="Unique identifier for the tool call")
    type: str = Field("function", description="Type of tool call")
    function: Dict[str, Any] = Field(..., description="Function call details with 'name' and 'arguments'")

class ToolChoice(BaseModel):
    """Tool choice parameter - can be 'none', 'auto', 'required', or a specific tool"""
    pass  # Union type will be handled in ChatCompletionRequest

# Chat Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (system, user, assistant, tool)")
    content: Any = Field(..., description="Content of the message. Can be a string or an array for vision requests.")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls made by the assistant")
    tool_call_id: Optional[str] = Field(None, description="Tool call ID for tool responses")

class TokenDetails(BaseModel):
    text_tokens: Optional[int] = None
    audio_tokens: Optional[int] = None
    image_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    accepted_prediction_tokens: Optional[int] = None
    rejected_prediction_tokens: Optional[int] = None

class UsageMetrics(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    prompt_tokens_details: Optional[Dict[str, Any]] = None
    completion_tokens_details: Optional[Dict[str, Any]] = None

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = Field(None, description="ID of the model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages in the conversation")
    max_tokens: Optional[int] = Field(1024, description="Maximum number of tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(1.0, description="Nucleus sampling parameter")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    user: Optional[str] = Field(None, description="A unique identifier for the end-user")
    tools: Optional[List[Tool]] = Field(None, description="List of tools the model can call")
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Controls which tool is called. Can be 'none', 'auto', 'required', or specify a tool")

class ChatCompletionResponse(BaseModel):
    id: Optional[str] = None
    object: Optional[str] = None
    created: Optional[int] = None
    model: Optional[str] = None
    choices: List[Dict[str, Any]]
    usage: Optional[Union[Dict[str, Any], UsageMetrics]] = None

# Adding detailed models for chat completion response
class ChatCompletionResponseMessage(BaseModel):
    role: str = Field(..., description="The role of the message author (e.g., 'assistant')")
    content: Optional[str] = Field(None, description="The content of the message")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls made by the assistant")

class ChatCompletionResponseChoice(BaseModel):
    index: int = Field(..., description="The index of the choice")
    message: ChatCompletionResponseMessage = Field(..., description="The message content")
    finish_reason: Optional[str] = Field(None, description="The reason the model stopped generating (e.g., 'stop', 'length')")

class ChatCompletionResponseChunk(BaseModel):
    id: Optional[str] = None
    object: Optional[str] = Field("chat.completion.chunk", description="Object type, always 'chat.completion.chunk' for streaming")
    created: Optional[int] = None
    model: Optional[str] = None
    choices: List[Dict[str, Any]] = Field(..., description="List of message delta chunks")
    usage: Optional[Union[Dict[str, Any], UsageMetrics]] = None

class ChatCompletionStreamChoice(BaseModel):
    index: int = Field(..., description="The index of the choice")
    delta: Dict[str, Any] = Field(..., description="The content delta for this chunk")
    finish_reason: Optional[str] = Field(None, description="The reason the model stopped generating, if applicable")

# Responses API Models (xAI Native Agentic Tools API)
class ServerSideTool(BaseModel):
    """Server-side tool definition (web_search, x_search, code_execution)"""
    type: str = Field(..., description="Tool type: 'web_search', 'x_search', or 'code_execution'")
    
class ResponsesInputMessage(BaseModel):
    """Message format for Responses API input"""
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'tool'")
    content: Optional[Any] = Field(None, description="Message content")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls made by assistant")
    tool_call_id: Optional[str] = Field(None, description="ID of tool call being responded to")

class ResponsesRequest(BaseModel):
    """Request model for xAI Responses API"""
    model: str = Field(..., description="Model to use (e.g., 'grok-4', 'grok-4-fast')")
    input: List[ResponsesInputMessage] = Field(..., description="Input messages (replaces 'messages')")
    max_output_tokens: Optional[int] = Field(None, description="Maximum tokens to generate (replaces 'max_tokens')")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    top_p: Optional[float] = Field(1.0, description="Nucleus sampling parameter")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    previous_response_id: Optional[str] = Field(None, description="ID of previous response to continue conversation")
    store: Optional[bool] = Field(True, description="Store conversation server-side for 30 days")
    tools: Optional[List[Union[Tool, ServerSideTool]]] = Field(None, description="Mix of client-side and server-side tools")
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Tool choice control")
    include: Optional[List[str]] = Field(None, description="Additional data to include (e.g., 'reasoning.encrypted_content', 'code_execution_call_output')")
    user: Optional[str] = Field(None, description="Unique identifier for end-user")

class ServerSideToolUsage(BaseModel):
    """Server-side tool usage metrics"""
    web_search_calls: Optional[int] = Field(0, description="Number of web search calls")
    x_search_calls: Optional[int] = Field(0, description="Number of X search calls")
    code_execution_calls: Optional[int] = Field(0, description="Number of code execution calls")

class ResponsesUsageMetrics(BaseModel):
    """Usage metrics for Responses API"""
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None

class Citation(BaseModel):
    """Citation information from searches"""
    url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = Field(None, description="Source type: 'web' or 'x'")

class OutputContent(BaseModel):
    """Content item in response output"""
    type: str = Field(..., description="Content type: 'output_text', 'tool_call', etc.")
    text: Optional[str] = Field(None, description="Text content")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls")

class ResponsesOutputMessage(BaseModel):
    """Output message from Responses API"""
    type: str = Field(..., description="Output type: 'message', 'web_search_call', etc.")
    role: Optional[str] = Field(None, description="Message role")
    content: Optional[List[OutputContent]] = Field(None, description="Array of content items")
    tool_calls: Optional[List[ToolCall]] = Field(None, description="Tool calls made")
    # Allow additional fields for tool-specific responses
    class Config:
        extra = "allow"

class ResponsesResponse(BaseModel):
    """Response model for xAI Responses API"""
    id: str = Field(..., description="Response ID (can be used as previous_response_id)")
    object: str = Field("response", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    model: str = Field(..., description="Model used")
    output: List[Dict[str, Any]] = Field(..., description="Array of output messages (flexible schema)")
    usage: Optional[ResponsesUsageMetrics] = None
    server_side_tool_usage: Optional[ServerSideToolUsage] = None
    citations: Optional[List[Citation]] = Field(None, description="Citations from web/X searches")
    finish_reason: Optional[str] = Field(None, description="Reason completion stopped")
    
    class Config:
        extra = "allow"

class ResponsesStreamChunk(BaseModel):
    """Streaming chunk for Responses API"""
    id: str
    object: str = Field("response.chunk", description="Object type for streaming")
    created: int
    model: str
    output: List[Dict[str, Any]] = Field(..., description="Partial output data")
    usage: Optional[ResponsesUsageMetrics] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_outputs: Optional[List[Dict[str, Any]]] = None

# Error Response
class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    details: Optional[Dict[str, Any]] = None 