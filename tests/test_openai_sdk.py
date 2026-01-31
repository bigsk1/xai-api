import os
import time
import sys
from openai import OpenAI

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up client
API_KEY = os.environ.get("XAI_API_KEY")
API_BASE_URL = "http://localhost:8000/api/v1"

if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

print(f"Testing OpenAI SDK compatibility against {API_BASE_URL}")

client = OpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL
)

def test_chat_completion():
    print("\n=== Testing Chat Completion with OpenAI SDK ===")
    try:
        response = client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            messages=[
                {"role": "user", "content": "What is the capital of France?"}
            ],
            temperature=0.7
        )
        
        print(f"Success! Response: {response.choices[0].message.content}")
        print(f"Model: {response.model}")
        print(f"Tokens: {response.usage.total_tokens}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_vision_analysis():
    print("\n=== Testing Vision Analysis with OpenAI SDK ===")
    try:
        response = client.chat.completions.create(
            model="grok-2-vision-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg",
                                "detail": "high",
                            },
                        },
                        {
                            "type": "text",
                            "text": "What animals are in this image?",
                        },
                    ],
                }
            ],
            temperature=0.01
        )
        
        print(f"Success! Response: {response.choices[0].message.content}")
        print(f"Model: {response.model}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_image_generation():
    print("\n=== Testing Image Generation with OpenAI SDK ===")
    try:
        response = client.images.generate(
            model="grok-2-image",
            prompt="A beautiful sunset over mountains",
            n=1
        )
        
        print(f"Success! Image URL: {response.data[0].url}")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_streaming_chat():
    print("\n=== Testing Streaming Chat with OpenAI SDK ===")
    try:
        print("Streaming response (first 100 characters): ", end="")
        char_count = 0
        full_response = ""
        
        stream = client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            messages=[
                {"role": "user", "content": "Write a short poem about technology"}
            ],
            stream=True,
            temperature=0.7
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                
                # Print just the first 100 characters to keep the output clean
                if char_count < 100:
                    remaining = 100 - char_count
                    to_print = content[:remaining]
                    print(to_print, end="", flush=True)
                    char_count += len(to_print)
        
        print("...")
        print(f"Total response length: {len(full_response)} characters")
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def run_tests():
    results = {}
    
    # Test chat completion
    results["chat"] = test_chat_completion()
    time.sleep(1)
    
    # Test streaming chat
    results["streaming_chat"] = test_streaming_chat()
    time.sleep(1)
    
    # Test vision analysis
    results["vision"] = test_vision_analysis()
    time.sleep(1)
    
    # Test image generation
    results["image"] = test_image_generation()
    
    # Print summary
    print("\n=== Test Results Summary ===")
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test.upper()}: {status}")
    
    # Check overall success
    if all(results.values()):
        print("\n🎉 All OpenAI SDK compatibility tests passed! Your API is fully compatible.")
    else:
        print("\n⚠️ Some tests failed. Check the details above for more information.")

if __name__ == "__main__":
    run_tests() 