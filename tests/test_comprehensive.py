#!/usr/bin/env python3
"""
Comprehensive test suite for xAI API before production deployment.
Tests all major functionality to catch any regressions.
"""

import requests
import json
import sys
import os
import time
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Check if API auth is enabled
API_AUTH_ENABLED = os.getenv("XAI_API_AUTH", "false").lower() in ("true", "1", "yes")
API_AUTH_TOKEN = os.getenv("XAI_API_AUTH_TOKEN", "")
API_AUTH_HEADER = os.getenv("XAI_API_AUTH_HEADER", "Authorization")

def get_auth_headers():
    """Get proper auth headers based on configuration"""
    if API_AUTH_ENABLED and API_AUTH_TOKEN:
        # Use API auth token
        if API_AUTH_HEADER == "Authorization":
            return {"Authorization": f"Bearer {API_AUTH_TOKEN}"}
        else:
            return {API_AUTH_HEADER: API_AUTH_TOKEN}
    else:
        # Use XAI API key as Bearer token (for xAI API calls)
        return {"Authorization": f"Bearer {XAI_API_KEY}"}

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_test(name):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def print_info(msg):
    print(f"   {msg}")

# ============================================================================
# HEALTH & DOCS TESTS
# ============================================================================

def test_health():
    """Test health endpoint (always public)"""
    print_test("Health Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print_success("Health endpoint responds correctly")
                print_info(f"Response: {data}")
                return True
            else:
                print_error("Health endpoint returned unexpected data")
                print_info(f"Response: {data}")
                return False
        else:
            print_error(f"Health endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health endpoint error: {str(e)}")
        return False

def test_docs_accessibility():
    """Test if docs endpoint is accessible based on config"""
    print_test("Documentation Endpoints")
    
    auth_enabled = os.getenv("XAI_API_AUTH", "false").lower() in ("true", "1", "yes")
    exclude_docs = os.getenv("XAI_API_AUTH_EXCLUDE_DOCS", "true").lower() in ("true", "1", "yes")
    
    print_info(f"XAI_API_AUTH: {auth_enabled}")
    print_info(f"XAI_API_AUTH_EXCLUDE_DOCS: {exclude_docs}")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        
        if auth_enabled and not exclude_docs:
            # Docs should be protected
            if response.status_code == 401:
                print_success("Docs correctly protected by auth")
                return True
            else:
                print_error(f"Docs should be protected but got {response.status_code}")
                return False
        else:
            # Docs should be accessible
            if response.status_code == 200:
                print_success("Docs accessible as expected")
                return True
            else:
                print_error(f"Docs should be accessible but got {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Docs endpoint error: {str(e)}")
        return False

# ============================================================================
# CHAT COMPLETIONS TESTS
# ============================================================================

def test_chat_completion_basic():
    """Test basic chat completion"""
    print_test("Chat Completions - Basic")
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "grok-4-1-fast-non-reasoning",
                "messages": [{"role": "user", "content": "Say 'test successful' and nothing else"}],
                "max_tokens": 20
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print_success("Basic chat completion works")
            print_info(f"Response: {content}")
            print_info(f"Model: {data.get('model')}")
            print_info(f"Usage: {data.get('usage')}")
            return True
        else:
            print_error(f"Chat completion failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Chat completion error: {str(e)}")
        return False

def test_chat_completion_streaming():
    """Test streaming chat completion"""
    print_test("Chat Completions - Streaming")
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "grok-4-1-fast-non-reasoning",
                "messages": [{"role": "user", "content": "Count from 1 to 5"}],
                "max_tokens": 50,
                "stream": True
            },
            stream=True
        )
        
        if response.status_code == 200:
            chunks = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
                            if content:
                                chunks.append(content)
                        except json.JSONDecodeError:
                            pass
            
            full_response = "".join(chunks)
            print_success(f"Streaming works - received {len(chunks)} chunks")
            print_info(f"Response: {full_response}")
            return True
        else:
            print_error(f"Streaming failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Streaming error: {str(e)}")
        return False

