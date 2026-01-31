import os
from openai import OpenAI
import time

# Set up the client once and use for all API calls
client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="http://localhost:8000/api/v1",  # Point to the FastAPI server
)

def test_chat_completion():
    print("\n=== Testing Chat Completion ===")
    try:
        chat_response = client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            messages=[
                {"role": "user", "content": "What is the capital of France?"}
            ],
            temperature=0.7,
        )
        print(f"Success! Response: {chat_response.choices[0].message.content}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_vision_analysis():
    print("\n=== Testing Vision Analysis (Direct API) ===")
    import requests
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('XAI_API_KEY')}"
    }
    
    data = {
        "model": "grok-2-vision-latest",
        "image": {
            "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
        },
        "prompt": "What animals are in this image?",
        "detail": "high"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/vision/analyze",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Response: {result['content']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_image_generation():
    print("\n=== Testing Image Generation (Direct API) ===")
    import requests
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('XAI_API_KEY')}"
    }
    
    data = {
        "model": "grok-2-image",
        "prompt": "A beautiful sunset over mountains",
        "n": 1
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/images/generate",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Image URL: {result['data'][0]['url']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Test all endpoints
    test_chat_completion()
    time.sleep(1)  # Add a small delay between requests
    
    test_vision_analysis()
    time.sleep(1)
    
    test_image_generation() 