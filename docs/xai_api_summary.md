# xAI API Integration Summary

## API Overview

The xAI API consists of three main services:

1. **Chat Completions** - Text generation using language models
2. **Vision Analysis** - Image understanding using vision models
3. **Image Generation** - AI-powered image creation

## API Endpoints

- Chat Completions: `/api/v1/chat/completions`
- Vision Analysis: `/api/v1/vision/analyze`
- Image Generation: `/api/v1/images/generate`

## Integration Options

There are two main ways to integrate with the xAI API:

### 1. Direct HTTP Requests

You can make direct HTTP requests to any endpoint using any HTTP client (requests, httpx, axios, fetch, etc.).
This approach gives you the most control and reliability.

Example (Python):
```python
import requests
import os

API_KEY = os.environ.get("XAI_API_KEY")
API_BASE_URL = "http://localhost:8000"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Chat Completion
response = requests.post(
    f"{API_BASE_URL}/api/v1/chat/completions",
    headers=headers,
    json={
        "model": "grok-4-1-fast-non-reasoning",
        "messages": [
            {"role": "user", "content": "What is the capital of France?"}
        ]
    }
)

# Vision Analysis
response = requests.post(
    f"{API_BASE_URL}/api/v1/vision/analyze",
    headers=headers,
    json={
        "model": "grok-2-vision-latest",
        "image": {"url": "https://example.com/image.jpg"},
        "prompt": "What's in this image?"
    }
)

# Image Generation
response = requests.post(
    f"{API_BASE_URL}/api/v1/images/generate",
    headers=headers,
    json={
        "model": "grok-2-image",
        "prompt": "A beautiful sunset over mountains",
        "n": 1
    }
)
```

### 2. OpenAI SDK

The xAI API is compatible with the OpenAI SDK format, allowing you to use this SDK for simpler integration.

#### Chat Completions & Vision Analysis

The OpenAI SDK works directly with chat completions and vision analysis:

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="http://localhost:8000/api/v1"
)

# Chat Completion
response = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

# Vision Analysis (uses special message format with chat completions)
response = client.chat.completions.create(
    model="grok-2-vision-latest",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high"
                    }
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                }
            ]
        }
    ]
)
```

#### Image Generation with OpenAI SDK

For image generation, you have two options:

**Option 1**: Create an adapter function that mimics the OpenAI SDK interface:

```python
def generate_image(prompt, model="grok-2-image", n=1, size=None, response_format=None):
    """Adapter function to use OpenAI-like parameters but call our API directly"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    data = {
        "model": model,
        "prompt": prompt,
        "n": n
    }
    
    if size:
        data["size"] = size
    
    if response_format:
        data["response_format"] = response_format
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/images/generate",
        headers=headers,
        json=data
    )
    
    result = response.json()
    
    # (Optional) Convert to OpenAI-like response format
    class ImageResponse:
        class Data:
            def __init__(self, data_item):
                self.url = data_item.get('url')
                self.b64_json = data_item.get('b64_json')
        
        def __init__(self, result):
            self.created = result.get('created')
            self.data = [self.Data(item) for item in result.get('data', [])]
    
    return ImageResponse(result)

# Usage
image_result = generate_image("A serene beach at sunset")
print(f"Image URL: {image_result.data[0].url}")
```

**Option 2**: Use direct HTTP requests instead of the SDK for image generation:

```python
# Use OpenAI SDK for chat/vision
from openai import OpenAI
client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

# Use direct HTTP for image generation
import requests

def generate_image(prompt, n=1):
    response = requests.post(
        f"{API_BASE_URL}/api/v1/images/generate",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        json={
            "model": "grok-2-image",
            "prompt": prompt,
            "n": n
        }
    )
    return response.json()
```

## Notes and Considerations

1. **API Endpoint Differences**: The xAI API uses `/images/generate` while the OpenAI API uses `/images/generations`. This causes issues when using the OpenAI SDK for image generation.

2. **Parameter Compatibility**:
   - `size` parameter is accepted but ignored by xAI image generation
   - `quality` parameter is accepted but ignored by xAI image generation 
   - `style` parameter is accepted but ignored by xAI image generation

3. **Vision Analysis Implementation**: Vision analysis is implemented through the chat completions endpoint with a special message format, similar to OpenAI's approach.

4. **Base64 Support**: Both image generation and vision analysis support base64 encoding for submitting/receiving images.

## Conclusion

The xAI API provides a flexible, OpenAI-compatible interface for AI services. For the best integration experience:

- Use the OpenAI SDK for chat completions and vision analysis
- Use direct HTTP requests for image generation
- Consider implementing an adapter function if you want a consistent SDK-like experience for all services 