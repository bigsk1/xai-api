import os
import sys
import time
import requests
import base64

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Constants
API_BASE_URL = "http://localhost:8000"
API_KEY = os.environ.get("XAI_API_KEY")

if not API_KEY:
    raise ValueError("API_KEY environment variable not set")

# Headers for API requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def print_separator(title):
    print(f"\n=== {title} ===")

def test_health_check():
    print_separator("Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        
        if response.status_code == 200:
            print(f"Success! Response: {response.json()}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_chat_completion():
    print_separator("Chat Completion (Direct API)")
    
    try:
        data = {
            "model": "grok-4-1-fast-non-reasoning",
            "messages": [
                {"role": "user", "content": "What is the capital of Germany?"}
            ],
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {result['choices'][0]['message']['content']}")
            print(f"Model: {result['model']}")
            print(f"Tokens: {result['usage']['total_tokens']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_streaming_chat():
    print_separator("Streaming Chat Completion (Direct API)")
    
    try:
        data = {
            "model": "grok-4-1-fast-non-reasoning",
            "messages": [
                {"role": "user", "content": "Write three facts about space exploration"}
            ],
            "temperature": 0.7,
            "stream": True
        }
        
        # For streaming requests, we need to use stream=True in the request
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chat/completions",
            headers=headers,
            json=data,
            stream=True
        )
        
        if response.status_code == 200:
            print("Streaming response (first few chunks):")
            
            chunk_count = 0
            content_so_far = ""
            
            # Process the SSE stream
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    
                    # Skip empty lines or non-data lines
                    if not line.startswith('data: '):
                        continue
                        
                    # Handle the [DONE] message
                    if line.strip() == 'data: [DONE]':
                        break
                        
                    # Parse the JSON data
                    import json
                    json_str = line[6:]  # Remove 'data: ' prefix
                    
                    try:
                        chunk = json.loads(json_str)
                        delta_content = chunk['choices'][0]['delta'].get('content', '')
                        content_so_far += delta_content
                        
                        # Print only the first 3 chunks to keep output clean
                        if chunk_count < 3:
                            print(f"Chunk {chunk_count+1}: {json_str[:50]}...")
                            
                        chunk_count += 1
                    except json.JSONDecodeError:
                        print(f"Error parsing chunk: {line}")
            
            print(f"Received {chunk_count} chunks total")
            print(f"Final content length: {len(content_so_far)} characters")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_vision_analysis():
    print_separator("Vision Analysis (Direct API)")
    
    try:
        data = {
            "model": "grok-2-vision-latest",
            "image": {
                "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
            },
            "prompt": "What animals are in this image and what are they doing?",
            "detail": "high",
            "temperature": 0.01
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/vision/analyze",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {result['content']}")
            print(f"Model: {result['model']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_vision_local_image():
    print_separator("Vision Analysis with Local Image")
    try:
        # Path to local image file
        image_path = "../images/image.jpg"  # Adjust path as needed
        
        # Check if file exists
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at {image_path}")
            return False
            
        # Read and encode the image file
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')
        
        data = {
            "model": "grok-2-vision-latest",
            "image": {
                "b64_json": base64_encoded
            },
            "prompt": "Describe this image in detail",
            "detail": "high"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/vision/analyze",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {result['content']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_image_generation():
    print_separator("Image Generation (Direct API)")
    
    try:
        data = {
            "model": "grok-2-image",
            "prompt": "A beautiful waterfall in a lush forest",
            "n": 1
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/images/generate",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Image URL: {result['data'][0]['url']}")
            print(f"Model: {result['model']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_multiple_images():
    print_separator("Generate Multiple Images")
    
    try:
        data = {
            "model": "grok-2-image",
            "prompt": "Abstract paintings in different styles",
            "n": 2
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/images/generate",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            for i, image in enumerate(result['data']):
                print(f"Success! Image {i+1} URL: {image['url']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_base64_image():
    print_separator("Image Generation with Base64 Response")
    
    try:
        data = {
            "model": "grok-2-image",
            "prompt": "A geometric pattern with bright colors",
            "n": 1,
            "response_format": "b64_json"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/images/generate",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'b64_json' in result['data'][0]:
                print("Success! Received base64 encoded image")
                return True
            else:
                print("Error: Base64 response not received")
                return False
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def run_all_tests():
    results = {}
    
    # Health check
    results["health"] = test_health_check()
    time.sleep(1)
    
    # Chat completion
    results["chat"] = test_chat_completion()
    time.sleep(1)
    
    # Streaming chat
    results["streaming_chat"] = test_streaming_chat()
    time.sleep(1)
    
    # Vision analysis tests
    results["vision_url"] = test_vision_analysis()
    time.sleep(1)
    
    results["vision_local"] = test_vision_local_image()
    time.sleep(1)
    
    # Image generation tests
    results["image_basic"] = test_image_generation()
    time.sleep(1)
    
    results["image_multiple"] = test_multiple_images()
    time.sleep(1)
    
    results["image_base64"] = test_base64_image()
    
    # Print summary
    print("\n=== Test Results Summary ===")
    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test.upper()}: {status}")
    
    # Check overall success
    if all(results.values()):
        print("\n🎉 All direct API tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check the details above for more information.")

if __name__ == "__main__":
    run_all_tests() 