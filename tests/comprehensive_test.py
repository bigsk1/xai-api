import os
import requests
import base64
import time
from openai import OpenAI
from colorama import init, Fore, Style

# Initialize colorama for colored console output
init()

# Constants
API_BASE_URL = "http://localhost:8000"
API_KEY = os.environ.get("XAI_API_KEY")

if not API_KEY:
    print(f"{Fore.RED}Error: XAI_API_KEY environment variable not set{Style.RESET_ALL}")
    exit(1)

# Headers for API requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# OpenAI SDK client
openai_client = OpenAI(
    api_key=API_KEY,
    base_url=f"{API_BASE_URL}/api/v1"
)

def print_section(title):
    """Print a formatted section title"""
    print(f"\n{Fore.CYAN}{'=' * 20} {title} {'=' * 20}{Style.RESET_ALL}")

def print_subsection(title):
    """Print a formatted subsection title"""
    print(f"\n{Fore.YELLOW}--- {title} ---{Style.RESET_ALL}")

def print_success(message):
    """Print a success message"""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print an error message"""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_info(message):
    """Print an info message"""
    print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")

def test_health_check():
    """Test the health check endpoint"""
    print_section("Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        
        if response.status_code == 200:
            print_success(f"Health check successful: {response.json()}")
        else:
            print_error(f"Health check failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Health check error: {str(e)}")

def test_chat_completion_direct():
    """Test chat completion using direct API calls"""
    print_section("Chat Completion (Direct API)")
    
    # Basic chat completion
    print_subsection("Basic Chat")
    try:
        data = {
            "model": "grok-3-mini-beta",
            "messages": [
                {"role": "user", "content": "What is the capital of France?"}
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
            print_success(f"Response: {result['choices'][0]['message']['content']}")
            print_info(f"Model: {result['model']}")
            print_info(f"Tokens: {result['usage']['total_tokens']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    # Chat completion with system message
    print_subsection("Chat with System Message")
    try:
        data = {
            "model": "grok-3-mini-beta",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that speaks like a pirate."},
                {"role": "user", "content": "Tell me about the weather today."}
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
            print_success(f"Response: {result['choices'][0]['message']['content']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    # Chat completion with different temperature
    print_subsection("Chat with Different Temperature")
    try:
        data = {
            "model": "grok-3-mini-beta",
            "messages": [
                {"role": "user", "content": "Write a short poem about coding."}
            ],
            "temperature": 1.0,  # Higher temperature for more creativity
            "max_tokens": 100
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Response: {result['choices'][0]['message']['content']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_chat_completion_sdk():
    """Test chat completion using OpenAI SDK"""
    print_section("Chat Completion (OpenAI SDK)")
    
    # Basic chat completion
    print_subsection("Basic Chat")
    try:
        response = openai_client.chat.completions.create(
            model="grok-3-mini-beta",
            messages=[
                {"role": "user", "content": "What is the capital of Japan?"}
            ],
            temperature=0.7
        )
        
        print_success(f"Response: {response.choices[0].message.content}")
        print_info(f"Model: {response.model}")
        print_info(f"Tokens: {response.usage.total_tokens}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    # Chat with conversation history
    print_subsection("Chat with Conversation History")
    try:
        response = openai_client.chat.completions.create(
            model="grok-3-mini-beta",
            messages=[
                {"role": "user", "content": "My name is Alice."},
                {"role": "assistant", "content": "Hello Alice, how can I help you today?"},
                {"role": "user", "content": "What was my name again?"}
            ],
            temperature=0.7
        )
        
        print_success(f"Response: {response.choices[0].message.content}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_vision_analysis_direct():
    """Test vision analysis using direct API calls"""
    print_section("Vision Analysis (Direct API)")
    
    # Analyze image from URL
    print_subsection("Vision Analysis from URL")
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
            print_success(f"Response: {result['content']}")
            print_info(f"Model: {result['model']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    # Analyze with different prompt
    print_subsection("Vision Analysis with Specific Question")
    try:
        data = {
            "model": "grok-2-vision-latest",
            "image": {
                "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
            },
            "prompt": "What colors are present in this image?",
            "detail": "high"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/vision/analyze",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Response: {result['content']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        
    # Analyze local image with base64 encoding
    print_subsection("Vision Analysis with Local Image")
    try:
        # Path to local image file
        image_path = "images/image.jpg"
        
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
            print_success(f"Response: {result['content']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_image_generation_direct():
    """Test image generation using direct API calls"""
    print_section("Image Generation (Direct API)")
    
    # Basic image generation
    print_subsection("Basic Image Generation")
    try:
        data = {
            "model": "grok-2-image",
            "prompt": "A beautiful sunset over mountains with a lake reflection",
            "n": 1
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/images/generate",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Image URL: {result['data'][0]['url']}")
            print_info(f"Model: {result['model']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    # Generate multiple images
    print_subsection("Generate Multiple Images")
    try:
        data = {
            "model": "grok-2-image",
            "prompt": "A futuristic cityscape with flying vehicles",
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
                print_success(f"Image {i+1} URL: {image['url']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    # Base64 response format
    print_subsection("Image Generation with Base64 Response")
    try:
        data = {
            "model": "grok-2-image",
            "prompt": "Abstract geometric patterns in bright colors",
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
                print_success("Successfully received base64 encoded image")
                
                # Save the image to a file
                print_info("Saving generated image to 'images/output_image.jpg'")
                img_data = base64.b64decode(result['data'][0]['b64_json'])
                with open('images/output_image.jpg', 'wb') as f:
                    f.write(img_data)
            else:
                print_error("Base64 response not received")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_image_generation_sdk():
    """Test image generation using OpenAI SDK"""
    print_section("Image Generation (OpenAI SDK)")
    
    # Basic image generation
    print_subsection("Basic Image Generation")
    try:
        # Use the OpenAI SDK correctly for image generation
        # The SDK should work with the proper endpoint mapping
        response = openai_client.images.generate(
            model="grok-2-image",
            prompt="A serene beach at dawn with palm trees",
            n=1
        )
        
        print_success(f"Image URL: {response.data[0].url}")
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        
    # Multiple images with SDK
    print_subsection("Generate Multiple Images with SDK")
    try:
        response = openai_client.images.generate(
            model="grok-2-image",
            prompt="A beautiful mountain landscape",
            n=2
        )
        
        for i, image_data in enumerate(response.data):
            print_success(f"Image {i+1} URL: {image_data.url}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        
    # With different parameters
    print_subsection("Image Generation with Different Parameters")
    try:
        response = openai_client.images.generate(
            model="grok-2-image",
            prompt="Abstract painting with vibrant colors",
            n=1,
            response_format="b64_json"  # Request base64 encoded image
        )
        
        if hasattr(response.data[0], 'b64_json') and response.data[0].b64_json:
            print_success("Successfully received base64 encoded image")
            
            # Save the image to a file
            print_info("Saving generated image to 'images/output_sdk_image.jpg'")
            img_data = base64.b64decode(response.data[0].b64_json)
            with open('images/output_sdk_image.jpg', 'wb') as f:
                f.write(img_data)
        else:
            print_error("Base64 response not received correctly")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def test_image_generation_sdk_compatibility():
    """Test image generation using OpenAI SDK with compatibility adapter"""
    print_section("Image Generation (OpenAI SDK Compatibility)")
    
    print_info("Note: The OpenAI SDK expects endpoint at '/images/generations' but our server uses '/images/generate'")
    print_info("We'll demonstrate how to adapt the OpenAI SDK to work with our custom endpoints")
    
    # Method 1: Use a proxy function that maps endpoints
    print_subsection("Method 1: Custom proxy function")
    try:
        from functools import wraps
        
        # Create a simple wrapper function
        def generate_image_adapter(prompt, model="grok-2-image", n=1, size=None, response_format=None):
            """Adapter function to use OpenAI-like parameters but call our API directly"""
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}"
            }
            
            data = {
                "model": model,
                "prompt": prompt,
                "n": n
            }
            
            if size:
                data["size"] = size
            
            if response_format:
                data["response_format"] = response_format
            
            response = requests.post(
                f"{API_BASE_URL}/api/v1/images/generate",
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Convert to OpenAI-like response format
            class ImageResponse:
                class Data:
                    def __init__(self, data_item):
                        self.url = data_item.get('url')
                        self.b64_json = data_item.get('b64_json')
                
                def __init__(self, result):
                    self.created = result.get('created')
                    self.data = [self.Data(item) for item in result.get('data', [])]
            
            return ImageResponse(result)
        
        # Use our adapter
        response = generate_image_adapter(
            prompt="A serene beach at sunset with palm trees",
            model="grok-2-image",
            n=1
        )
        
        print_success(f"Image URL: {response.data[0].url}")
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    # Method 2: Direct HTTP approach (most reliable)
    print_subsection("Method 2: Direct HTTP Requests (Most Reliable)")
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        data = {
            "model": "grok-2-image",
            "prompt": "A serene beach at dawn with palm trees",
            "n": 1
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/images/generate",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print_success(f"Image URL: {result['data'][0]['url']}")
            print_info(f"Model: {result['model']}")
        else:
            print_error(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print_error(f"Error: {str(e)}")

def run_all_tests():
    """Run all test functions"""
    print(f"{Fore.MAGENTA}{'=' * 30} xAI API COMPREHENSIVE TESTS {'=' * 30}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Testing against API: {API_BASE_URL}/api/v1{Style.RESET_ALL}")
    
    # Health check
    test_health_check()
    time.sleep(1)
    
    # Chat completion tests
    test_chat_completion_direct()
    time.sleep(1)
    test_chat_completion_sdk()
    time.sleep(1)
    
    # Vision analysis tests
    test_vision_analysis_direct()
    time.sleep(1)
    
    # Image generation tests
    test_image_generation_direct()
    time.sleep(1)
    test_image_generation_sdk()
    time.sleep(1)
    
    # OpenAI SDK compatibility test for image generation
    test_image_generation_sdk_compatibility()
    
    print(f"\n{Fore.MAGENTA}{'=' * 30} TEST COMPLETE {'=' * 30}{Style.RESET_ALL}")

if __name__ == "__main__":
    run_all_tests() 