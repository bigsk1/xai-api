# Function Calling (Tool Calling) Guide

This guide explains how to use function calling (also known as tool calling) with the xAI API. Function calling allows the model to intelligently decide when to call external functions to help answer user queries.

## Table of Contents

- [Overview](#overview)
- [Enabling Function Calling](#enabling-function-calling)
- [Security Considerations](#security-considerations)
- [Basic Concepts](#basic-concepts)
- [Request Format](#request-format)
- [Response Format](#response-format)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)
- [Limitations](#limitations)

## Overview

Function calling enables the model to:
- Recognize when a function should be called based on user input
- Generate properly formatted JSON to call functions
- Incorporate function results into the conversation

This is particularly useful for:
- Retrieving real-time data (weather, stock prices, etc.)
- Performing calculations
- Querying databases
- Executing external actions

## Enabling Function Calling

Function calling is **disabled by default** for security reasons. To enable it, set the environment variable:

```bash
XAI_TOOLS_ENABLED=true
```

When disabled, any requests containing `tools` or `tool_choice` parameters will receive a 403 Forbidden error.

## Security Considerations

When exposing this API publicly with function calling enabled, be aware:

1. **Validation**: The API automatically validates all tool definitions for security issues
2. **Dangerous Patterns**: Function names and descriptions are checked for potentially dangerous patterns (exec, eval, file operations, etc.)
3. **Rate Limiting**: Consider implementing stricter rate limits for tool-enabled requests
4. **Tool Execution**: The API only returns tool call requests - **you are responsible for executing them securely**
5. **Input Sanitization**: Always sanitize function arguments before executing them

### Validation Rules

The API enforces these security constraints:

- Maximum 20 tools per request
- Function names: max 64 characters, alphanumeric + underscore/hyphen only
- Function descriptions: max 1024 characters
- Parameter schemas: max 5 levels of nesting
- No duplicate function names
- Blocks dangerous patterns in function names

## Basic Concepts

### Tool Definition

A tool consists of:
- **type**: Always "function" (currently the only supported type)
- **function**: Object containing:
  - **name**: Unique identifier for the function
  - **description**: Clear explanation of what the function does
  - **parameters**: JSON Schema describing the function's parameters

### Tool Choice

Controls which tool the model can use:
- `"none"`: Model won't call any functions
- `"auto"`: Model decides whether to call a function (default)
- `"required"`: Model must call at least one function
- `{"type": "function", "function": {"name": "function_name"}}`: Force a specific function

## Request Format

### Basic Chat Completion with Tools

```json
{
  "model": "grok-beta",
  "messages": [
    {
      "role": "user",
      "content": "What's the weather like in San Francisco?"
    }
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
              "description": "The city and state, e.g., San Francisco, CA"
            },
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"],
              "description": "The temperature unit"
            }
          },
          "required": ["location"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

### Parameter Schema Format

Parameters follow JSON Schema specification:

```json
{
  "type": "object",
  "properties": {
    "string_param": {
      "type": "string",
      "description": "A string parameter"
    },
    "number_param": {
      "type": "number",
      "description": "A numeric parameter",
      "minimum": 0,
      "maximum": 100
    },
    "enum_param": {
      "type": "string",
      "enum": ["option1", "option2", "option3"],
      "description": "A parameter with predefined values"
    },
    "array_param": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "An array of strings"
    },
    "nested_object": {
      "type": "object",
      "properties": {
        "nested_field": {
          "type": "string"
        }
      }
    }
  },
  "required": ["string_param", "number_param"]
}
```

## Response Format

### When Model Calls a Function

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "grok-beta",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\": \"San Francisco, CA\", \"unit\": \"fahrenheit\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

### When Model Responds Normally

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "grok-beta",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I'd be happy to help you with that!"
      },
      "finish_reason": "stop"
    }
  ]
}
```

## Complete Examples

### Example 1: Weather Query

#### Step 1: Initial Request with Tool Definition

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-beta",
    "messages": [
      {"role": "user", "content": "What is the weather in New York?"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_current_weather",
          "description": "Get the current weather in a given location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "The city and state, e.g., San Francisco, CA"
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

#### Step 2: Model Response (Tool Call)

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_xyz789",
            "type": "function",
            "function": {
              "name": "get_current_weather",
              "arguments": "{\"location\": \"New York, NY\", \"unit\": \"fahrenheit\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

#### Step 3: Execute Function (Your Application)

```python
import json

# Parse the function call
function_name = response["choices"][0]["message"]["tool_calls"][0]["function"]["name"]
function_args = json.loads(response["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"])

# Execute the function (example)
def get_current_weather(location, unit="fahrenheit"):
    # Your implementation here
    return {
        "location": location,
        "temperature": 72,
        "unit": unit,
        "conditions": "Sunny"
    }

# Get the result
function_result = get_current_weather(**function_args)
```

#### Step 4: Send Function Result Back to Model

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-beta",
    "messages": [
      {"role": "user", "content": "What is the weather in New York?"},
      {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_xyz789",
            "type": "function",
            "function": {
              "name": "get_current_weather",
              "arguments": "{\"location\": \"New York, NY\", \"unit\": \"fahrenheit\"}"
            }
          }
        ]
      },
      {
        "role": "tool",
        "tool_call_id": "call_xyz789",
        "content": "{\"location\": \"New York, NY\", \"temperature\": 72, \"unit\": \"fahrenheit\", \"conditions\": \"Sunny\"}"
      }
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_current_weather",
          "description": "Get the current weather in a given location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {"type": "string"},
              "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
          }
        }
      }
    ]
  }'
```

#### Step 5: Final Model Response

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "The weather in New York is currently sunny with a temperature of 72°F."
      },
      "finish_reason": "stop"
    }
  ]
}
```

### Example 2: Multiple Tools

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_XAI_API_KEY" \
  -d '{
    "model": "grok-beta",
    "messages": [
      {"role": "user", "content": "What is the weather in Paris and what time is it there?"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "get_weather",
          "description": "Get current weather for a location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {"type": "string"}
            },
            "required": ["location"]
          }
        }
      },
      {
        "type": "function",
        "function": {
          "name": "get_current_time",
          "description": "Get current time for a location",
          "parameters": {
            "type": "object",
            "properties": {
              "location": {"type": "string"}
            },
            "required": ["location"]
          }
        }
      }
    ]
  }'
