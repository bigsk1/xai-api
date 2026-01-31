#!/bin/bash
set -e

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# API key - source from .env file or use passed argument
if [ -f "../.env" ]; then
    source <(grep XAI_API_KEY ../.env | sed 's/^/export /')
elif [ -f ".env" ]; then
    source <(grep XAI_API_KEY .env | sed 's/^/export /')
fi

# Allow API key to be passed as argument
if [ $# -eq 1 ]; then
    export XAI_API_KEY=$1
fi

if [ -z "$XAI_API_KEY" ]; then
    echo -e "${RED}Error: XAI_API_KEY environment variable not set.${NC}"
    echo "Usage: $0 [your_api_key]"
    echo "   or: export XAI_API_KEY=your_api_key_here && $0"
    exit 1
fi

# Base URLs
HTTP_URL="http://localhost"
HTTPS_URL="https://localhost"
API_URL="$HTTPS_URL/api/v1"

echo -e "${YELLOW}Starting xAI API tests through Nginx proxy...${NC}"

# Test 1: HTTP to HTTPS redirection
echo -e "\n${YELLOW}Test 1: HTTP to HTTPS redirection${NC}"
echo -n "Checking redirection: "
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -L --insecure $HTTP_URL/health || echo "Failed")

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ HTTP successfully redirected to HTTPS (status $HTTP_STATUS)${NC}"
else
    echo -e "${RED}✗ HTTP redirection failed with status $HTTP_STATUS${NC}"
fi

# Test 2: Health check
echo -e "\n${YELLOW}Test 2: Health check${NC}"
echo -n "Checking health endpoint: "
HEALTH_RESPONSE=$(curl -s -k $HTTPS_URL/health || echo "Failed to connect")
echo "Response: $HEALTH_RESPONSE"

if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Troubleshooting tip: Check if containers are running with 'docker-compose -f docker/docker-compose.yaml ps'"
    exit 1
fi

# Test 3: Chat completion
echo -e "\n${YELLOW}Test 3: Chat completion${NC}"
echo "Sending chat completion request..."
CHAT_RESPONSE=$(curl -s -k -X POST \
  "$API_URL/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }' || echo "Failed to connect")

if [[ $CHAT_RESPONSE == *"Failed"* ]]; then
    echo -e "${RED}✗ Request failed - connection error${NC}"
else
    echo "Response excerpt:"
    echo "$CHAT_RESPONSE" | grep -o '.*"content":"[^"]*".*' | head -50
    
    if [[ $CHAT_RESPONSE == *"choices"* ]]; then
        echo -e "${GREEN}✓ Chat completion successful${NC}"
    else
        echo -e "${RED}✗ Chat completion failed${NC}"
    fi
fi

# Test 4: Image generation
echo -e "\n${YELLOW}Test 4: Image generation${NC}"
echo "Generating image..."
IMAGE_RESPONSE=$(curl -s -k -X POST \
  "$API_URL/images/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "model": "grok-2-image"
  }' || echo "Failed to connect")

if [[ $IMAGE_RESPONSE == *"Failed"* ]]; then
    echo -e "${RED}✗ Request failed - connection error${NC}"
else
    IMAGE_URL=$(echo "$IMAGE_RESPONSE" | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "Image URL: $IMAGE_URL"
    
    if [[ $IMAGE_RESPONSE == *"data"* && $IMAGE_RESPONSE == *"url"* ]]; then
        echo -e "${GREEN}✓ Image generation successful${NC}"
    else
        echo -e "${RED}✗ Image generation failed${NC}"
    fi
fi

# Test 5: OpenAI SDK compatibility endpoint
echo -e "\n${YELLOW}Test 5: OpenAI SDK compatibility endpoint (images/generations)${NC}"
echo "Testing OpenAI SDK compatibility..."
SDK_RESPONSE=$(curl -s -k -X POST \
  "$API_URL/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "prompt": "A futuristic cityscape",
    "model": "grok-2-image"
  }' || echo "Failed to connect")

if [[ $SDK_RESPONSE == *"Failed"* ]]; then
    echo -e "${RED}✗ Request failed - connection error${NC}"
else
    SDK_URL=$(echo "$SDK_RESPONSE" | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "Image URL: $SDK_URL"
    
    if [[ $SDK_RESPONSE == *"data"* && $SDK_RESPONSE == *"url"* ]]; then
        echo -e "${GREEN}✓ OpenAI SDK compatibility endpoint successful${NC}"
    else
        echo -e "${RED}✗ OpenAI SDK compatibility endpoint failed${NC}"
    fi
fi

# Test 6: Vision analysis
echo -e "\n${YELLOW}Test 6: Vision analysis${NC}"
echo "Analyzing image..."
VISION_RESPONSE=$(curl -s -k -X POST \
  "$API_URL/vision/analyze" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-2-vision-latest",
    "image": {
      "url": "https://api.time.com/wp-content/uploads/2017/11/dogs-cats-brain-study.jpg"
    },
    "prompt": "What animals are in this image?"
  }' || echo "Failed to connect")

if [[ $VISION_RESPONSE == *"Failed"* ]]; then
    echo -e "${RED}✗ Request failed - connection error${NC}"
else
    VISION_CONTENT=$(echo "$VISION_RESPONSE" | grep -o '"content":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "Analysis: $VISION_CONTENT"
    
    if [[ $VISION_RESPONSE == *"content"* ]]; then
        echo -e "${GREEN}✓ Vision analysis successful${NC}"
    else
        echo -e "${RED}✗ Vision analysis failed${NC}"
    fi
fi

# Test 7: Test rate limiting
echo -e "\n${YELLOW}Test 7: Rate limiting test (sending 5 quick requests)${NC}"
echo "Testing rate limiting..."
for i in {1..5}; do
    RATE_STATUS=$(curl -s -k -o /dev/null -w "%{http_code}" $HTTPS_URL/health)
    echo -n "$RATE_STATUS "
    sleep 0.1
done
echo -e "\n${GREEN}✓ Rate limiting test complete${NC}"

# Final summary
echo -e "\n${YELLOW}=== Test Results Summary ===${NC}"
echo -e "${GREEN}✓ All tests completed!${NC}"
echo ""
echo "If any tests failed, check:"
echo "  - Docker containers: docker-compose -f docker/docker-compose.yaml ps"
echo "  - API logs: docker logs xai-api"
echo "  - Nginx logs: docker logs xai-nginx"
echo "  - Nginx error logs: docker exec xai-nginx cat /var/log/nginx/error.log" 