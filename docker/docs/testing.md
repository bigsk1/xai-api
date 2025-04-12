# Testing the Dockerized xAI API

This document provides commands to test the xAI API after deploying it with Docker. All commands assume the API is running with the Nginx reverse proxy as configured in the docker-compose.yaml file.

## Prerequisites

- The Docker containers are running
- You have your xAI API key

## Quick Start

For automated testing of all endpoints, run the included test script:

```bash
# Set your API key
export XAI_API_KEY=your_api_key_here

# Run the test script
./docker/test_api.sh
```

## Manual Testing

If you prefer to test endpoints individually, use the following curl commands:

### 1. Health Check

```bash
# Test HTTP to HTTPS redirection
curl -L -v http://localhost/health

# Test HTTPS health endpoint
curl -k https://localhost/health
```

Expected output:
```json
{"status":"healthy","version":"0.1.0"}
```

### 2. Chat Completion

```bash
export XAI_API_KEY=your_api_key_here

curl -k -X POST "https://localhost/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-3-mini-beta",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

### 3. Image Generation

```bash
curl -k -X POST "https://localhost/api/v1/images/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "model": "grok-2-image"
  }'
```

### 4. OpenAI SDK Compatible Endpoint

```bash
curl -k -X POST "https://localhost/api/v1/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "prompt": "A futuristic cityscape",
    "model": "grok-2-image"
  }'
```

### 5. Vision Analysis

```bash
curl -k -X POST "https://localhost/api/v1/vision/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "image": {
      "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
    },
    "prompt": "What animals are in this image?"
  }'
```

### 6. Test OpenAI SDK Vision Format

```bash
curl -k -X POST "https://localhost/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
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
    ]
  }'
```

## Security Tests

### 1. Test Rate Limiting

```bash
# Send multiple requests in quick succession to trigger rate limiting
for i in {1..10}; do
  curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost/health
  sleep 0.1
done
```

### 2. Test HTTP to HTTPS Redirection

```bash
curl -v -L http://localhost/api/v1/chat/completions
```

You should see a 301 redirect to HTTPS.

### 3. Test Documentation Endpoints (Should be Blocked)

```bash
curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost/docs
curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost/redoc
curl -k -s -o /dev/null -w "%{http_code}\n" https://localhost/openapi.json
```

All should return a 404 status code since these endpoints are blocked for security.

## Using Python with the OpenAI SDK

You can also test the API using the OpenAI SDK:

```python
import os
from openai import OpenAI

# Set up environment variables
os.environ["OPENAI_API_KEY"] = "your_api_key_here"
os.environ["OPENAI_BASE_URL"] = "https://localhost/api/v1"

# Initialize client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# Test chat completion
response = client.chat.completions.create(
    model="grok-3-mini-beta",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)
print(response.choices[0].message.content)

# Test image generation
image_response = client.images.generate(
    model="grok-2-image",
    prompt="A beautiful sunset over mountains",
    n=1
)
print(image_response.data[0].url)
```

> **Note**: When using the Python SDK with the HTTPS endpoint, you may need to add `verify=False` to bypass SSL certificate verification for self-signed certificates or use a proper certificate in production.

## Troubleshooting

- If you see "Connection refused" errors, make sure the containers are running: `docker-compose -f docker/docker-compose.yaml ps`
- Check container logs: `docker logs xai-api` or `docker logs xai-nginx`
- Verify your API key is correct: `grep XAI_API_KEY .env`
- Check Nginx access and error logs: `docker exec xai-nginx cat /var/log/nginx/error.log` 