#!/usr/bin/env python3
"""
Test script to verify empty tools array handling.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"

def test_empty_tools_array():
    """Test that empty tools array is handled gracefully."""
    
    print("Testing empty tools array handling...")
    
    payload = {
        "model": "grok-4-1-fast-non-reasoning",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ],
        "tools": [],  # Empty array that should be converted to None
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Empty tools array handled correctly")
            result = response.json()
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ FAILED: Got status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_empty_tools_with_tool_choice():
    """Test that tool_choice is removed when tools is empty."""
    
    print("\n\nTesting empty tools with tool_choice...")
    
    payload = {
        "model": "grok-4-1-fast-non-reasoning",
        "messages": [
            {"role": "user", "content": "What's 2+2?"}
        ],
        "tools": [],  # Empty array
        "tool_choice": "auto"  # Should be removed
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: tool_choice removed when tools is empty")
            result = response.json()
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ FAILED: Got status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_none_tools():
    """Test that tools=None is handled correctly."""
    
    print("\n\nTesting tools=None...")
    
    payload = {
        "model": "grok-4-1-fast-non-reasoning",
        "messages": [
            {"role": "user", "content": "Tell me a joke"}
        ],
        "tools": None
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: tools=None handled correctly")
            result = response.json()
            print(f"Response: {result['choices'][0]['message']['content']}")
            return True
        else:
            print(f"❌ FAILED: Got status {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Empty Tools Array Handling")
    print("=" * 60)
    
    results = []
    
    results.append(("Empty tools array", test_empty_tools_array()))
    results.append(("Empty tools with tool_choice", test_empty_tools_with_tool_choice()))
    results.append(("tools=None", test_none_tools()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
    print("=" * 60)