def test_chat_completion_with_tools():
    """Test chat completion with function calling"""
    print_test("Chat Completions - Function Calling")
    
    tools_enabled = os.getenv("XAI_TOOLS_ENABLED", "false").lower() in ("true", "1", "yes")
    
    if not tools_enabled:
        print_warning("XAI_TOOLS_ENABLED is false - skipping function calling test")
        return True
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        # Define a simple test tool
        tools = [
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
                                "description": "The city and state, e.g. San Francisco, CA"
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
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "grok-4-1-fast-non-reasoning",
                "messages": [{"role": "user", "content": "What's the weather in San Francisco?"}],
                "tools": tools,
                "max_tokens": 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            message = data.get("choices", [{}])[0].get("message", {})
            
            # Check if model wants to call function
            if message.get("tool_calls"):
                print_success("Function calling works - model requested tool call")
                print_info(f"Tool calls: {json.dumps(message.get('tool_calls'), indent=2)}")
                return True
            else:
                # Model might not always call the function, but request should succeed
                print_success("Function calling request accepted (model didn't call function)")
                print_info(f"Response: {message.get('content')}")
                return True
        else:
            print_error(f"Function calling failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Function calling error: {str(e)}")
        return False

def test_chat_completion_without_tools_when_disabled():
    """Test that tools are rejected when XAI_TOOLS_ENABLED=false"""
    print_test("Chat Completions - Tools Disabled Check")
    
    tools_enabled = os.getenv("XAI_TOOLS_ENABLED", "false").lower() in ("true", "1", "yes")
    
    if tools_enabled:
        print_warning("XAI_TOOLS_ENABLED is true - skipping disabled tools test")
        return True
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "test_function",
                    "description": "Test function",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "grok-4-1-fast-non-reasoning",
                "messages": [{"role": "user", "content": "Test"}],
                "tools": tools
            }
        )
        
        if response.status_code == 403:
            print_success("Tools correctly rejected when disabled")
            print_info(f"Response: {response.json()}")
            return True
        else:
            print_error(f"Expected 403 but got {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Tools disabled check error: {str(e)}")
        return False

# ============================================================================
# RESPONSES API TESTS
# ============================================================================

