# Ready-to-Use Curl Commands

This document provides copy-pastable curl commands for testing the API endpoints, with placeholders you need to replace.

## Configuration

Replace `YOUR_API_KEY` with your actual xAI API key in all commands.

## Health Check

```bash
curl -X GET http://localhost:8000/health
```

## Image Generation

### Basic Image Generation

```bash
curl -X POST http://localhost:8000/api/v1/images/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "prompt": "A beautiful mountain landscape at sunset",
    "model": "grok-2-image"
  }'
```

### Multiple Images

```bash
curl -X POST http://localhost:8000/api/v1/images/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "prompt": "Abstract geometric patterns in bright colors",
    "model": "grok-2-image",
    "n": 3
  }'
```

### Base64 Response Format

```bash
curl -X POST http://localhost:8000/api/v1/images/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "prompt": "A serene ocean view with palm trees",
    "model": "grok-2-image",
    "response_format": "b64_json"
  }'
```

> **Note**: xAI API currently doesn't support the `quality`, `size`, and `style` parameters. These will be ignored if included in your request.

### OpenAI SDK Compatible Endpoint

For compatibility with the OpenAI SDK, you can also use the `/images/generations` endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "prompt": "A cyberpunk city scene with flying cars",
    "model": "grok-2-image",
    "n": 1
  }'
```

This is functionally identical to the `/images/generate` endpoint but matches the OpenAI SDK endpoint naming.

## Image Vision

### Analyze Image from URL

```bash
curl -X POST http://localhost:8000/api/v1/vision/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "image": {
      "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
    },
    "prompt": "What animals are in this image and what are they doing?",
    "detail": "high"
  }'
```

### Analyze Local Image (Base64)

First, encode your image:

```bash
base64 -i path/to/your/image.jpg | tr -d '\n' > image_base64.txt
```

Then use the encoded data:

```bash
curl -X POST http://localhost:8000/api/v1/vision/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "image": {
      "b64_json": "'$(cat image_base64.txt)'"
    },
    "prompt": "Describe this image in detail",
    "detail": "high"
  }'
```

## Chat Completions

### Simple Question

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {
        "role": "user",
        "content": "What are the main challenges in artificial intelligence today?"
      }
    ]
  }'
```

### Streaming Response

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {
        "role": "user",
        "content": "Write a short poem about technology."
      }
    ],
    "stream": true
  }'
```

This will return a streaming response using Server-Sent Events (SSE) format. Each chunk will start with `data: ` followed by a JSON object, and the stream will end with `data: [DONE]`.

### Processing Streaming Responses with Command Line Tools

You can use common command line tools to process streaming responses:

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ],
    "stream": true
  }' | grep -o '"content":"[^"]*"' | sed 's/"content":"//g' | sed 's/"//g' | tr -d '\n'
```

This pipeline extracts and concatenates just the content field from each chunk.

### OpenAI SDK Vision Format

For compatibility with the OpenAI SDK's vision handling, you can send vision requests through the chat completions endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "messages": [
      {
        "role": "user", 
        "content": [
          {
            "type": "image_url",
            "image_url": {
              "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg",
              "detail": "high"
            }
          },
          {
            "type": "text",
            "text": "What animals are in this image?"
          }
        ]
      }
    ],
    "temperature": 0.01
  }'
```

This format is needed when using the OpenAI SDK for vision analysis.

### Note on Vision Streaming

While the API supports streaming for regular chat completions, it currently **does not** support streaming for vision requests. If you set `stream: true` in a vision request, the API will automatically convert it to a non-streaming request and return a complete response with the header `X-Stream-Fallback` to indicate this fallback.

Example of a vision request with streaming that will automatically fall back:

```bash
curl -i -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "messages": [
      {
        "role": "user", 
        "content": [
          {
            "type": "image_url",
            "image_url": {
              "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
            }
          },
          {
            "type": "text",
            "text": "What is in this image?"
          }
        ]
      }
    ],
    "stream": true
  }'
```

The `-i` flag shows headers, where you can see the `X-Stream-Fallback` header in the response.

### Conversation with System Prompt

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {
        "role": "system",
        "content": "You are a creative writing assistant specialized in science fiction."
      },
      {
        "role": "user",
        "content": "Write a short opening paragraph for a story about space exploration."
      }
    ],
    "temperature": 0.8
  }'
```

### Multi-turn Conversation

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {
        "role": "user",
        "content": "What is deep learning?"
      },
      {
        "role": "assistant",
        "content": "Deep learning is a subset of machine learning that uses neural networks with multiple layers (hence \"deep\") to analyze various factors of data. It attempts to mimic the human brain, allowing it to learn from large amounts of data and make intelligent decisions."
      },
      {
        "role": "user",
        "content": "How is it different from traditional machine learning?"
      }
    ]
  }'
```

## Testing Different Models

### Using grok-3-beta for Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "grok-3-beta",
    "messages": [
      {
        "role": "user",
        "content": "Explain how quantum computers work."
      }
    ]
  }'
```

### Using Latest Vision Model

```bash
curl -X POST http://localhost:8000/api/v1/vision/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "image": {
      "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
    }
  }'
```

## Environment-Specific Examples

### For Windows Command Prompt

```cmd
curl -X POST http://localhost:8000/api/v1/images/generate -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_API_KEY" -d "{\"prompt\":\"A beautiful sunset over mountains\",\"model\":\"grok-2-image\"}"
```

### For Windows PowerShell

```powershell
$body = @{
    prompt = "A beautiful sunset over mountains"
    model = "grok-2-image"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/images/generate" -Method Post -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer YOUR_API_KEY"
} -Body $body
``` 