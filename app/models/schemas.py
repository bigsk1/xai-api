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

# Chat Models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender (system, user, assistant)")
    content: Any = Field(..., description="Content of the message. Can be a string or an array for vision requests.")

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

class ChatCompletionResponseMessage(BaseModel):
    role: str
    content: str

class ChatCompletionResponse(BaseModel):
    id: Optional[str] = None
    object: Optional[str] = None
    created: Optional[int] = None
    model: Optional[str] = None
    choices: List[Dict[str, Any]]
    usage: Optional[Union[Dict[str, Any], UsageMetrics]] = None

# Error Response
class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    details: Optional[Dict[str, Any]] = None 