# API Integration Guide

## OpenAI SDK Compatibility

**Key Feature**: This API is fully compatible with the OpenAI SDK!

You can integrate with our xAI API using the same OpenAI SDK you might already be familiar with. This makes migration and integration incredibly easy - just point the SDK to our API endpoint instead of OpenAI's.

All three main services are supported through the OpenAI SDK:
- Chat completions
- Vision analysis
- Image generation

The examples later in this document show both direct HTTP requests and OpenAI SDK usage for each endpoint.

## API Base URL

When the FastAPI application is running locally:
```
http://localhost:8000/api/v1
```

For production deployments, replace with your domain:
```
https://your-domain.com/api/v1
```

## Authentication

All API requests require authentication using your xAI API key. Include this in the `Authorization` header:

```
Authorization: Bearer YOUR_XAI_API_KEY
```

## Python Integration

### Installing Required Packages

```bash
pip install requests
```

### Image Generation

```python
import requests
import json
import os

def generate_image(prompt, model=None, n=1, response_format=None):
    """
    Generate images using xAI Grok API
    
    Args:
        prompt (str): Text description of the image to generate
        model (str, optional): Model to use for image generation
        n (int, optional): Number of images to generate (default: 1)
        response_format (str, optional): Format in which the generated images are returned ("url" or "b64_json")
        
    Returns:
        dict: Generated image data
    """
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI API key not found in environment variables")
    
    url = "http://localhost:8000/api/v1/images/generate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Build request data
    data = {"prompt": prompt, "n": n}
    
    # Add optional parameters if provided
    if model: data["model"] = model
    if response_format: data["response_format"] = response_format
    
    # Make the API request
    response = requests.post(url, headers=headers, json=data)
    
    # Check for errors
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
        
    return response.json()

# Example usage
try:
    result = generate_image(
        prompt="A beautiful mountain landscape with a waterfall",
        model="grok-2-image"
    )
    
    print(f"Generated {len(result['data'])} image(s)")
    
    for i, image_data in enumerate(result["data"]):
        print(f"Image {i+1}: {image_data.get('url', 'No URL')}")
        
except Exception as e:
    print(f"Error: {str(e)}")
```

### Image Vision/Analysis

```python
import requests
import base64
from pathlib import Path
import os

def analyze_image_url(image_url, model=None, max_tokens=1024):
    """
    Analyze an image from a URL using xAI Grok Vision API
    
    Args:
        image_url (str): URL of the image to analyze
        model (str, optional): Model to use for image analysis
        max_tokens (int, optional): Maximum number of tokens to generate
        
    Returns:
        dict: Image analysis result
    """
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI API key not found in environment variables")
    
    url = "http://localhost:8000/api/v1/vision/analyze"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Build request data
    data = {
        "image": {"url": image_url},
        "max_tokens": max_tokens
    }
    
    # Add optional parameters if provided
    if model: data["model"] = model
    
    # Make the API request
    response = requests.post(url, headers=headers, json=data)
    
    # Check for errors
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
        
    return response.json()

def analyze_image_file(image_path, model=None, max_tokens=1024):
    """
    Analyze an image from a local file using xAI Grok Vision API
    
    Args:
        image_path (str): Path to the local image file
        model (str, optional): Model to use for image analysis
        max_tokens (int, optional): Maximum number of tokens to generate
        
    Returns:
        dict: Image analysis result
    """
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI API key not found in environment variables")
    
    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode("utf-8")
    
    url = "http://localhost:8000/api/v1/vision/analyze"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Build request data
    data = {
        "image": {"b64_json": base64_image},
        "max_tokens": max_tokens
    }
    
    # Add optional parameters if provided
    if model: data["model"] = model
    
    # Make the API request
    response = requests.post(url, headers=headers, json=data)
    
    # Check for errors
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
        
    return response.json()

# Example usage
try:
    # Analyze from URL
    result = analyze_image_url(
        image_url="https://example.com/image.jpg",
        model="grok-2-vision-latest"
    )
    
    print(f"Analysis result: {result['content']}")
    
    # Analyze from file
    # file_result = analyze_image_file("path/to/local/image.jpg")
    # print(f"File analysis result: {file_result['content']}")
    
except Exception as e:
    print(f"Error: {str(e)}")
```

