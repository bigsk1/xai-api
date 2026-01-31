#!/usr/bin/env python3
"""
Test script for API authentication middleware.
Tests both enabled and disabled authentication scenarios.
"""

import requests
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Health endpoint should always be accessible (exempt from auth)"""
    print("\n🔍 Testing /health endpoint (should be exempt from auth)...")
    
    response = requests.get(f"{BASE_URL}/health")
    
    if response.status_code == 200:
        print("✅ Health endpoint accessible without auth")
        print(f"   Response: {response.json()}")
        return True
    else:
        print(f"❌ Health endpoint failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_auth_disabled():
    """Test that API works without auth when XAI_API_AUTH=false"""
    print("\n🔍 Testing with XAI_API_AUTH=false...")
    print("   (Should allow requests without Authorization header)")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat/completions",
        json={
            "model": "grok-4-1-fast-non-reasoning",
            "messages": [{"role": "user", "content": "Say 'hello' only"}],
            "max_tokens": 10
        }
    )
    
    if response.status_code == 200:
        print("✅ Request succeeded without auth (XAI_API_AUTH=false)")
        return True
    elif response.status_code == 401:
        print("⚠️  Got 401 - Authentication appears to be ENABLED")
        print(f"   Response: {response.json()}")
        return False
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_auth_enabled_no_token():
    """Test that API rejects requests without token when XAI_API_AUTH=true"""
    print("\n🔍 Testing with XAI_API_AUTH=true (no token)...")
    print("   (Should return 401 Unauthorized)")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat/completions",
        json={
            "model": "grok-4-1-fast-non-reasoning",
            "messages": [{"role": "user", "content": "Say 'hello' only"}],
            "max_tokens": 10
        }
    )
    
    if response.status_code == 401:
        print("✅ Request rejected without token (401)")
        print(f"   Response: {response.json()}")
        return True
    elif response.status_code == 200:
        print("⚠️  Request succeeded - Authentication appears to be DISABLED")
        return False
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_auth_enabled_invalid_token():
    """Test that API rejects requests with invalid token"""
    print("\n🔍 Testing with invalid token...")
    print("   (Should return 401 Unauthorized)")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat/completions",
        headers={"Authorization": "Bearer invalid_token_12345"},
        json={
            "model": "grok-4-1-fast-non-reasoning",
            "messages": [{"role": "user", "content": "Say 'hello' only"}],
            "max_tokens": 10
        }
    )
    
    if response.status_code == 401:
        print("✅ Request rejected with invalid token (401)")
        print(f"   Response: {response.json()}")
        return True
    elif response.status_code == 200:
        print("⚠️  Request succeeded - Token validation not working!")
        return False
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_auth_enabled_valid_token(token: str, header_name: str = "Authorization"):
    """Test that API accepts requests with valid token"""
    print(f"\n🔍 Testing with valid token in {header_name} header...")
    print("   (Should return 200 OK)")
    
    # Prepare headers based on header type
    if header_name == "Authorization":
        headers = {"Authorization": f"Bearer {token}"}
    else:
        headers = {header_name: token}
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "grok-4-1-fast-non-reasoning",
            "messages": [{"role": "user", "content": "Say 'hello' only"}],
            "max_tokens": 10
        }
    )
    
    if response.status_code == 200:
        print(f"✅ Request succeeded with valid token in {header_name}")
        result = response.json()
        if "choices" in result:
            print(f"   Response: {result['choices'][0]['message']['content']}")
        return True
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_custom_header_with_basic_auth(token: str, header_name: str = "X-API-Token"):
    """Test using custom header alongside basic auth (simulated dual auth)"""
    print(f"\n🔍 Testing dual auth simulation...")
    print(f"   Basic Auth (simulated) + {header_name}: <token>")
    
    headers = {
        "Authorization": "Basic YWRtaW46cGFzc3dvcmQ=",  # Simulated basic auth (admin:password)
        header_name: token
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat/completions",
        headers=headers,
        json={
            "model": "grok-4-1-fast-non-reasoning",
            "messages": [{"role": "user", "content": "Say 'hello' only"}],
            "max_tokens": 10
        }
    )
    
    if response.status_code == 200:
        print(f"✅ Dual auth simulation succeeded")
        print(f"   (Basic auth header sent, app checked {header_name})")
        result = response.json()
        if "choices" in result:
            print(f"   Response: {result['choices'][0]['message']['content']}")
        return True
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def main():
    print("=" * 60)
    print("API Authentication Middleware Test")
    print("=" * 60)
    
    # Check current auth settings
    auth_enabled = os.getenv("XAI_API_AUTH", "false").lower() in ("true", "1", "yes")
    auth_token = os.getenv("XAI_API_AUTH_TOKEN", "")
    auth_header = os.getenv("XAI_API_AUTH_HEADER", "Authorization")
    
    print(f"\n📋 Current settings:")
    print(f"   XAI_API_AUTH: {auth_enabled}")
    print(f"   XAI_API_AUTH_TOKEN: {'(set)' if auth_token else '(not set)'}")
    print(f"   XAI_API_AUTH_HEADER: {auth_header}")
    
    results = []
    
    # Test 1: Health endpoint (always accessible)
    results.append(test_health_endpoint())
    
    # Test based on current auth state
    if not auth_enabled:
        print("\n" + "=" * 60)
        print("Testing Mode: AUTH DISABLED")
        print("=" * 60)
        results.append(test_auth_disabled())
        
        print("\n💡 To test auth enabled mode:")
        print("   1. Set XAI_API_AUTH=true in .env")
        print("   2. Set XAI_API_AUTH_TOKEN=your_token in .env")
        print("   3. Optionally set XAI_API_AUTH_HEADER=X-API-Token for custom header")
        print("   4. Restart the server")
        print("   5. Run this test again")
    else:
        print("\n" + "=" * 60)
        print("Testing Mode: AUTH ENABLED")
        print(f"Auth Header: {auth_header}")
        print("=" * 60)
        
        if not auth_token:
            print("\n⚠️  XAI_API_AUTH=true but XAI_API_AUTH_TOKEN is not set!")
            print("   Server will return 500 error for protected endpoints")
        
        results.append(test_auth_enabled_no_token())
        results.append(test_auth_enabled_invalid_token())
        
        if auth_token:
            results.append(test_auth_enabled_valid_token(auth_token, auth_header))
            
            # If using custom header, test dual auth simulation
            if auth_header != "Authorization":
                print(f"\n💡 Custom header mode detected ({auth_header})")
                print("   Testing dual-auth scenario (BasicAuth + custom header)...")
                results.append(test_custom_header_with_basic_auth(auth_token, auth_header))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
