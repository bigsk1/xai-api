# Testing the Dockerized xAI API

This document provides commands to test the xAI API after deploying it with Docker.

## Prerequisites

- The Docker containers are running
- You have your xAI API key
- (Optional) API authentication token if `XAI_API_AUTH=true`

## Environment Variables for Testing

```bash
# Required
export XAI_API_KEY=your_xai_api_key_here

# If API auth is enabled
export XAI_API_AUTH_TOKEN=your_auth_token_here
```

## Quick Start - Automated Testing

Run the comprehensive test suite:

```bash
# Make sure server is running
docker-compose -f docker/docker-compose.yaml up -d

# Run comprehensive tests
python tests/test_comprehensive.py
```

## Manual Testing

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected output:
```json
{"status":"healthy","version":"0.1.0"}
```

### 2. Chat Completion - Basic

```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

### 3. Chat Completion - With Function Calling (Proxy Mode)

**Important:** This is **validation-only mode**. The API:
- ✅ Validates tool definitions for security
- ✅ Passes tools to xAI API
- ✅ Returns xAI's response (including tool calls)
- ❌ Does NOT execute tools on this server

```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {"role": "user", "content": "What is the weather in San Francisco?"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get the current weather for a location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City and state, e.g. San Francisco, CA"
              },
              "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"]
              }
            },
            "required": ["location"]
          }
        }
      }
    ]
  }'
```

**What happens:**
1. This proxy validates the tool definition (name length, dangerous patterns, etc.)
2. Forwards request to xAI API with tools included
3. xAI model decides if it wants to call the function
4. Returns xAI's response (may include `tool_calls` in message)
5. **Your client app** executes the function and sends results back

### 4. Responses API - Basic

```bash
curl -X POST "http://localhost:8000/api/v1/responses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "input": [
      {"role": "user", "content": "Tell me a joke"}
    ]
  }'
```

### 5. Responses API - With Native Tools (xAI Executes)

**Important:** These tools are **executed by xAI** on their servers:

```bash
curl -X POST "http://localhost:8000/api/v1/responses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "input": [
      {"role": "user", "content": "What was the score of the latest Arsenal match?"}
    ],
    "tools": [
      {"type": "web_search"}
    ]
  }'
```

**What happens:**
1. Request forwarded to xAI Responses API
2. xAI's model uses web_search tool autonomously
3. xAI searches the web on their servers
4. Returns answer with citations

### 6. Image Generation

```bash
curl -X POST "http://localhost:8000/api/v1/images/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "model": "grok-2-image"
  }'
```

### 7. Vision Analysis

```bash
curl -X POST "http://localhost:8000/api/v1/vision/analyze" \
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

## Testing with API Authentication Enabled

If `XAI_API_AUTH=true`:

### Using Authorization Header (Default)

```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_AUTH_TOKEN" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Using Custom Header (For Dual Auth with Traefik)

If `XAI_API_AUTH_HEADER=X-API-Token`:

```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -u "admin:traefik_password" \                    # Traefik BasicAuth
  -H "X-API-Token: $XAI_API_AUTH_TOKEN" \          # App-level token
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

## Understanding Tool Calling Modes

### Two Types of Tools:

#### 1. Client-Side Function Calling (Chat Completions)
**Endpoint:** `/api/v1/chat/completions`
**Control:** `XAI_TOOLS_ENABLED=true`
**Execution:** Your client application executes tools

**Flow:**
```
Your App → Proxy (validates) → xAI API
                                  ↓
                            Returns: "call get_weather(SF)"
                                  ↓
Your App → Execute get_weather() → Get: "72°F sunny"
         ↓
Your App → Proxy → xAI API with function result
                      ↓
                Returns: "It's 72°F and sunny in SF"
```

**Use Case:** Custom tools specific to your application (database queries, internal APIs, etc.)

#### 2. Native Agentic Tools (Responses API)
**Endpoint:** `/api/v1/responses`  
**Control:** `XAI_NATIVE_TOOLS_ENABLED=true`
**Execution:** xAI executes tools on their servers

**Flow:**
```
Your App → Proxy → xAI Responses API
                      ↓
                xAI executes web_search internally
                      ↓
                Returns: Answer with citations
                      ↓
Your App ← Proxy ← Complete response
```

**Available Tools:**
- `web_search` - Search the web
- `x_search` - Search X (Twitter)
- `code_execution` - Execute Python code

**Use Case:** Real-time information, calculations, web/X research

### Example: AI Assistant Using This Proxy

If you have an AI assistant app with built-in tools:

