# Streaming API

This document explains how to use the streaming functionality in the xAI Grok API.

## Overview

Streaming allows you to receive responses from the API as they are generated, rather than waiting for the entire response to be completed. This is particularly useful for chat applications where you want to show the response to the user as it's being generated.

Streaming is implemented using Server-Sent Events (SSE), which allows the server to push content to clients as it becomes available.

## Supported Endpoints

Currently, streaming is supported for the following endpoints:

- `/api/v1/chat/completions` - For chat completions

Streaming is **not** supported for:

- `/api/v1/images/generate` - Image generation inherently produces a complete result
- `/api/v1/vision/analyze` - Vision requests currently don't support streaming

## Vision Streaming Considerations

While the xAI documentation suggests streaming is supported for "Chat, Image Understanding, etc.", our current implementation does not support streaming for vision requests. When a vision request is made with `stream=true`:

1. The API will automatically convert it to a non-streaming request
2. A header `X-Stream-Fallback` will be added to the response to indicate this conversion
3. The response will be returned as a complete (non-streaming) response

This affects both the dedicated vision endpoint (`/api/v1/vision/analyze`) and vision requests made through the chat completions endpoint (with image content).

## Using Streaming

### 1. Using the OpenAI SDK

The simplest way to use streaming is with the OpenAI SDK, which will handle the SSE protocol for you:

```python
import os
from openai import OpenAI

# Set up client
client = OpenAI(
    api_key="your_api_key",
    base_url="https://your-api-domain.com/api/v1"  # Point to your API server
)

# Create a streaming completion
stream = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",
    messages=[
        {"role": "user", "content": "Write a short story about a space adventure"}
    ],
    stream=True  # Enable streaming
)

# Print each chunk as it arrives
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 2. Using Direct HTTP Requests

You can also make direct HTTP requests to use streaming:

```python
import requests
import json

API_KEY = "your_api_key"
API_URL = "https://your-api-domain.com/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}

data = {
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
        {"role": "user", "content": "Write a short story about a space adventure"}
    ],
    "stream": True
}

# Make the request with streaming enabled
response = requests.post(API_URL, headers=headers, json=data, stream=True)

# Process the streaming response
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        # SSE format is "data: {...}"
        if line.startswith('data: '):
            if line.strip() == 'data: [DONE]':
                break
            json_str = line[6:]  # Remove 'data: ' prefix
            try:
                chunk = json.loads(json_str)
                content = chunk['choices'][0]['delta'].get('content', '')
                if content:
                    print(content, end='', flush=True)
            except json.JSONDecodeError:
                continue
```

### 3. Using curl

You can test streaming with curl:

```bash
curl -X POST https://your-api-domain.com/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {"role": "user", "content": "Write a short story about a space adventure"}
    ],
    "stream": true
  }'
```

## Stream Format

The streaming response follows the SSE format:

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1692469985,"model":"grok-4-1-fast-non-reasoning","choices":[{"delta":{"role":"assistant","content":"Once"},"index":0,"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1692469985,"model":"grok-4-1-fast-non-reasoning","choices":[{"delta":{"content":" upon"},"index":0,"finish_reason":null}]}

data: [DONE]
```

Each line starts with `data: ` followed by a JSON object or `[DONE]` to indicate the end of the stream.

## Rate Limiting Considerations

When using streaming, keep in mind that:

1. Each streamed response counts as one request against your rate limit
2. Streaming requests may consume more server resources for longer periods
3. If the connection is interrupted, you'll need to start a new request

## Error Handling

If an error occurs during streaming, the API will return an error message in the SSE format:

```
data: {"error":"API error: Invalid authentication token"}
```

You should handle these errors in your client application. 