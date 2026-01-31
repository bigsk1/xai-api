#!/usr/bin/env python3
"""
Test suite for xAI Responses API

This tests the new Responses API with:
- Basic chat (no tools)
- Web search tool
- X search tool  
- Code execution tool
- Stateful conversations (previous_response_id)
- Retrieve response
- Delete response
"""

import os
import requests
import time
import json

# Configuration
API_BASE = "http://localhost:8000/api/v1"
XAI_API_KEY = os.environ.get("XAI_API_KEY")

if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY environment variable not set")

# Default model
MODEL = os.environ.get("DEFAULT_CHAT_MODEL", "grok-4-1-fast-non-reasoning")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {XAI_API_KEY}"
}

# Store response IDs for cleanup
response_ids = []

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_result(success, message, details=None):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"  Details: {details}")

def test_basic_chat():
    """Test 1: Basic chat without tools."""
    print_section("Test 1: Basic Chat (No Tools)")
    
    try:
        data = {
            "model": MODEL,
            "input": [
                {"role": "user", "content": "What is 2+2? Answer in one word."}
            ]
        }
        
        response = requests.post(
            f"{API_BASE}/responses",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            response_ids.append(result["id"])
            
            # Extract the text response
            text = result["output"][-1]["content"][0]["text"]
            usage = result["usage"]
            
            print_result(True, "Basic chat successful")
            print(f"  Response ID: {result['id']}")
            print(f"  Response: {text}")
            print(f"  Tokens: {usage['input_tokens']} in / {usage['output_tokens']} out / {usage['total_tokens']} total")
            
            return result["id"]
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return None
            
    except Exception as e:
        print_result(False, "Exception occurred", str(e))
        return None

def test_web_search():
    """Test 2: Responses API with web search tool."""
    print_section("Test 2: Web Search Tool")
    
    try:
        data = {
            "model": MODEL,
            "input": [
                {"role": "user", "content": "What is the current price of Bitcoin? Just give me the approximate number."}
            ],
            "tools": [
                {"type": "web_search"}
            ]
        }
        
        print("  Searching the web... (this may take 10-15 seconds)")
        
        response = requests.post(
            f"{API_BASE}/responses",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            response_ids.append(result["id"])
            
            # Count web search calls
            search_calls = sum(1 for item in result["output"] if item.get("type") == "web_search_call")
            
            # Extract final response
            text = result["output"][-1]["content"][0]["text"] if result["output"][-1].get("content") else "No text response"
            usage = result["usage"]
            
            print_result(True, "Web search successful")
            print(f"  Response ID: {result['id']}")
            print(f"  Search calls made: {search_calls}")
            print(f"  Response: {text[:200]}..." if len(text) > 200 else f"  Response: {text}")
            print(f"  Tokens: {usage['input_tokens']} in / {usage['output_tokens']} out / {usage['total_tokens']} total")
            
            return result["id"]
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return None
            
    except Exception as e:
        print_result(False, "Exception occurred", str(e))
        return None

def test_code_execution():
    """Test 3: Responses API with code execution."""
    print_section("Test 3: Code Execution Tool")
    
    try:
        data = {
            "model": MODEL,
            "input": [
                {"role": "user", "content": "Calculate the 20th Fibonacci number using Python. Show me the code and result."}
            ],
            "tools": [
                {"type": "code_execution"}
            ],
            "include": ["code_execution_call_output"]
        }
        
        print("  Executing code... (this may take 10-15 seconds)")
        
        response = requests.post(
            f"{API_BASE}/responses",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            response_ids.append(result["id"])
            
            # Extract response
            text = result["output"][-1]["content"][0]["text"] if result["output"][-1].get("content") else "No text response"
            usage = result["usage"]
            
            print_result(True, "Code execution successful")
            print(f"  Response ID: {result['id']}")
            print(f"  Response: {text[:300]}..." if len(text) > 300 else f"  Response: {text}")
            print(f"  Tokens: {usage['input_tokens']} in / {usage['output_tokens']} out / {usage['total_tokens']} total")
            
            return result["id"]
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return None
            
    except Exception as e:
        print_result(False, "Exception occurred", str(e))
        return None

def test_stateful_conversation():
    """Test 4: Stateful conversation with previous_response_id."""
    print_section("Test 4: Stateful Conversation")
    
    try:
        # First message
        print("  Sending first message...")
        data1 = {
            "model": MODEL,
            "input": [
                {"role": "system", "content": "You are a helpful assistant. Be concise."},
                {"role": "user", "content": "What is the capital of France?"}
            ],
            "store": True
        }
        
        response1 = requests.post(
            f"{API_BASE}/responses",
            headers=headers,
            json=data1,
            timeout=30
        )
        
        if response1.status_code != 200:
            print_result(False, f"First message failed: HTTP {response1.status_code}", response1.text)
            return None
        
        result1 = response1.json()
        response_ids.append(result1["id"])
        conversation_id = result1["id"]
        
        text1 = result1["output"][-1]["content"][0]["text"]
        tokens1 = result1["usage"]["total_tokens"]
        
        print(f"  First response: {text1}")
        print(f"  Tokens used: {tokens1}")
        print(f"  Conversation ID: {conversation_id}")
        
        # Wait a moment
        time.sleep(1)
        
        # Follow-up message using previous_response_id
        print("\n  Sending follow-up message (using previous_response_id)...")
        data2 = {
            "model": MODEL,
            "previous_response_id": conversation_id,
            "input": [
                {"role": "user", "content": "What is the population of that city?"}
            ],
            "store": True
        }
        
        response2 = requests.post(
            f"{API_BASE}/responses",
            headers=headers,
            json=data2,
            timeout=30
        )
        
        if response2.status_code == 200:
            result2 = response2.json()
            response_ids.append(result2["id"])
            
            text2 = result2["output"][-1]["content"][0]["text"]
            tokens2 = result2["usage"]["total_tokens"]
            
            print_result(True, "Stateful conversation successful")
            print(f"  Follow-up response: {text2[:150]}...")
            print(f"  Tokens used: {tokens2} (vs {tokens1} for first message)")
            print(f"  Token savings: ~{100 - int(tokens2/tokens1*100)}%")
            
            return result2["id"]
        else:
            print_result(False, f"Follow-up message failed: HTTP {response2.status_code}", response2.text)
            return None
            
    except Exception as e:
        print_result(False, "Exception occurred", str(e))
        return None

def test_retrieve_response(response_id):
    """Test 5: Retrieve a previous response."""
    print_section("Test 5: Retrieve Response")
    
    if not response_id:
        print_result(False, "No response ID to retrieve", "Skipping test")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE}/responses/{response_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print_result(True, "Retrieve successful")
            print(f"  Retrieved response ID: {result['id']}")
            print(f"  Model: {result['model']}")
            print(f"  Output items: {len(result['output'])}")
            print(f"  Created: {result['created']}")
            
            return True
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Exception occurred", str(e))
        return False

def test_delete_response(response_id):
    """Test 6: Delete a response."""
    print_section("Test 6: Delete Response")
    
    if not response_id:
        print_result(False, "No response ID to delete", "Skipping test")
        return False
    
    try:
        response = requests.delete(
            f"{API_BASE}/responses/{response_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print_result(True, "Delete successful")
            print(f"  Deleted response ID: {result['id']}")
            print(f"  Deleted: {result['deleted']}")
            
            # Remove from our tracking list
            if response_id in response_ids:
                response_ids.remove(response_id)
            
            return True
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Exception occurred", str(e))
        return False

def test_streaming():
    """Test 7: Streaming responses."""
    print_section("Test 7: Streaming Response")
    
    try:
        data = {
            "model": MODEL,
            "input": [
                {"role": "user", "content": "Count from 1 to 5, one number per line."}
            ],
            "stream": True
        }
        
        print("  Receiving stream...")
        
        response = requests.post(
            f"{API_BASE}/responses",
            headers=headers,
            json=data,
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str != '[DONE]':
                            chunk_count += 1
            
            print_result(True, "Streaming successful")
            print(f"  Chunks received: {chunk_count}")
            
            return True
        else:
            print_result(False, f"HTTP {response.status_code}", response.text)
            return False
            
    except Exception as e:
        print_result(False, "Exception occurred", str(e))
        return False

def cleanup():
    """Clean up any remaining test responses."""
    print_section("Cleanup")
    
    if not response_ids:
        print("  No responses to clean up")
        return
    
    print(f"  Cleaning up {len(response_ids)} test responses...")
    
    for response_id in response_ids[:]:  # Copy list to avoid modification during iteration
        try:
            response = requests.delete(
                f"{API_BASE}/responses/{response_id}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                print(f"  ✓ Deleted {response_id}")
                response_ids.remove(response_id)
            else:
                print(f"  ✗ Failed to delete {response_id}: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error deleting {response_id}: {str(e)}")
    
    print(f"  Cleanup complete. {len(response_ids)} responses remaining.")

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  xAI Responses API Test Suite")
    print("="*60)
    print(f"  API Base: {API_BASE}")
    print(f"  Model: {MODEL}")
    print("="*60)
    
    # Track test results
    results = []
    
    # Test 1: Basic chat
    test_id = test_basic_chat()
    results.append(("Basic Chat", test_id is not None))
    time.sleep(1)
    
    # Test 2: Web search
    test_id = test_web_search()
    results.append(("Web Search", test_id is not None))
    time.sleep(1)
    
    # Test 3: Code execution
    test_id = test_code_execution()
    results.append(("Code Execution", test_id is not None))
    time.sleep(1)
    
    # Test 4: Stateful conversation
    conversation_id = test_stateful_conversation()
    results.append(("Stateful Conversation", conversation_id is not None))
    time.sleep(1)
    
    # Test 5: Retrieve (use the conversation_id from test 4)
    if conversation_id:
        retrieve_success = test_retrieve_response(conversation_id)
        results.append(("Retrieve Response", retrieve_success))
        time.sleep(1)
    
    # Test 6: Delete (use the conversation_id from test 4)
    if conversation_id:
        delete_success = test_delete_response(conversation_id)
        results.append(("Delete Response", delete_success))
        time.sleep(1)
    
    # Test 7: Streaming
    stream_success = test_streaming()
    results.append(("Streaming", stream_success))
    
    # Cleanup
    cleanup()
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed!")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        cleanup()
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        cleanup()
        exit(1)
