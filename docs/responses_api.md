# xAI Responses API Guide

This guide explains how to use xAI's new **Responses API** with native agentic tools that execute on xAI's servers.

## Table of Contents

- [Overview](#overview)
- [Responses API vs Chat Completions API](#responses-api-vs-chat-completions-api)
- [Enabling the Responses API](#enabling-the-responses-api)
- [Native Agentic Tools](#native-agentic-tools)
- [Request Format](#request-format)
- [Response Format](#response-format)
- [Stateful Conversations](#stateful-conversations)
- [Complete Examples](#complete-examples)
- [Streaming Responses](#streaming-responses)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The xAI Responses API is the **recommended** way to interact with Grok models. It provides:

- **Native Agentic Tools**: xAI executes tools (web search, X search, code execution) on their servers
- **Server-side Storage**: Conversations stored for 30 days with automatic caching
- **Stateful Conversations**: Use `previous_response_id` instead of resending full history
- **Citations**: Automatic citations from web and X searches
- **Billing Optimization**: Cached conversation history reduces token costs
- **Future-proof**: All new xAI features will be delivered here first

## Responses API vs Chat Completions API

This server now provides **BOTH** APIs for different use cases:

| Feature | `/api/v1/chat/completions` | `/api/v1/responses` |
|---------|---------------------------|---------------------|
| **Purpose** | Legacy chat + client-side function calling | Modern agentic tools API |
| **Tool Execution** | YOU execute functions on this server | xAI executes tools on their servers |
| **Tools Available** | Custom functions you define | web_search, x_search, code_execution |
| **State Management** | Stateless (send full history) | Stateful (use previous_response_id) |
| **Caching** | No automatic caching | Automatic conversation caching |
| **Control Flag** | `XAI_TOOLS_ENABLED` | `XAI_NATIVE_TOOLS_ENABLED` |
| **Citations** | No | Yes (from searches) |
| **Billing** | Full history billed each time | Cached history saves tokens |

### When to Use Each

**Use Chat Completions** (`/api/v1/chat/completions`) when:
- You need to execute custom functions on your server
- You want full control over tool execution
- You're integrating with existing OpenAI-compatible code
- You need client-side function calling

**Use Responses API** (`/api/v1/responses`) when:
- You want Grok to autonomously search the web or X
- You need Grok to execute Python code
- You want automatic conversation caching
- You need citations from searches
- You want the latest xAI features

## Enabling the Responses API

Set this environment variable in your `.env` file:

```bash
XAI_NATIVE_TOOLS_ENABLED=true
```

This enables xAI's native agentic tools (web_search, x_search, code_execution). Without this flag, the Responses API endpoint will return a 403 error if tools are requested.

## Native Agentic Tools

xAI provides three server-side tools that execute on their infrastructure:

### 1. Web Search (`web_search`)

Searches the web in real-time and returns relevant information with citations.

```json
{
  "type": "web_search"
}
```

**Use cases:**
- Current events and news
- Factual information that may have changed
- Real-time data (weather, stock prices, sports scores)

### 2. X Search (`x_search`)

Searches X (formerly Twitter) for posts and conversations.

```json
{
  "type": "x_search"
}
```

**Use cases:**
- X user activity and posts
- Trending topics on X
- Social media sentiment
- Recent discussions

### 3. Code Execution (`code_execution`)

Executes Python code in a sandboxed environment on xAI's servers.

```json
{
  "type": "code_execution"
}
```

**Use cases:**
- Mathematical calculations
- Data analysis
- Algorithm implementation
- Generating visualizations

## Request Format

### Basic Request Structure

```json
{
  "model": "grok-4-fast",
  "input": [
    {
      "role": "user",
      "content": "What was Arsenal's most recent game result?"
    }
  ],
  "tools": [
    {"type": "web_search"}
  ]
}
```

### Key Differences from Chat Completions

| Chat Completions | Responses API |
|-----------------|---------------|
| `messages` | `input` |
| `max_tokens` | `max_output_tokens` |
| Resend full history | Use `previous_response_id` |
| No `store` parameter | `store: true` (default) |

### Full Request Parameters

```json
{
  "model": "grok-4-fast",
  "input": [
    {
      "role": "user",
      "content": "Your query here"
    }
  ],
  "tools": [
    {"type": "web_search"},
    {"type": "x_search"},
    {"type": "code_execution"}
  ],
  "max_output_tokens": 1024,
  "temperature": 0.7,
  "top_p": 1.0,
  "stream": false,
  "store": true,
  "previous_response_id": null,
  "include": [
    "code_execution_call_output",
    "verbose_streaming"
  ]
}
```

### Parameters Explained

- **model**: Model to use (`grok-4`, `grok-4-fast`, `grok-3`, etc.)
- **input**: Array of messages (uses `input` instead of `messages`)
- **tools**: Array of tool definitions (server-side or client-side)
- **max_output_tokens**: Maximum tokens to generate (replaces `max_tokens`)
- **temperature**: Sampling temperature (0.0 to 2.0)
- **top_p**: Nucleus sampling parameter
- **stream**: Enable streaming responses
- **store**: Store conversation server-side for 30 days (default: `true`)
- **previous_response_id**: ID from previous response to continue conversation
- **include**: Additional data to include in response:
  - `code_execution_call_output`: Include output from code execution
  - `verbose_streaming`: More detailed streaming information
  - `reasoning.encrypted_content`: Include encrypted reasoning content

## Response Format

### Non-Streaming Response

```json
{
  "id": "resp-abc123",
  "object": "response",
  "created": 1700000000,
  "model": "grok-4-fast",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {
          "type": "output_text",
          "text": "Arsenal won their recent match 2-1 against Manchester United..."
        }
      ],
      "tool_calls": [
        {
          "id": "call_xyz",
          "type": "function",
          "function": {
            "name": "web_search",
            "arguments": "{\"query\": \"Arsenal recent match result\"}"
          }
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 50,
    "output_tokens": 120,
    "total_tokens": 170,
    "reasoning_tokens": 0,
    "cached_tokens": 0
  },
  "server_side_tool_usage": {
    "web_search_calls": 1,
    "x_search_calls": 0,
    "code_execution_calls": 0
  },
  "citations": [
    {
      "url": "https://example.com/arsenal-match",
      "title": "Arsenal Match Report",
      "snippet": "Arsenal secured a 2-1 victory...",
      "source": "web"
    }
  ],
  "finish_reason": "stop"
}
```

### Key Response Fields

- **id**: Response ID (save this for `previous_response_id`)
- **output**: Array of output messages with typed content
- **usage**: Token usage metrics
- **server_side_tool_usage**: Count of each tool type used
- **citations**: Citations from web/X searches with URLs and snippets
- **finish_reason**: Why generation stopped (`stop`, `length`, `tool_calls`)

## Stateful Conversations

One of the biggest advantages of the Responses API is stateful conversations using `previous_response_id`.

### Traditional Way (Chat Completions)

```json
{
  "messages": [
    {"role": "user", "content": "What is 2+2?"},
    {"role": "assistant", "content": "4"},
    {"role": "user", "content": "Multiply that by 10"}
  ]
}
```

You must resend the entire conversation history every time.

### Modern Way (Responses API)

**First Request:**
```json
{
  "model": "grok-4-fast",
  "input": [
    {"role": "user", "content": "What is 2+2?"}
  ],
  "store": true
}
```

**Response:**
```json
{
  "id": "resp-abc123",
  "output": [...]
}
```

**Follow-up Request:**
```json
{
  "model": "grok-4-fast",
  "previous_response_id": "resp-abc123",
  "input": [
    {"role": "user", "content": "Multiply that by 10"}
  ],
  "store": true
}
```

xAI's servers maintain the conversation history automatically!

## Complete Examples

### Example 1: Web Search for Current Information

```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-fast",
    "input": [
      {
        "role": "user",
        "content": "What was the result of Arsenal'\''s most recent game?"
      }
    ],
    "tools": [
      {"type": "web_search"}
    ]
  }'
```

**Response includes:**
- Game result
- Citations with URLs to match reports
- Tool usage metrics

### Example 2: X Search for User Activity

```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-fast",
    "input": [
      {
        "role": "user",
        "content": "What has Elon Musk posted about recently on X?"
      }
    ],
    "tools": [
      {"type": "x_search"}
    ]
  }'
```

### Example 3: Code Execution for Calculations

```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-fast",
    "input": [
      {
        "role": "user",
        "content": "What is the 100th number in the Fibonacci sequence? Show me the code."
      }
    ],
    "tools": [
      {"type": "code_execution"}
    ],
    "include": ["code_execution_call_output"]
  }'
```

### Example 4: Multiple Tools

```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-fast",
    "input": [
      {
        "role": "user",
        "content": "Search X for recent posts about AI, then calculate the average engagement rate if I give you the numbers"
      }
    ],
    "tools": [
      {"type": "x_search"},
      {"type": "code_execution"}
    ],
    "include": ["code_execution_call_output"]
  }'
```

### Example 5: Continuing a Conversation

**First message:**
```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-fast",
    "input": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ],
    "store": true
  }'
```

Save the `id` from the response (e.g., `resp-abc123`).

**Follow-up message:**
```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-fast",
    "previous_response_id": "resp-abc123",
    "input": [
      {
        "role": "user",
        "content": "What is the population of that city?"
      }
    ],
    "store": true
  }'
```

Grok knows "that city" refers to Paris!

### Example 6: Python with Requests

```python
import requests
import json

API_BASE = "http://localhost:8000/api/v1"
XAI_API_KEY = "your_xai_api_key"

def create_response(input_messages, tools=None, previous_id=None):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {XAI_API_KEY}"
    }
    
    data = {
        "model": "grok-4-fast",
        "input": input_messages,
        "store": True
    }
    
    if tools:
        data["tools"] = tools
    
    if previous_id:
        data["previous_response_id"] = previous_id
    
    response = requests.post(
        f"{API_BASE}/responses",
        headers=headers,
        json=data
    )
    
    return response.json()

# Example: Web search
result = create_response(
    input_messages=[
        {"role": "user", "content": "What's the latest news about SpaceX?"}
    ],
    tools=[{"type": "web_search"}]
)

print("Response:", result["output"][0]["content"][0]["text"])
print("Citations:", result.get("citations", []))
print("Web searches:", result.get("server_side_tool_usage", {}).get("web_search_calls", 0))

# Continue conversation
response_id = result["id"]
result2 = create_response(
    input_messages=[
        {"role": "user", "content": "Tell me more about the most recent launch"}
    ],
    tools=[{"type": "web_search"}],
    previous_id=response_id
)

print("Follow-up:", result2["output"][0]["content"][0]["text"])
```

## Streaming Responses

Enable real-time streaming for better UX:

```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-4-fast",
    "input": [
      {"role": "user", "content": "Write a short story about AI"}
    ],
    "stream": true
  }'
```

The response is streamed as Server-Sent Events (SSE):

```
data: {"id":"resp-abc","object":"response.chunk","created":1700000000,"model":"grok-4-fast","output":[...]}

data: {"id":"resp-abc","object":"response.chunk","created":1700000000,"model":"grok-4-fast","output":[...]}

data: [DONE]
```

## Best Practices

### 1. Use Appropriate Models

- **grok-4**: Most capable, best for complex reasoning
- **grok-4-fast**: Faster responses, great for most use cases
- **grok-3**: Previous generation, still powerful

### 2. Enable Server-side Storage

```json
{
  "store": true
}
```

Always enable `store` unless you have privacy concerns. This:
- Enables `previous_response_id` for follow-ups
- Reduces token costs through caching
- Improves response times

### 3. Use Appropriate Tools

Only include tools the model might actually need:

```json
// Good: User might need current info
{
  "input": [{"role": "user", "content": "What's the weather?"}],
  "tools": [{"type": "web_search"}]
}

// Bad: User doesn't need web search for this
{
  "input": [{"role": "user", "content": "What is 2+2?"}],
  "tools": [{"type": "web_search"}]
}
```

### 4. Handle Citations

Always display citations when provided:

```python
if "citations" in response:
    print("\n\nSources:")
    for citation in response["citations"]:
        print(f"- {citation['title']}: {citation['url']}")
```

### 5. Monitor Tool Usage

Track server-side tool usage for billing:

```python
tool_usage = response.get("server_side_tool_usage", {})
print(f"Web searches: {tool_usage.get('web_search_calls', 0)}")
print(f"X searches: {tool_usage.get('x_search_calls', 0)}")
print(f"Code executions: {tool_usage.get('code_execution_calls', 0)}")
```

### 6. Error Handling

```python
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 403:
        print("Native tools are disabled. Set XAI_NATIVE_TOOLS_ENABLED=true")
    elif e.response.status_code == 400:
        print("Invalid request:", e.response.json())
    else:
        print(f"HTTP error: {e}")
```

## Troubleshooting

### 403 Forbidden - Tools Disabled

```json
{
  "detail": "Native agentic tools are disabled on this server. Set XAI_NATIVE_TOOLS_ENABLED=true to enable."
}
```

**Solution**: Set `XAI_NATIVE_TOOLS_ENABLED=true` in `.env` and restart the server.

### 400 Bad Request - Missing Required Field

```json
{
  "detail": "Input field is required for Responses API (use 'input' instead of 'messages')"
}
```

**Solution**: Use `input` instead of `messages` in your request.

### No Citations Returned

If you're not getting citations when expected:
- Ensure you're using `web_search` or `x_search` tools
- Check that the query actually required a search
- Verify the model found relevant results

### Previous Response ID Not Working

```json
{
  "detail": "Invalid previous_response_id"
}
```

**Possible causes:**
- Response ID expired (30 day limit)
- Wrong response ID format
- `store: false` was used in the original request

## See Also

- [Function Calling Guide](./function_calling.md) - For client-side function calling
- [API Examples](./examples.md) - General API usage
- [Streaming Guide](./streaming.md) - Streaming responses
- [xAI Responses API Docs](https://docs.x.ai/docs/guides/chat) - Official xAI documentation
