# Stateful Conversations with Responses API

This guide shows how to use the Responses API for efficient, stateful conversations.

## Why Use Responses API for Chat?

The Responses API is **better than Chat Completions for regular chatting** because:

✅ **Stateful**: Use `previous_response_id` instead of resending full history  
✅ **Cheaper**: Automatic caching reduces token costs  
✅ **Faster**: Cached conversations respond quicker  
✅ **30-day storage**: Conversations stored server-side  
✅ **Retrieve/Delete**: Manage conversation history  

## Basic Chat (No Tools)

### Simple Question & Answer

```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "input": [
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

**Response:**
```json
{
  "id": "resp-abc123",
  "output": [{
    "content": [{
      "type": "output_text",
      "text": "Paris is the capital of France."
    }],
    "role": "assistant",
    "type": "message"
  }],
  "usage": {
    "input_tokens": 175,
    "output_tokens": 10,
    "total_tokens": 185
  }
}
```

Save the `id` for continuing the conversation!

---

## Method 1: Chaining with `previous_response_id` (Recommended)

This is the **most efficient** method - only sends new messages, xAI maintains full history.

### First Message

```bash
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "input": [
      {
        "role": "system",
        "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
      },
      {
        "role": "user",
        "content": "What is the meaning of life, the universe, and everything?"
      }
    ],
    "store": true
  }')

# Extract the response ID
RESPONSE_ID=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Response ID: $RESPONSE_ID"
```

### Follow-up Message (Uses Conversation Context)

```bash
curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d "{
    \"model\": \"grok-4-1-fast-non-reasoning\",
    \"previous_response_id\": \"$RESPONSE_ID\",
    \"input\": [
      {\"role\": \"user\", \"content\": \"What is the meaning of 42?\"}
    ],
    \"store\": true
  }"
```

Grok knows the context from the previous message!

**Token Usage Comparison:**

| Method | Input Tokens | Output Tokens | Total | Cost |
|--------|--------------|---------------|-------|------|
| First message | 175 | 120 | 295 | 100% |
| Follow-up (with previous_response_id) | ~50 | 80 | 130 | **44%** |
| Follow-up (resending full history) | 295 | 80 | 375 | 127% |

**Savings: ~56% on follow-up messages!**

---

## Method 2: Adding Encrypted Reasoning Content

For reasoning models, you can include encrypted thinking content in follow-up messages.

### First Message with Reasoning

```bash
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d '{
    "model": "grok-4",
    "input": [
      {
        "role": "system",
        "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
      },
      {
        "role": "user",
        "content": "What is the meaning of life, the universe, and everything?"
      }
    ],
    "include": ["reasoning.encrypted_content"]
  }')

echo $RESPONSE | python3 -m json.tool > first_response.json
```

### Follow-up with Output History

```bash
# Read the output from the previous response
OUTPUT=$(cat first_response.json | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)['output']))")

curl -X POST http://localhost:8000/api/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $XAI_API_KEY" \
  -d "{
    \"model\": \"grok-4\",
    \"input\": $(echo $OUTPUT | sed 's/$/,/'),
      {\"role\": \"user\", \"content\": \"What is the meaning of 42?\"}
    ],
    \"include\": [\"reasoning.encrypted_content\"]
  }"
```

---

## Retrieving Previous Responses

If you have a response ID, retrieve the full conversation:

```bash
curl -X GET http://localhost:8000/api/v1/responses/$RESPONSE_ID \
  -H "Authorization: Bearer $XAI_API_KEY"
```

**Use cases:**
- Resume conversation from a different session
- Review conversation history
- Extract information from past responses
- Audit tool usage and citations

**Response:**
```json
{
  "id": "resp-abc123",
  "object": "response",
  "created": 1769847310,
  "model": "grok-4-1-fast-non-reasoning",
  "output": [...],
  "usage": {...},
  "store": true
}
```

---

## Deleting Responses

Clean up stored conversations:

```bash
curl -X DELETE http://localhost:8000/api/v1/responses/$RESPONSE_ID \
  -H "Authorization: Bearer $XAI_API_KEY"
