# xAI Grok API FastAPI Application

A modular FastAPI application to interact with xAI Grok API for image generation, image understanding, and chat functionalities.

![Image](https://github.com/user-attachments/assets/102af561-f379-4b3f-a8e5-dc7c592dd9d7)

## Features

- **Responses API (NEW!)**: xAI's modern agentic tools API with native web search, X search, and code execution
- **Image Generation**: Generate images using xAI Grok models based on text prompts
- **Image Vision/Understanding**: Analyze and understand image content
- **Chat Completions**: Generate text responses using xAI Grok chat models with optional client-side function calling
- **Streaming Support**: Stream responses in real-time as they are generated
- **Function Calling**: Define and execute custom functions on this server (optional)
- **Native Agentic Tools**: Let Grok autonomously search the web, X, or execute code (optional)
- **Optional API Authentication**: Bearer token authentication middleware for access control
- **Docker Ready**: Production-ready Docker setup with Nginx reverse proxy
- **Security Hardened**: SSL/TLS, security headers, and non-root user setup
- Modular architecture for easy extension
- Support for multiple models
- Rate limiting and request logging

## OpenAI SDK Compatibility

This API is fully compatible with the OpenAI SDK! You can use the same SDK you might already be using for OpenAI, just pointing to our xAI API instead.

### Using the OpenAI SDK

```python
import os
from openai import OpenAI

# Set up client
client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="https://yourdomain.com/api/v1"  # Point to your API server
)

# Chat completion
chat_response = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ],
    temperature=0.7
)
print(chat_response.choices[0].message.content)

# Streaming chat completion
stream = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",
    messages=[
        {"role": "user", "content": "Write a short story about space travel"}
    ],
    stream=True,
    temperature=0.7
)
for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="", flush=True)

# Vision analysis
vision_response = client.chat.completions.create(
    model="grok-2-vision-latest",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high",
                    },
                },
                {
                    "type": "text",
                    "text": "What's in this image?",
                },
            ],
        }
    ],
    temperature=0.01
)
print(vision_response.choices[0].message.content)

# Image generation
image_response = client.images.generate(
    model="grok-2-image",
    prompt="A beautiful sunset over mountains",
    n=1
)
print(f"Image URL: {image_response.data[0].url}")
```

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- Docker and Docker Compose (for containerized deployment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/bigsk1/xai-api
   cd xai-api
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with your API keys:
   ```
   XAI_API_KEY=your_xai_api_key
   XAI_API_BASE=https://api.x.ai/v1
   
   # Optional configuration
   DEFAULT_CHAT_MODEL=grok-4-1-fast-non-reasoning
   DEFAULT_IMAGE_GEN_MODEL=grok-2-image
   DEFAULT_VISION_MODEL=grok-2-vision-latest 
     # Optional: Rate limiting
     API_RATE_LIMIT=100
     API_RATE_LIMIT_PERIOD=3600
     
     # Optional: Enable tools (both disabled by default for security)
     XAI_TOOLS_ENABLED=false              # Enable client-side function calling
     XAI_NATIVE_TOOLS_ENABLED=false       # Enable xAI's native agentic tools
     
     # Optional: API Authentication (disabled by default)
     XAI_API_AUTH=false                   # Enable bearer token authentication
     XAI_API_AUTH_TOKEN=                  # Set a secure token when auth enabled
     ```

### Running the API

#### Local Development

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

#### Docker Deployment

This project includes a production-ready Docker setup with Nginx for secure deployment:

1. Generate SSL certificates (for development):
   ```bash
   cd docker/nginx/ssl
   ./generate-self-signed-cert.sh
   ```

2. Start the containers:
   ```bash
   docker-compose -f docker/docker-compose.yaml up -d
   ```

3. The API will be available at:
   - HTTPS: `https://localhost/api/v1` (secured with SSL/TLS)
   - HTTP: `http://localhost/api/v1` (redirects to HTTPS)

4. Run the test script to verify all endpoints:
   ```bash
   ./docker/test_api.sh
   ```

For more details on the Docker setup, see [Docker Documentation](docker/README.md) and [Testing Documentation](docker/docs/testing.md).

## API Documentation

Once the server is running, you can access the auto-generated API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Example Usage

For detailed examples of how to use the API, check the documentation in the `docs` folder:

- **[Responses API Guide](docs/responses_api.md)** - **NEW!** Complete guide to xAI's native agentic tools
- **[Function Calling Guide](docs/function_calling.md)** - Guide to client-side function calling
- **[API Authentication](docs/authentication.md)** - Optional bearer token authentication setup
- **[Dual Authentication](docs/dual_authentication.md)** - Using Traefik BasicAuth + API token together
- **[Documentation Security](docs/docs_security.md)** - Controlling access to /docs and API documentation
- [API Usage Examples](docs/examples.md) - Examples of using each endpoint with curl
- [Streaming API](docs/streaming.md) - Guide to using streaming responses for real-time output
- [Ready-to-Use Curl Commands](docs/curl_commands.md) - Copy-pastable curl commands for testing
- [API Integration Guide](docs/api_integration.md) - Code examples for integrating with different programming languages

## Endpoints

### Responses API (Recommended - NEW!)

- `POST /api/v1/responses`: Create responses with xAI's native agentic tools (web search, X search, code execution)

### Chat Completions

- `POST /api/v1/chat/completions`: Generate chat completions with optional client-side function calling

### Image Generation

- `POST /api/v1/images/generate`: Generate images based on text prompts
- `POST /api/v1/images/generations`: OpenAI SDK compatible endpoint

### Image Vision/Understanding

- `POST /api/v1/vision/analyze`: Analyze image content using vision models

### Health Check

- `GET /health`: Check the API health status

## Configuration

The application is configurable through environment variables or a `.env` file:

- `XAI_API_KEY`: Your xAI API key (required)
- `XAI_API_BASE`: Base URL for xAI API (default: "https://api.x.ai/v1")
- `DEFAULT_CHAT_MODEL`: Default model for chat completions (default: "grok-4-1-fast-non-reasoning")
- `DEFAULT_IMAGE_GEN_MODEL`: Default model for image generation (default: "grok-2-image")
- `DEFAULT_VISION_MODEL`: Default model for image vision (default: "grok-2-vision-latest")
- `API_RATE_LIMIT`: Maximum number of requests per time window (default: 100)
- `API_RATE_LIMIT_PERIOD`: Time window in seconds for rate limiting (default: 3600)
- `XAI_TOOLS_ENABLED`: Enable client-side function calling (default: false, for security)
- `XAI_NATIVE_TOOLS_ENABLED`: Enable xAI's native agentic tools (default: false, for security)

## Security

- API key authentication
- Rate limiting
- CORS configuration
- Request logging
- When using Docker:
  - SSL/TLS encryption with modern cipher configuration
  - Security headers (HSTS, CSP, X-Content-Type-Options, etc.)
  - Non-root container user
  - Read-only filesystem where possible
  - Nginx reverse proxy with request buffering
  - No privilege escalation
  - Temporary filesystem for volatile data

## Future Enhancements

This API currently serves as a secure proxy to xAI's Grok API services. However, there are many opportunities to enhance its capabilities:

- **Specialized Endpoints**: Create purpose-built endpoints for summarization, data extraction, and research
- **External Integrations**: Connect to additional data sources, vector databases, and APIs
- **Custom Logic**: Add pre-processing and post-processing capabilities to improve responses
- **Enhanced Features**: Combine image generation with text generation, validate code outputs, etc.

For a detailed roadmap and technical implementation ideas, see the [Future API Enhancements](docs/future-api.md) documentation.

## License

[MIT](LICENSE)