```

### Example 3: Using Python with OpenAI SDK

```python
import os
import json
from openai import OpenAI

# Initialize client
client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="http://localhost:8000/api/v1"
)

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather in a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state, e.g., San Francisco, CA"
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

# Make initial request
response = client.chat.completions.create(
    model="grok-beta",
    messages=[
        {"role": "user", "content": "What's the weather in Boston?"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Check if model wants to call a function
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    
    # Execute function
    if tool_call.function.name == "get_weather":
        args = json.loads(tool_call.function.arguments)
        weather_data = get_weather(**args)  # Your function implementation
        
        # Send function result back
        second_response = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "user", "content": "What's the weather in Boston?"},
                response.choices[0].message,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(weather_data)
                }
            ],
            tools=tools
        )
        
        print(second_response.choices[0].message.content)
else:
    print(response.choices[0].message.content)
```

## Best Practices

### 1. Clear Function Descriptions

```json
{
  "name": "get_weather",
  "description": "Get the current weather conditions including temperature, humidity, and precipitation for a specific city. Use this when users ask about current weather, temperature, or weather conditions.",
  "parameters": { ... }
}
```

### 2. Detailed Parameter Descriptions

```json
{
  "properties": {
    "location": {
      "type": "string",
      "description": "The city and state in the format 'City, State' or 'City, Country'. Examples: 'New York, NY', 'London, UK'"
    },
    "unit": {
      "type": "string",
      "enum": ["celsius", "fahrenheit"],
      "description": "The temperature unit to use in the response. Defaults to fahrenheit."
    }
  }
}
```

### 3. Handle Errors Gracefully

```python
try:
    result = execute_function(function_name, function_args)
except Exception as e:
    # Return error as tool response
    error_response = {
        "error": str(e),
        "message": "Failed to execute function"
    }
    # Send error back to model so it can inform the user
```

### 4. Validate Function Arguments

```python
import json
from jsonschema import validate, ValidationError

def execute_tool_call(tool_call, function_schema):
    try:
        # Parse arguments
        args = json.loads(tool_call.function.arguments)
        
        # Validate against schema
        validate(instance=args, schema=function_schema["parameters"])
        
        # Execute function
        return your_function(**args)
    except ValidationError as e:
        return {"error": f"Invalid arguments: {e.message}"}
    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}
```

### 5. Use Enums for Limited Options

```json
{
  "action": {
    "type": "string",
    "enum": ["start", "stop", "restart", "status"],
    "description": "The action to perform on the service"
  }
}
```

## Limitations

1. **Streaming Not Fully Supported**: Tool calls work best with non-streaming requests
2. **Single Model Round**: The model makes one decision per request - implement your own loop for multi-step reasoning
3. **No Automatic Execution**: You must implement function execution and send results back
4. **xAI API Limits**: Check xAI's documentation for model-specific limitations on tool calling
5. **Maximum Complexity**: Parameter schemas are limited to 5 levels of nesting for security

## Troubleshooting

### 403 Forbidden Error

```json
{
  "detail": "Tool calling is disabled on this server. Set XAI_TOOLS_ENABLED=true to enable."
}
```

**Solution**: Set `XAI_TOOLS_ENABLED=true` in your `.env` file and restart the server.

### 400 Bad Request - Validation Error

```json
{
  "detail": "Tool validation failed: Function name can only contain alphanumeric characters, underscores, and hyphens"
}
```

**Solution**: Ensure function names follow the naming rules (alphanumeric, underscore, hyphen only).

### 400 Bad Request - Dangerous Pattern

```json
{
  "detail": "Tool validation failed: Function name contains potentially dangerous pattern"
}
```

**Solution**: Avoid patterns like "exec", "eval", "system", "shell" in function names and descriptions.

### Model Not Calling Functions

**Possible causes:**
1. Description is too vague or unclear
2. User query doesn't match the function's purpose
3. `tool_choice` is set to "none"
4. Function parameters are too complex

**Solution**: Improve function descriptions, add examples, simplify parameter schemas.

## See Also

- [API Examples](./examples.md) - General API usage examples
- [Streaming API](./streaming.md) - Streaming responses guide
- [xAI API Comparison](https://docs.x.ai/docs/guides/chat/comparison) - Differences between xAI APIs
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling) - Similar concepts
