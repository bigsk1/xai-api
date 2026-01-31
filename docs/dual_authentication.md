# Dual Authentication: Traefik BasicAuth + API Token

## The Problem

Both Traefik BasicAuth and Bearer tokens use the `Authorization` HTTP header, which means **you cannot use both simultaneously** on the same request.

```
Authorization: Basic <base64>     # Traefik BasicAuth
Authorization: Bearer <token>     # API Bearer token
```

A single HTTP request can only have one `Authorization` header value.

## The Solution: Custom Header

Use a **custom header** for the API token while Traefik handles BasicAuth on the `Authorization` header.

### Configuration

Set the API to check a custom header instead of `Authorization`:

```bash
# .env
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=your_secure_token_here
XAI_API_AUTH_HEADER=X-API-Token    # Custom header instead of Authorization
```

Now requests can carry **both** authentication layers:

```bash
curl -X POST https://api.yourdomain.com/api/v1/chat/completions \
  -u "admin:traefik_password" \                    # Traefik BasicAuth (uses Authorization)
  -H "X-API-Token: your_secure_token_here" \       # App-level auth (custom header)
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Authentication Flow

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ Authorization: Basic admin:password
     │ X-API-Token: app_token_123
     │
     ▼
┌─────────────┐
│   Traefik   │  ◄─── Layer 1: Checks Authorization header
└──────┬──────┘       (BasicAuth validation)
       │
       │ ✅ BasicAuth passed
       │ X-API-Token: app_token_123  (forwarded)
       │
       ▼
┌──────────────┐
│ APIAuthMW    │  ◄─── Layer 2: Checks X-API-Token header
└──────┬───────┘       (Token validation)
       │
       │ ✅ Token valid
       │
       ▼
┌──────────────┐
│  API Handler │  ◄─── Request processed
└──────────────┘
```

## Configuration Options

### Option 1: Bearer Token Only (No Traefik BasicAuth)

**Use when:** You want simple API token authentication

```bash
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=your_token
XAI_API_AUTH_HEADER=Authorization  # Default
```

**Request:**
```bash
curl -X POST https://api.yourdomain.com/api/v1/chat/completions \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{"model": "grok-4-1-fast-non-reasoning", "messages": [...]}'
```

### Option 2: Custom Header Only (No Traefik BasicAuth)

**Use when:** You prefer a custom header name

```bash
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=your_token
XAI_API_AUTH_HEADER=X-API-Token
```

**Request:**
```bash
curl -X POST https://api.yourdomain.com/api/v1/chat/completions \
  -H "X-API-Token: your_token" \
  -H "Content-Type: application/json" \
  -d '{"model": "grok-4-1-fast-non-reasoning", "messages": [...]}'
```

### Option 3: Dual Auth (Traefik BasicAuth + Custom Header)

**Use when:** Maximum security with two authentication layers ✅ **Recommended for production**

```bash
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=your_token
XAI_API_AUTH_HEADER=X-API-Token  # Custom header to avoid conflict
```

**Coolify/Traefik setup:**
- Enable BasicAuth in Coolify UI for the service
- Set username/password for BasicAuth

**Request:**
```bash
curl -X POST https://api.yourdomain.com/api/v1/chat/completions \
  -u "admin:basicauth_password" \              # Traefik layer
  -H "X-API-Token: your_token" \               # App layer
  -H "Content-Type: application/json" \
  -d '{"model": "grok-4-1-fast-non-reasoning", "messages": [...]}'
```

### Option 4: Traefik BasicAuth Only (No App Auth)

**Use when:** BasicAuth is sufficient

```bash
XAI_API_AUTH=false  # Disable app-level auth
```

**Request:**
```bash
curl -X POST https://api.yourdomain.com/api/v1/chat/completions \
  -u "admin:basicauth_password" \
  -H "Content-Type: application/json" \
  -d '{"model": "grok-4-1-fast-non-reasoning", "messages": [...]}'
```

## Coolify Deployment with Dual Auth

### Step 1: Set Environment Variables

In Coolify service settings:

```env
XAI_API_KEY=xai-your-actual-key
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=your-secure-app-token
XAI_API_AUTH_HEADER=X-API-Token
```

### Step 2: Enable Traefik BasicAuth

In Coolify:
1. Go to your service settings
2. Find "Basic Authentication" section
3. Enable it
4. Set username and password
5. Save and redeploy

Coolify will automatically add Traefik labels:
```yaml
traefik.http.middlewares.xai-auth.basicauth.users=admin:$apr1$...
traefik.http.routers.xai-api.middlewares=xai-auth
```

### Step 3: Test

```bash
# Test with both auth layers
curl -X POST https://your-domain.com/api/v1/chat/completions \
  -u "admin:your_basicauth_password" \
  -H "X-API-Token: your-secure-app-token" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Health check (exempt from both)
curl https://your-domain.com/health
```

## Using with OpenAI SDK

The OpenAI SDK only supports the `Authorization` header for API keys. When using dual auth:

### Option A: Use Custom Header with Requests Library