def test_responses_basic():
    """Test basic responses API"""
    print_test("Responses API - Basic")
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        response = requests.post(
            f"{BASE_URL}/api/v1/responses",
            headers=headers,
            json={
                "model": "grok-4-1-fast-non-reasoning",
                "input": [{"role": "user", "content": "Say 'responses API working' and nothing else"}]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Basic Responses API works")
            print_info(f"Response ID: {data.get('id')}")
            print_info(f"Model: {data.get('model')}")
            
            # Check output format
            output = data.get("output", [])
            if output:
                print_info(f"Output: {output[0]}")
            
            return True
        else:
            print_error(f"Responses API failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Responses API error: {str(e)}")
        return False

def test_responses_with_web_search():
    """Test responses API with web search tool"""
    print_test("Responses API - Web Search")
    
    native_tools_enabled = os.getenv("XAI_NATIVE_TOOLS_ENABLED", "false").lower() in ("true", "1", "yes")
    
    if not native_tools_enabled:
        print_warning("XAI_NATIVE_TOOLS_ENABLED is false - skipping web search test")
        return True
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        response = requests.post(
            f"{BASE_URL}/api/v1/responses",
            headers=headers,
            json={
                "model": "grok-4-1-fast-non-reasoning",
                "input": [{"role": "user", "content": "What was the score of the latest Arsenal match?"}],
                "tools": [{"type": "web_search"}]
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Web search tool works")
            print_info(f"Response ID: {data.get('id')}")
            
            # Check for web search usage
            output = data.get("output", [])
            has_web_search = any(
                item.get("type") == "web_search_call" or 
                item.get("web_search_call") 
                for item in output
            )
            
            if has_web_search:
                print_success("Web search was used")
            else:
                print_warning("Web search not used (model's choice)")
            
            # Show citations if present
            citations = data.get("citations", [])
            if citations:
                print_info(f"Citations found: {len(citations)}")
            
            return True
        else:
            print_error(f"Web search failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Web search error: {str(e)}")
        return False

def test_responses_retrieve():
    """Test retrieving a stored response"""
    print_test("Responses API - Retrieve")
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        # First create a response
        create_response = requests.post(
            f"{BASE_URL}/api/v1/responses",
            headers=headers,
            json={
                "model": "grok-4-1-fast-non-reasoning",
                "input": [{"role": "user", "content": "Hello"}]
            }
        )
        
        if create_response.status_code != 200:
            print_error("Failed to create response for retrieve test")
            return False
        
        response_id = create_response.json().get("id")
        print_info(f"Created response: {response_id}")
        
        # Now retrieve it
        get_response = requests.get(
            f"{BASE_URL}/api/v1/responses/{response_id}",
            headers=headers
        )
        
        if get_response.status_code == 200:
            data = get_response.json()
            print_success("Response retrieval works")
            print_info(f"Retrieved ID: {data.get('id')}")
            return True
        else:
            print_error(f"Retrieve failed: {get_response.status_code}")
            print_info(f"Response: {get_response.text}")
            return False
    except Exception as e:
        print_error(f"Retrieve error: {str(e)}")
        return False

def test_responses_delete():
    """Test deleting a stored response"""
    print_test("Responses API - Delete")
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        # First create a response
        create_response = requests.post(
            f"{BASE_URL}/api/v1/responses",
            headers=headers,
            json={
                "model": "grok-4-1-fast-non-reasoning",
                "input": [{"role": "user", "content": "Test delete"}]
            }
        )
        
        if create_response.status_code != 200:
            print_error("Failed to create response for delete test")
            return False
        
        response_id = create_response.json().get("id")
        print_info(f"Created response: {response_id}")
        
        # Now delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/v1/responses/{response_id}",
            headers=headers
        )
        
        if delete_response.status_code == 200:
            data = delete_response.json()
            print_success("Response deletion works")
            print_info(f"Deleted: {data.get('deleted')}")
            
            # Verify it's actually deleted
            get_response = requests.get(
                f"{BASE_URL}/api/v1/responses/{response_id}",
                headers=headers
            )
            
            if get_response.status_code == 404:
                print_success("Response confirmed deleted")
                return True
            else:
                print_error("Response still exists after deletion")
                return False
        else:
            print_error(f"Delete failed: {get_response.status_code}")
            print_info(f"Response: {delete_response.text}")
            return False
    except Exception as e:
        print_error(f"Delete error: {str(e)}")
        return False

# ============================================================================
# IMAGE TESTS
# ============================================================================

def test_image_generation():
    """Test image generation"""
    print_test("Image Generation")
    
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}"}
        
        response = requests.post(
            f"{BASE_URL}/api/v1/images/generate",
            headers=headers,
            json={
                "prompt": "A simple red circle on white background",
                "model": "grok-2-image",
                "n": 1
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Image generation works")
            if data.get("data"):
                print_info(f"Generated {len(data['data'])} image(s)")
                print_info(f"URL: {data['data'][0].get('url', 'N/A')[:60]}...")
            return True
        else:
            print_error(f"Image generation failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Image generation error: {str(e)}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}xAI API Comprehensive Test Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    # Check configuration
    print(f"\n{BLUE}Configuration:{RESET}")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"XAI_API_KEY: {'(set)' if XAI_API_KEY else '(NOT SET)'}")
    print_info(f"XAI_API_AUTH: {os.getenv('XAI_API_AUTH', 'false')}")
    print_info(f"XAI_TOOLS_ENABLED: {os.getenv('XAI_TOOLS_ENABLED', 'false')}")
    print_info(f"XAI_NATIVE_TOOLS_ENABLED: {os.getenv('XAI_NATIVE_TOOLS_ENABLED', 'false')}")
    print_info(f"XAI_API_AUTH_EXCLUDE_DOCS: {os.getenv('XAI_API_AUTH_EXCLUDE_DOCS', 'true')}")
    
    if not XAI_API_KEY:
        print_error("XAI_API_KEY not set! Tests will fail.")
        sys.exit(1)
    
    results = {}
    
    # Run all tests
    tests = [
        ("Health Endpoint", test_health),
        ("Documentation Accessibility", test_docs_accessibility),
        ("Chat Completion - Basic", test_chat_completion_basic),
        ("Chat Completion - Streaming", test_chat_completion_streaming),
        ("Chat Completion - Function Calling", test_chat_completion_with_tools),
        ("Chat Completion - Tools Disabled", test_chat_completion_without_tools_when_disabled),
        ("Responses API - Basic", test_responses_basic),
        ("Responses API - Web Search", test_responses_with_web_search),
        ("Responses API - Retrieve", test_responses_retrieve),
        ("Responses API - Delete", test_responses_delete),
        ("Image Generation", test_image_generation),
    ]
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
            time.sleep(0.5)  # Small delay between tests
        except Exception as e:
            print_error(f"Test '{name}' crashed: {str(e)}")
            results[name] = False
    
    # Print summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} - {name}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Results: {passed}/{total} tests passed{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    if passed == total:
        print_success("All tests passed! ✅ Safe to deploy.")
        sys.exit(0)
    else:
        print_error(f"{total - passed} test(s) failed. Fix issues before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
