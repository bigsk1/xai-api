# API Usage Examples

This document provides examples of how to use the xAI Grok API endpoints with curl commands.

## Prerequisites

- An API key for xAI Grok API
- curl installed on your system

## Health Check

### Check API Health

```bash
curl -X GET http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

## Image Generation

> **Note**: Currently, according to xAI documentation, the parameters `quality`, `size`, and `style` are not supported by the xAI API and will be ignored.

### Generate an Image

```bash
curl -X POST http://localhost:8000/api/v1/images/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "prompt": "A beautiful sunset over mountains with a lake in the foreground",
    "model": "grok-2-image",
    "n": 1,
    "response_format": "url"
  }'
```

Expected response:
```json
{
  "created": 1700000000,
  "data": [
    {
      "url": "https://example.com/image-url.jpg",
      "revised_prompt": "A beautiful sunset over mountains with a lake in the foreground"
    }
  ],
  "model": "grok-2-image"
}
```

### Using OpenAI SDK Compatible Endpoint

This endpoint is identical to the one above but matches the OpenAI SDK endpoint naming for compatibility:

```bash
curl -X POST http://localhost:8000/api/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "prompt": "A beautiful sunset over mountains with a lake in the foreground",
    "model": "grok-2-image",
    "n": 1
  }'
```

### Generate Multiple Images

```bash
curl -X POST http://localhost:8000/api/v1/images/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "prompt": "A futuristic city with flying cars and tall skyscrapers",
    "model": "grok-2-image",
    "n": 3,
    "response_format": "url"
  }'
```

### Generate Image with Base64 Response

```bash
curl -X POST http://localhost:8000/api/v1/images/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "prompt": "Bioluminescent jellyfish in the deep ocean",
    "model": "grok-2-image",
    "n": 1,
    "response_format": "b64_json"
  }'
```

## Image Vision/Analysis

### Analyze an Image from URL

```bash
curl -X POST http://localhost:8000/api/v1/vision/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "image": {
      "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
    },
    "prompt": "What animals are in this image and what are they doing?",
    "detail": "high",
    "temperature": 0.01,
    "max_tokens": 1024
  }'
```

Expected response:
```json
{
  "model": "grok-2-vision-latest",
  "created": 1700000000,
  "content": "In this image, there is a dog and a cat sitting side by side on what appears to be a couch or soft surface. The dog is a brown and white Boxer or similar breed with a short coat, while the cat appears to be a gray tabby. Both animals are looking directly at the camera. They seem to be in a relaxed, calm state, simply sitting together in what looks like a domestic home environment.",
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 156,
    "total_tokens": 256
  }
}
```

### Analyze an Image with Base64 Data

```bash
curl -X POST http://localhost:8000/api/v1/vision/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "image": {
      "b64_json": "BASE64_ENCODED_IMAGE_DATA"
    },
    "prompt": "Describe this image in detail",
    "detail": "high",
    "max_tokens": 1024
  }'
```

### Using OpenAI SDK for Image Analysis

Here's an example using the OpenAI SDK to analyze an image:

```python
import os
from openai import OpenAI

XAI_API_KEY = os.getenv("XAI_API_KEY")  # Or use your API key directly
image_url = "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"

# Initialize client with xAI base URL
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="http://localhost:8000/api/v1",  # Point to your FastAPI server
)

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                    "detail": "high",
                },
            },
            {
                "type": "text",
                "text": "What's in this image?",
            },
        ],
    },
]

completion = client.chat.completions.create(
    model="grok-2-vision-latest",
    messages=messages,
    temperature=0.01,
)

print(completion.choices[0].message.content)
```

## Chat Completions

### Basic Chat Completion

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ],
    "temperature": 0.7
  }'
```

### Streaming Chat Completion

You can use streaming to receive responses as they're being generated:

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {"role": "user", "content": "Write a short poem about the ocean"}
    ],
    "stream": true,
    "temperature": 0.7
  }'
```

For more detailed information about streaming, see the [Streaming API documentation](./streaming.md).

### Chat Completion with System Message

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant specialized in explaining scientific concepts."
      },
      {
        "role": "user",
        "content": "What is quantum computing?"
      },
      {
        "role": "assistant",
        "content": "Quantum computing is a type of computing that uses quantum phenomena such as superposition and entanglement to perform operations on data."
      },
      {
        "role": "user",
        "content": "Can you explain superposition in simpler terms?"
      }
    ],
    "max_tokens": 1024,
    "temperature": 0.5
  }'
```

### Chat Completion with Lower Temperature

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {
        "role": "user",
        "content": "Write a short poem about artificial intelligence"
      }
    ],
    "max_tokens": 256,
    "temperature": 0.2,
    "top_p": 0.9
  }'
```

## Using with Programming Languages

### Python Example

```python
import requests
import json

def generate_image(prompt):
    url = "http://localhost:8000/api/v1/images/generate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_XAI_API_KEY"
    }
    data = {
        "prompt": prompt,
        "model": "grok-2-image",
        "n": 1
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

image_result = generate_image("A surreal landscape with floating islands")
print(json.dumps(image_result, indent=2))
```

### JavaScript Example

```javascript
async function analyzeImage(imageUrl) {
  const response = await fetch('http://localhost:8000/api/v1/vision/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer YOUR_XAI_API_KEY'
    },
    body: JSON.stringify({
      model: 'grok-2-vision-latest',
      image: {
        url: imageUrl
      },
      max_tokens: 1024
    })
  });
  
  return await response.json();
}

// Usage
analyzeImage('https://example.com/image.jpg')
  .then(result => console.log(result))
  .catch(error => console.error('Error:', error));
```

## Testing with Postman or Similar Tools

You can also test these endpoints using Postman or similar API testing tools:

1. Set the request type (GET/POST)
2. Enter the endpoint URL
3. Add request headers including:
   - Content-Type: application/json
   - Authorization: Bearer YOUR_XAI_API_KEY
4. For POST requests, add the request body in JSON format
5. Send the request and view the response 