### Chat Completions

```python
import requests
import os

def chat_completion(messages, model=None, max_tokens=1024, temperature=0.7, top_p=1.0):
    """
    Generate chat completions using xAI Grok API
    
    Args:
        messages (list): List of message objects with 'role' and 'content'
        model (str, optional): Model to use for chat completions
        max_tokens (int, optional): Maximum number of tokens to generate
        temperature (float, optional): Sampling temperature (0-1)
        top_p (float, optional): Nucleus sampling parameter (0-1)
        
    Returns:
        dict: Chat completion result
    """
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise ValueError("XAI API key not found in environment variables")
    
    url = "http://localhost:8000/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Build request data
    data = {
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p
    }
    
    # Add optional parameters if provided
    if model: data["model"] = model
    
    # Make the API request
    response = requests.post(url, headers=headers, json=data)
    
    # Check for errors
    if response.status_code != 200:
        raise Exception(f"API Error: {response.status_code} - {response.text}")
        
    return response.json()

# Example usage
try:
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What are three ways to improve productivity?"}
    ]
    
    result = chat_completion(
        messages=messages,
        model="grok-4-1-fast-non-reasoning",
        temperature=0.7
    )
    
    # Extract the assistant's response
    assistant_message = result["choices"][0]["message"]["content"]
    print(f"Assistant: {assistant_message}")
    
except Exception as e:
    print(f"Error: {str(e)}")
```

## JavaScript/Node.js Integration

### Image Generation

```javascript
const fetch = require('node-fetch');

async function generateImage(prompt, options = {}) {
  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) {
    throw new Error('XAI API key not found in environment variables');
  }
  
  const url = 'http://localhost:8000/api/v1/images/generate';
  
  // Build request data
  const data = {
    prompt,
    n: options.n || 1,
    ...options.model && { model: options.model },
    ...options.response_format && { response_format: options.response_format }
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Error generating image:', error);
    throw error;
  }
}

// Example usage
async function main() {
  try {
    const result = await generateImage(
      'A futuristic cityscape with flying vehicles',
      {
        model: 'grok-2-image'
      }
    );
    
    console.log(`Generated ${result.data.length} image(s)`);
    result.data.forEach((image, i) => {
      console.log(`Image ${i+1}: ${image.url || 'No URL'}`);
    });
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

main();
```

### Image Vision/Analysis

```javascript
const fetch = require('node-fetch');
const fs = require('fs').promises;

async function analyzeImageUrl(imageUrl, options = {}) {
  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) {
    throw new Error('XAI API key not found in environment variables');
  }
  
  const url = 'http://localhost:8000/api/v1/vision/analyze';
  
  // Build request data
  const data = {
    image: { url: imageUrl },
    max_tokens: options.max_tokens || 1024,
    ...options.model && { model: options.model }
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Error analyzing image:', error);
    throw error;
  }
}

async function analyzeImageFile(imagePath, options = {}) {
  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) {
    throw new Error('XAI API key not found in environment variables');
  }
  
  // Read and encode the image file
  const imageBuffer = await fs.readFile(imagePath);
  const base64Image = imageBuffer.toString('base64');
  
  const url = 'http://localhost:8000/api/v1/vision/analyze';
  
  // Build request data
  const data = {
    image: { b64_json: base64Image },
    max_tokens: options.max_tokens || 1024,
    ...options.model && { model: options.model }
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Error analyzing image:', error);
    throw error;
  }
}

// Example usage
async function main() {
  try {
    // Analyze from URL
    const result = await analyzeImageUrl(
      'https://example.com/image.jpg',
      { model: 'grok-2-vision-latest' }
    );
    
    console.log(`Analysis result: ${result.content}`);
    
    // Analyze from file
    // const fileResult = await analyzeImageFile('path/to/local/image.jpg');
    // console.log(`File analysis result: ${fileResult.content}`);
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

main();
```