```

**Response:**
```json
{
  "id": "resp-abc123",
  "deleted": true,
  "object": "response.deleted"
}
```

**When to delete:**
- Conversation contains sensitive information
- Testing/development cleanup
- Managing storage limits
- Privacy compliance

**Important:** Once deleted, the response cannot be retrieved or used with `previous_response_id`.

---

## Complete Python Example

```python
import os
import requests

API_BASE = "http://localhost:8000/api/v1"
XAI_API_KEY = os.getenv("XAI_API_KEY")

class GrokChat:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {XAI_API_KEY}"
        }
        self.conversation_id = None
    
    def send(self, message, system_prompt=None):
        """Send a message and maintain conversation state."""
        
        # First message includes system prompt
        if self.conversation_id is None and system_prompt:
            data = {
                "model": "grok-4-1-fast-non-reasoning",
                "input": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "store": True
            }
        # Follow-up messages use previous_response_id
        elif self.conversation_id:
            data = {
                "model": "grok-4-1-fast-non-reasoning",
                "previous_response_id": self.conversation_id,
                "input": [
                    {"role": "user", "content": message}
                ],
                "store": True
            }
        # First message without system prompt
        else:
            data = {
                "model": "grok-4-1-fast-non-reasoning",
                "input": [
                    {"role": "user", "content": message}
                ],
                "store": True
            }
        
        response = requests.post(
            f"{API_BASE}/responses",
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        
        # Save conversation ID for next message
        self.conversation_id = result["id"]
        
        # Extract the text response
        text = result["output"][-1]["content"][0]["text"]
        
        return {
            "text": text,
            "id": result["id"],
            "usage": result["usage"]
        }
    
    def retrieve(self, response_id=None):
        """Retrieve a previous response."""
        rid = response_id or self.conversation_id
        if not rid:
            raise ValueError("No response ID to retrieve")
        
        response = requests.get(
            f"{API_BASE}/responses/{rid}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def delete(self, response_id=None):
        """Delete a response from server."""
        rid = response_id or self.conversation_id
        if not rid:
            raise ValueError("No response ID to delete")
        
        response = requests.delete(
            f"{API_BASE}/responses/{rid}",
            headers=self.headers
        )
        response.raise_for_status()
        
        # Clear conversation ID if deleting current conversation
        if rid == self.conversation_id:
            self.conversation_id = None
        
        return response.json()

# Usage
chat = GrokChat()

# First message
response = chat.send(
    "What is the meaning of life?",
    system_prompt="You are a philosophical AI assistant."
)
print(f"Grok: {response['text']}")
print(f"Tokens: {response['usage']['total_tokens']}")

# Follow-up (automatically uses previous_response_id)
response = chat.send("Can you elaborate on that?")
print(f"Grok: {response['text']}")
print(f"Tokens: {response['usage']['total_tokens']}")

# Another follow-up
response = chat.send("What are some philosophical perspectives on this?")
print(f"Grok: {response['text']}")
print(f"Tokens: {response['usage']['total_tokens']}")

# Retrieve conversation history
history = chat.retrieve()
print(f"Conversation has {len(history['output'])} messages")

# Clean up
chat.delete()
print("Conversation deleted")
```

---

## JavaScript/TypeScript Example

```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';
const XAI_API_KEY = process.env.XAI_API_KEY;

class GrokChat {
    constructor() {
        this.conversationId = null;
        this.headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${XAI_API_KEY}`
        };
    }

    async send(message, systemPrompt = null) {
        let data;

        // First message with system prompt
        if (!this.conversationId && systemPrompt) {
            data = {
                model: 'grok-4-1-fast-non-reasoning',
                input: [
                    { role: 'system', content: systemPrompt },
                    { role: 'user', content: message }
                ],
                store: true
            };
        }
        // Follow-up message
        else if (this.conversationId) {
            data = {
                model: 'grok-4-1-fast-non-reasoning',
                previous_response_id: this.conversationId,
                input: [
                    { role: 'user', content: message }
                ],
                store: true
            };
        }
        // First message without system prompt
        else {
            data = {
                model: 'grok-4-1-fast-non-reasoning',
                input: [
                    { role: 'user', content: message }
                ],
                store: true
            };
        }

        const response = await axios.post(
            `${API_BASE}/responses`,
            data,
            { headers: this.headers }
        );

        // Save conversation ID
        this.conversationId = response.data.id;

        // Extract text
        const text = response.data.output[response.data.output.length - 1]
            .content[0].text;

        return {
            text,
            id: response.data.id,
            usage: response.data.usage
        };
    }

    async retrieve(responseId = null) {
        const rid = responseId || this.conversationId;
        if (!rid) throw new Error('No response ID to retrieve');

        const response = await axios.get(
            `${API_BASE}/responses/${rid}`,
            { headers: this.headers }
        );

        return response.data;
    }

    async delete(responseId = null) {
        const rid = responseId || this.conversationId;
        if (!rid) throw new Error('No response ID to delete');

        const response = await axios.delete(
            `${API_BASE}/responses/${rid}`,
            { headers: this.headers }
        );

        if (rid === this.conversationId) {
            this.conversationId = null;
        }

        return response.data;
    }
}

// Usage
const chat = new GrokChat();

const response1 = await chat.send(
    'What is the meaning of life?',
    'You are a philosophical AI assistant.'
);
console.log(`Grok: ${response1.text}`);
console.log(`Tokens: ${response1.usage.total_tokens}`);

const response2 = await chat.send('Can you elaborate?');
console.log(`Grok: ${response2.text}`);
console.log(`Tokens: ${response2.usage.total_tokens}`);

// Clean up
await chat.delete();
console.log('Conversation deleted');
```

---

## Best Practices

### 1. Always Enable Storage for Multi-turn Chats

```json
{
  "store": true  // Required for previous_response_id to work
}
```

### 2. Save Response IDs

```python
# Save to database, session, or local storage
conversation_id = response["id"]
```

### 3. Handle Token Limits

```python
# Monitor token usage
if response["usage"]["total_tokens"] > 100000:
    # Start new conversation or summarize
    chat.delete()
    chat.conversation_id = None
```

### 4. Clean Up Test Conversations

```python
# Delete test conversations
if IS_DEVELOPMENT:
    chat.delete()
```

### 5. Error Handling

```python
try:
    response = chat.send("Hello")
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        # Response expired or deleted, start new conversation
        chat.conversation_id = None
        response = chat.send("Hello")
    else:
        raise
```

---

## Comparison: Chat Completions vs Responses API

| Feature | Chat Completions | Responses API |
|---------|-----------------|---------------|
| **State Management** | Stateless | Stateful |
| **History** | Resend every time | Use previous_response_id |
| **Storage** | Client-side | Server-side (30 days) |
| **Token Cost** | Full history every time | Cached after first message |
| **Retrieve** | ❌ | ✅ |
| **Delete** | ❌ | ✅ |
| **Native Tools** | ❌ | ✅ (web, X, code) |
| **Citations** | ❌ | ✅ |
| **Best For** | Single questions, custom functions | Multi-turn chat, research, agents |

---

## Summary

✅ **For Regular Chat**: Use Responses API with `previous_response_id`  
✅ **Token Savings**: ~56% on follow-up messages  
✅ **Manage History**: Retrieve and delete as needed  
✅ **30-Day Storage**: Conversations persist server-side  
✅ **All Features Work**: Tools, reasoning, citations, etc.  

The Responses API is the modern, recommended way to build conversational applications with Grok!