**Scenario:** Your AI assistant has a `get_user_data()` tool

```javascript
// Your AI Assistant App
const tools = [
  {
    type: "function",
    function: {
      name: "get_user_data",
      description: "Get user data from database",
      parameters: {
        type: "object",
        properties: {
          user_id: { type: "string" }
        }
      }
    }
  }
];

// Send to proxy
const response = await fetch('http://localhost:8000/api/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${XAI_API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'grok-4-1-fast-non-reasoning',
    messages: [{ role: 'user', content: 'Get data for user 123' }],
    tools: tools  // Proxy validates and forwards
  })
});

const data = await response.json();

// If model wants to call tool
if (data.choices[0].message.tool_calls) {
  const toolCall = data.choices[0].message.tool_calls[0];
  
  // YOUR app executes the function
  const userData = await getUserData(toolCall.function.arguments.user_id);
  
  // Send result back through proxy
  const finalResponse = await fetch('...', {
    body: JSON.stringify({
      messages: [
        ...previousMessages,
        data.choices[0].message,  // Assistant's tool call
        {
          role: 'tool',
          tool_call_id: toolCall.id,
          content: JSON.stringify(userData)
        }
      ]
    })
  });
}
```

**Why this works:**
- ✅ Proxy validates tool definition (security)
- ✅ xAI API sees your tools and can request them
- ✅ Your app executes the actual function
- ✅ No errors when proxying through to xAI

**Without tool support**, your AI assistant's tool definitions would be rejected or cause errors.

## Security Tests

### 1. Test Tool Validation (If XAI_TOOLS_ENABLED=true)

Try a dangerous function name (should be rejected):

```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Test"}],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "exec_shell_command",
          "description": "Execute shell command",
          "parameters": {"type": "object", "properties": {}}
        }
      }
    ]
  }'
```

Expected: `400 Bad Request` with validation error

### 2. Test Tools Disabled (If XAI_TOOLS_ENABLED=false)

```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Test"}],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "safe_function",
          "description": "A safe function",
          "parameters": {"type": "object", "properties": {}}
        }
      }
    ]
  }'
```

Expected: `403 Forbidden` - "Tool calling is disabled on this server"

### 3. Test Rate Limiting

```bash
for i in {1..110}; do
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health
  sleep 0.01
done
```

Expected: First 100 succeed, then `429 Too Many Requests`

### 4. Test Documentation Access

```bash
# If XAI_API_AUTH_EXCLUDE_DOCS=true (default)
curl http://localhost:8000/docs
# Expected: 200 OK (Swagger UI HTML)

# If XAI_API_AUTH_EXCLUDE_DOCS=false
curl http://localhost:8000/docs
# Expected: 401 Unauthorized
```

## Using Python OpenAI SDK

```python
from openai import OpenAI

# For API proxy without auth
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="http://localhost:8000/api/v1"
)

# For API proxy with auth
client = OpenAI(
    api_key=os.getenv("XAI_API_AUTH_TOKEN"),  # Use auth token
    base_url="http://localhost:8000/api/v1"
)

# Test chat with tools (proxy validates, xAI sees them)
response = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",
    messages=[
        {"role": "user", "content": "What's the weather?"}
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    }
                }
            }
        }
    ]
)

# Check if model wants to call tool
if response.choices[0].message.tool_calls:
    print("Model wants to call:", response.choices[0].message.tool_calls)
    # YOU execute the function and send result back
```

## Troubleshooting

### "Connection refused"
```bash
docker-compose -f docker/docker-compose.yaml ps
# Make sure containers are running
```

### "Tool calling is disabled"
```bash
# Check .env
grep XAI_TOOLS_ENABLED .env

# Should be: XAI_TOOLS_ENABLED=true
# Restart: docker-compose restart
```

### "Invalid API token"
```bash
# Check auth is configured correctly
grep XAI_API_AUTH .env
grep XAI_API_AUTH_TOKEN .env

# Or disable: XAI_API_AUTH=false
```

### Check logs
```bash
docker logs xai-api
docker logs xai-nginx  # If using nginx
```

## Summary

This proxy supports **two tool paradigms**:

1. **Validation Proxy** (Chat Completions + `XAI_TOOLS_ENABLED`)
   - Validates tool definitions for security
   - Forwards to xAI API
   - Your app executes tools
   
2. **Native Tools** (Responses API + `XAI_NATIVE_TOOLS_ENABLED`)
   - xAI executes tools on their servers
   - web_search, x_search, code_execution
   - Fully autonomous

Both modes work through the proxy without errors when properly configured! ✅
