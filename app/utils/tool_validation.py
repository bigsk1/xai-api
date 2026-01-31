"""
Security validation for tool/function calling.

This module provides validation logic to ensure tool definitions are safe
when the API is exposed publicly. It prevents potentially dangerous operations
and ensures proper formatting.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from app.models.schemas import Tool
from app.core.config import settings

logger = logging.getLogger(__name__)

# Maximum limits for security (loaded from settings)
MAX_TOOLS_PER_REQUEST = settings.MAX_TOOLS_PER_REQUEST
MAX_FUNCTION_NAME_LENGTH = settings.MAX_FUNCTION_NAME_LENGTH
MAX_FUNCTION_DESCRIPTION_LENGTH = settings.MAX_FUNCTION_DESCRIPTION_LENGTH
MAX_PARAMETER_DEPTH = settings.MAX_PARAMETER_DEPTH

# Disallowed patterns in function names and descriptions (case-insensitive)
DANGEROUS_PATTERNS = [
    r'\bexec\b', r'\beval\b', r'\b__import__\b', r'\bcompile\b',
    r'\bos\.', r'\bsys\.', r'\bsubprocess\b', r'\bshell\b',
    r'\bfile\b.*\bopen\b', r'\bwrite\b.*\bfile\b',
    r'\bdelete\b.*\bfile\b', r'\brm\b', r'\bunlink\b'
]


class ToolValidationError(Exception):
    """Raised when tool validation fails."""
    pass


def validate_function_name(name: str) -> None:
    """
    Validate function name for security and format.
    
    Args:
        name: Function name to validate
        
    Raises:
        ToolValidationError: If validation fails
    """
    if not name:
        raise ToolValidationError("Function name cannot be empty")
    
    if len(name) > MAX_FUNCTION_NAME_LENGTH:
        raise ToolValidationError(
            f"Function name exceeds maximum length of {MAX_FUNCTION_NAME_LENGTH} characters"
        )
    
    # Function name should only contain alphanumeric characters, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        raise ToolValidationError(
            "Function name can only contain alphanumeric characters, underscores, and hyphens"
        )
    
    # Check for dangerous patterns
    name_lower = name.lower()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, name_lower):
            raise ToolValidationError(
                f"Function name contains potentially dangerous pattern: {pattern}"
            )


def validate_function_description(description: str) -> None:
    """
    Validate function description for security and format.
    
    Args:
        description: Function description to validate
        
    Raises:
        ToolValidationError: If validation fails
    """
    if not description:
        raise ToolValidationError("Function description cannot be empty")
    
    if len(description) > MAX_FUNCTION_DESCRIPTION_LENGTH:
        raise ToolValidationError(
            f"Function description exceeds maximum length of {MAX_FUNCTION_DESCRIPTION_LENGTH} characters"
        )
    
    # Check for dangerous patterns in description (more lenient than name)
    description_lower = description.lower()
    suspicious_patterns = [
        r'\bexec\b.*\bcode\b', r'\beval\b.*\bexpression\b',
        r'\bshell\b.*\bcommand\b', r'\bdelete\b.*\bsystem\b'
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, description_lower):
            logger.warning(f"Function description contains suspicious pattern: {pattern}")


def validate_parameter_schema(schema: Dict[str, Any], depth: int = 0) -> None:
    """
    Validate parameter schema for security.
    
    Args:
        schema: JSON Schema object for parameters
        depth: Current nesting depth
        
    Raises:
        ToolValidationError: If validation fails
    """
    if depth > MAX_PARAMETER_DEPTH:
        raise ToolValidationError(
            f"Parameter schema exceeds maximum nesting depth of {MAX_PARAMETER_DEPTH}"
        )
    
    if not isinstance(schema, dict):
        raise ToolValidationError("Parameter schema must be a dictionary")
    
    # Validate type field
    if "type" in schema and schema["type"] not in ["object", "string", "number", "integer", "boolean", "array", "null"]:
        raise ToolValidationError(f"Invalid parameter type: {schema['type']}")
    
    # Recursively validate nested properties
    if "properties" in schema:
        if not isinstance(schema["properties"], dict):
            raise ToolValidationError("Parameter 'properties' must be a dictionary")
        
        for prop_name, prop_schema in schema["properties"].items():
            if isinstance(prop_schema, dict):
                validate_parameter_schema(prop_schema, depth + 1)
    
    # Validate array items
    if "items" in schema:
        if isinstance(schema["items"], dict):
            validate_parameter_schema(schema["items"], depth + 1)


def validate_tool(tool: Tool) -> None:
    """
    Validate a single tool definition for security.
    
    Args:
        tool: Tool object to validate
        
    Raises:
        ToolValidationError: If validation fails
    """
    # Validate tool type
    if tool.type != "function":
        raise ToolValidationError(f"Unsupported tool type: {tool.type}. Only 'function' is supported")
    
    # Validate function definition
    validate_function_name(tool.function.name)
    validate_function_description(tool.function.description)
    
    # Validate parameters
    params_dict = tool.function.parameters.model_dump()
    validate_parameter_schema(params_dict)


def validate_tools(tools: Optional[List[Tool]]) -> None:
    """
    Validate a list of tools for security.
    
    Args:
        tools: List of Tool objects to validate
        
    Raises:
        ToolValidationError: If validation fails
    """
    if tools is None:
        return
    
    if not isinstance(tools, list):
        raise ToolValidationError("Tools must be a list")
    
    if len(tools) == 0:
        raise ToolValidationError("Tools list cannot be empty if provided")
    
    if len(tools) > MAX_TOOLS_PER_REQUEST:
        raise ToolValidationError(
            f"Number of tools ({len(tools)}) exceeds maximum allowed ({MAX_TOOLS_PER_REQUEST})"
        )
    
    # Check for duplicate function names
    function_names = set()
    for tool in tools:
        validate_tool(tool)
        
        if tool.function.name in function_names:
            raise ToolValidationError(f"Duplicate function name: {tool.function.name}")
        function_names.add(tool.function.name)
    
    logger.info(f"Successfully validated {len(tools)} tools")


def validate_tool_choice(tool_choice: Optional[Any], tools: Optional[List[Tool]]) -> None:
    """
    Validate tool_choice parameter.
    
    Args:
        tool_choice: Tool choice parameter (string or dict)
        tools: List of available tools
        
    Raises:
        ToolValidationError: If validation fails
    """
    if tool_choice is None:
        return
    
    # If tool_choice is specified but no tools are provided, it's an error
    if tools is None or len(tools) == 0:
        raise ToolValidationError("tool_choice specified but no tools provided")
    
    # Validate string values
    if isinstance(tool_choice, str):
        valid_choices = ["none", "auto", "required"]
        if tool_choice not in valid_choices:
            raise ToolValidationError(
                f"Invalid tool_choice: {tool_choice}. Must be one of {valid_choices}"
            )
    
    # Validate dict (specific tool selection)
    elif isinstance(tool_choice, dict):
        if "type" not in tool_choice or tool_choice["type"] != "function":
            raise ToolValidationError("tool_choice dict must have type='function'")
        
        if "function" not in tool_choice or "name" not in tool_choice["function"]:
            raise ToolValidationError("tool_choice dict must specify function.name")
        
        # Verify the function name exists in the tools list
        function_name = tool_choice["function"]["name"]
        available_names = [tool.function.name for tool in tools]
        if function_name not in available_names:
            raise ToolValidationError(
                f"tool_choice references unknown function: {function_name}"
            )
    else:
        raise ToolValidationError("tool_choice must be a string or dict")