```python
import requests

# Dual auth requires using requests library directly
response = requests.post(
    "https://your-domain.com/api/v1/chat/completions",
    auth=("admin", "basicauth_password"),  # BasicAuth
    headers={
        "X-API-Token": "your_app_token",   # App token
        "Content-Type": "application/json"
    },
    json={
        "model": "grok-4-1-fast-non-reasoning",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
```

### Option B: Proxy with Auth Injection

Create a local proxy that injects both auth headers:

```python
from flask import Flask, request, Response
import requests

app = Flask(__name__)

BASIC_AUTH = ("admin", "basicauth_password")
API_TOKEN = "your_app_token"
API_BASE = "https://your-domain.com"

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    headers = dict(request.headers)
    headers['X-API-Token'] = API_TOKEN
    
    resp = requests.request(
        method=request.method,
        url=f"{API_BASE}/{path}",
        auth=BASIC_AUTH,
        headers=headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )
    
    return Response(resp.content, resp.status_code, resp.headers.items())

if __name__ == '__main__':
    app.run(port=8080)
```

Then use OpenAI SDK with local proxy:

```python
from openai import OpenAI

client = OpenAI(
    api_key="ignored",  # Proxy injects real auth
    base_url="http://localhost:8080/api/v1"
)

response = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Security Comparison

| Configuration | Security Level | Use Case |
|--------------|----------------|----------|
| No auth | ⚠️ Low | Development only |
| BasicAuth only | 🟡 Medium | Simple deployments |
| Bearer token only | 🟡 Medium | API-only access |
| Custom header only | 🟡 Medium | API-only access |
| **Dual auth** | ✅ **High** | **Production** |

## Benefits of Dual Auth

1. **Defense in Depth**: Two independent authentication layers
2. **Different Threat Models**:
   - BasicAuth: Protects entire service (broad protection)
   - API Token: Per-client tracking and rate limiting
3. **Flexibility**: Can revoke BasicAuth OR API token independently
4. **Audit Trail**: Track which client (BasicAuth user) + which token
5. **Rate Limiting**: Each API token gets separate rate limit quota

## Testing

### Test Script

The included test script supports both modes:

```bash
# Test with Authorization header (default)
XAI_API_AUTH=true \
XAI_API_AUTH_TOKEN=test123 \
XAI_API_AUTH_HEADER=Authorization \
python tests/test_auth.py

# Test with custom header
XAI_API_AUTH=true \
XAI_API_AUTH_TOKEN=test123 \
XAI_API_AUTH_HEADER=X-API-Token \
python tests/test_auth.py
```

### Manual Testing

```bash
# Test custom header without BasicAuth
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "X-API-Token: test123" \
  -H "Content-Type: application/json" \
  -d '{"model": "grok-4-1-fast-non-reasoning", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}'

# Test dual auth (simulated)
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -u "admin:password" \
  -H "X-API-Token: test123" \
  -H "Content-Type: application/json" \
  -d '{"model": "grok-4-1-fast-non-reasoning", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}'
```

## Error Messages

### Custom Header Mode

**Missing custom header:**
```json
{
  "error": {
    "message": "Missing X-API-Token header. Please provide your API token.",
    "type": "authentication_error",
    "code": "missing_token_header"
  }
}
```

**Invalid token:**
```json
{
  "error": {
    "message": "Invalid API token",
    "type": "authentication_error",
    "code": "invalid_token"
  }
}
```

## Troubleshooting

### Problem: 401 even with valid token

**Cause:** Using wrong header name

**Solution:** Check `XAI_API_AUTH_HEADER` setting
```bash
# If XAI_API_AUTH_HEADER=X-API-Token, use:
-H "X-API-Token: your_token"

# NOT:
-H "Authorization: Bearer your_token"
```

### Problem: Traefik returns 401 before app sees request

**Cause:** BasicAuth failing at Traefik layer

**Solution:** Check Traefik BasicAuth credentials
```bash
# Test just BasicAuth
curl -u "admin:password" https://your-domain.com/health
```

### Problem: OpenAI SDK doesn't work with dual auth

**Cause:** SDK only supports Authorization header

**Solution:** Use Option B (proxy) from "Using with OpenAI SDK" section above

## Best Practices

1. **Use dual auth in production** for maximum security
2. **Generate strong tokens**: `openssl rand -hex 32`
3. **Different credentials**: Don't reuse BasicAuth password as API token
4. **HTTPS only**: Never use authentication over plain HTTP
5. **Rotate tokens**: Change API token periodically
6. **Monitor logs**: Watch for failed auth attempts
7. **Rate limiting**: Enable rate limiting alongside auth

## Summary

**For production with Coolify + Traefik:**

```env
# In Coolify environment variables
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=generated-secure-token-here
XAI_API_AUTH_HEADER=X-API-Token

# Enable BasicAuth in Coolify UI
# Username: admin
# Password: different-secure-password
```

This gives you **two-factor authentication** at the infrastructure level:
1. Something you know (BasicAuth username/password)
2. Something you have (API token)

Both must be valid for request to succeed. ✅