### Chat Completions

```javascript
const fetch = require('node-fetch');

async function chatCompletion(messages, options = {}) {
  const apiKey = process.env.XAI_API_KEY;
  if (!apiKey) {
    throw new Error('XAI API key not found in environment variables');
  }
  
  const url = 'http://localhost:8000/api/v1/chat/completions';
  
  // Build request data
  const data = {
    messages,
    max_tokens: options.max_tokens || 1024,
    temperature: options.temperature || 0.7,
    top_p: options.top_p || 1.0,
    ...options.model && { model: options.model }
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    
    return await response.json();
    
  } catch (error) {
    console.error('Error in chat completion:', error);
    throw error;
  }
}

// Example usage
async function main() {
  try {
    const messages = [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: 'What are three ways to improve productivity?' }
    ];
    
    const result = await chatCompletion(
      messages,
      { model: 'grok-4-1-fast-non-reasoning', temperature: 0.7 }
    );
    
    // Extract the assistant's response
    const assistantMessage = result.choices[0].message.content;
    console.log(`Assistant: ${assistantMessage}`);
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

main();
```

## Error Handling

All API endpoints may return error responses. Here's how to handle them:

```python
try:
    # Make API request
    response = requests.post(url, headers=headers, json=data)
    
    # Check for errors
    if response.status_code != 200:
        error_data = response.json()
        error_message = error_data.get("message", "Unknown error")
        error_details = error_data.get("details", {})
        
        print(f"API Error: {response.status_code} - {error_message}")
        if error_details:
            print(f"Details: {error_details}")
    else:
        result = response.json()
        # Process successful response
        
except Exception as e:
    print(f"Request failed: {str(e)}")
```

## Rate Limiting

The API has rate limiting in place. If you exceed the limits, you'll receive a 429 response. 
Here's how to handle rate limiting:

```python
response = requests.post(url, headers=headers, json=data)

if response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", 60))
    print(f"Rate limit exceeded. Retry after {retry_after} seconds.")
    
    # Implement exponential backoff
    import time
    time.sleep(retry_after)
    
    # Retry the request
    response = requests.post(url, headers=headers, json=data)
```

## API Integration Approaches: Direct HTTP vs OpenAI SDK

There are two main ways to integrate with the xAI API:

### Approach 1: Direct HTTP Requests

You can make HTTP requests directly to the API endpoints using any HTTP client library:
- Python: `requests`, `httpx`, `aiohttp`
- JavaScript: `fetch`, `axios`, `node-fetch`
- Other languages: Any HTTP client library

This approach requires you to format the requests manually according to the API documentation.

### Approach 2: OpenAI SDK (Recommended)

Because the xAI API is compatible with the OpenAI API format, you can use the OpenAI SDK to interact with ALL endpoints:
- Chat completions
- Vision analysis
- Image generation

This is simpler and recommended for most use cases.

```python
import os
from openai import OpenAI

# Set up the client once and use for all API calls
client = OpenAI(
    api_key=os.environ.get("XAI_API_KEY"),
    base_url="http://localhost:8000/api/v1",  # Point to your FastAPI server
)

# CHAT: Basic chat completion
chat_response = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ],
    temperature=0.7,
)
print(chat_response.choices[0].message.content)

# VISION: Image analysis using the chat completions endpoint
vision_response = client.chat.completions.create(
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
    temperature=0.01,
)
print(vision_response.choices[0].message.content)

# IMAGE GENERATION: Generate an image
image_response = client.images.generate(
    model="grok-2-image",
    prompt="A beautiful sunset over mountains",
    n=1,
    size="1024x1024"  # Note: Currently ignored by xAI but included for API compatibility
)
print(f"Image URL: {image_response.data[0].url}")
```

As shown above, you can use the OpenAI SDK for ALL xAI API operations. The vision analysis is done through the chat completions endpoint with a specific message format, which is why it uses `client.chat.completions.create` rather than a separate vision method. 