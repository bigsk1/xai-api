#!/usr/bin/env python
"""Generate updated OpenAPI schema."""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.openapi.utils import get_openapi
from app.main import app

# Create the OpenAPI schema
schema = get_openapi(
    title=app.title,
    version=app.version,
    openapi_version=app.openapi_version,
    description=app.description,
    routes=app.routes,
)

# Add missing request body schema for chat completions
if "/api/v1/chat/completions" in schema["paths"]:
    chat_path = schema["paths"]["/api/v1/chat/completions"]["post"]
    if "requestBody" not in chat_path:
        chat_path["requestBody"] = {
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ChatCompletionRequest"}
                }
            },
            "required": True
        }

# Update the detailed structure of ChatCompletionResponse choices
if "ChatCompletionResponse" in schema["components"]["schemas"]:
    choices_schema = schema["components"]["schemas"]["ChatCompletionResponse"]["properties"]["choices"]
    if "items" in choices_schema and "additionalProperties" in choices_schema["items"]:
        # Update with more specific structure
        choices_schema["items"] = {
            "$ref": "#/components/schemas/ChatCompletionResponseChoice"
        }

# Write the schema to a file
with open("openapi.json", "w") as f:
    json.dump(schema, f, indent=2)

print("OpenAPI schema generated successfully!")