# Documentation Endpoint Security

## Overview

By default, the API documentation endpoints (`/docs`, `/redoc`, `/openapi.json`) are **exempt from authentication**. This document explains the security implications and how to configure them.

## What's Exempt by Default

| Endpoint | Purpose | Exempt? |
|----------|---------|---------|
| `/health` | Health check | ✅ Always |
| `/docs` | Swagger UI (interactive docs) | ✅ Configurable |
| `/redoc` | ReDoc UI (alternative docs) | ✅ Configurable |
| `/openapi.json` | OpenAPI specification | ✅ Configurable |

## Security Implications

### What Documentation Endpoints Reveal

When docs are public (exempt from auth), anyone can access:
- ✅ API endpoint paths (`/api/v1/chat/completions`, etc.)
- ✅ Request/response schemas
- ✅ Parameter names and types
- ✅ Model definitions
- ✅ Available tools and functions

### What They DON'T Reveal

Documentation endpoints **cannot**:
- ❌ Execute API calls without authentication
- ❌ Access your data
- ❌ See your API keys or tokens
- ❌ Bypass authentication on actual API endpoints

### The "Try It Out" Button

The Swagger UI at `/docs` has interactive "Try it out" buttons:

**Important:** These buttons **still require authentication!**

When someone clicks "Try it out" and executes a request:
1. Request goes through normal authentication middleware
2. Without valid token → Returns 401 Unauthorized
3. With valid token → Request succeeds

**Example in Swagger UI:**
```
POST /api/v1/chat/completions
[Try it out] button
  ↓
User enters request body
  ↓
Clicks "Execute"
  ↓
Request sent WITHOUT token (if not provided)
  ↓
Middleware checks authentication
  ↓
Returns: 401 Unauthorized ❌
```

## Configuration Options

### Option 1: Public Docs (Default - Good for Public APIs)

**Use when:**
- You want developers to easily explore your API
- You're using Traefik BasicAuth to protect the entire service
- Your API is meant to be publicly documented
- You don't consider API structure sensitive

**Configuration:**
```bash
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=your_token
XAI_API_AUTH_EXCLUDE_DOCS=true  # Docs are public
```

**Access:**
- `https://api.domain.com/docs` - ✅ No auth needed
- `https://api.domain.com/api/v1/chat/completions` - 🔒 Requires token

**Pros:**
- Easy for developers to discover API
- Standard practice for public APIs
- Can test endpoints right in browser (if they provide token)

**Cons:**
- Reveals API structure
- Shows all available endpoints
- Could give attackers reconnaissance information

### Option 2: Protected Docs (Recommended for Private APIs)

**Use when:**
- Your API is internal/private
- You don't want API structure publicly visible
- Maximum security is priority
- You have a small known set of users

**Configuration:**
```bash
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=your_token
XAI_API_AUTH_EXCLUDE_DOCS=false  # Docs require auth
```

**Access:**
- `https://api.domain.com/docs` - 🔒 Requires token
- `https://api.domain.com/api/v1/chat/completions` - 🔒 Requires token

**How to access docs with token:**

**Method 1: Use Swagger UI's Authorize Button**
1. Go to `/docs`
2. Get 401 error in browser
3. If using custom header, you'll need Method 2

**Method 2: Browser Extension (Recommended)**

Install a browser extension that adds custom headers:
- Chrome: "ModHeader" or "Simple Modify Headers"
- Firefox: "Modify Header Value"

Configure it to add:
- If using `Authorization` header: `Authorization: Bearer your_token`
- If using custom header: `X-API-Token: your_token`

**Method 3: Local Proxy**

Run a local proxy that injects the auth header:

```python
# auth_proxy.py
from flask import Flask, request, Response
import requests

app = Flask(__name__)
TOKEN = "your_token_here"
API_BASE = "http://localhost:8000"
HEADER_NAME = "X-API-Token"  # or "Authorization"

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(path):
    headers = dict(request.headers)
    if HEADER_NAME == "Authorization":
        headers['Authorization'] = f'Bearer {TOKEN}'
    else:
        headers[HEADER_NAME] = TOKEN
    
    resp = requests.request(
        method=request.method,
        url=f"{API_BASE}/{path}",
        headers=headers,
        data=request.get_data(),
        allow_redirects=False
    )
    return Response(resp.content, resp.status_code, resp.raw.headers.items())

if __name__ == '__main__':
    app.run(port=8080)
```

Then access docs at `http://localhost:8080/docs`

### Option 3: Traefik BasicAuth for Docs

**Use when:**
- You want docs accessible but not completely public
- You're using Coolify with Traefik
- You want browser-friendly authentication for docs

**Configuration:**
```bash
# App auth for API endpoints
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=api_token_here
XAI_API_AUTH_HEADER=X-API-Token
XAI_API_AUTH_EXCLUDE_DOCS=true  # Docs exempt from app auth

# Traefik BasicAuth in Coolify
# (Enable in Coolify UI)
```

**Result:**
- All endpoints protected by Traefik BasicAuth (including docs)
- API endpoints additionally require `X-API-Token`
- Docs accessible with just BasicAuth
- Browser prompts for username/password

**Access:**
```bash
# Access docs - only BasicAuth needed
curl -u "admin:password" https://api.domain.com/docs

# Use API - needs both
curl -u "admin:password" \
  -H "X-API-Token: api_token" \
  https://api.domain.com/api/v1/chat/completions
```

## Security Recommendations

### For Public APIs
```bash
XAI_API_AUTH=true
XAI_API_AUTH_EXCLUDE_DOCS=true  # Public docs
```
**+ Use Traefik BasicAuth for additional protection**

### For Private/Internal APIs
```bash
XAI_API_AUTH=true
XAI_API_AUTH_EXCLUDE_DOCS=false  # Protected docs
```

### For Maximum Security
```bash
# App-level auth
XAI_API_AUTH=true
XAI_API_AUTH_HEADER=X-API-Token
XAI_API_AUTH_EXCLUDE_DOCS=false  # Docs require token

# + Traefik BasicAuth in Coolify
# + IP whitelisting at firewall level
# + Rate limiting (already enabled)
```

## Testing

### Test Public Docs

```bash
# Start server with public docs
XAI_API_AUTH=true \
XAI_API_AUTH_TOKEN=test123 \
XAI_API_AUTH_EXCLUDE_DOCS=true \
uvicorn app.main:app --reload

# Access docs (should work)
curl http://localhost:8000/docs
# Returns: Swagger UI HTML ✅

# Access API without token (should fail)
curl http://localhost:8000/api/v1/chat/completions
# Returns: 401 Unauthorized ❌
```

### Test Protected Docs

```bash
# Start server with protected docs
XAI_API_AUTH=true \
XAI_API_AUTH_TOKEN=test123 \
XAI_API_AUTH_EXCLUDE_DOCS=false \
uvicorn app.main:app --reload

# Access docs without token (should fail)
curl http://localhost:8000/docs
# Returns: 401 Unauthorized ❌

# Access docs with token (should work)
curl -H "Authorization: Bearer test123" http://localhost:8000/docs
# Returns: Swagger UI HTML ✅
```

## FAQ

### Q: Can someone use the API through /docs without a token?

**A: No.** The "Try it out" buttons in Swagger UI send requests that still go through authentication middleware. Without a valid token, they get 401 errors.

### Q: Does public docs expose my API key?

**A: No.** Documentation endpoints never reveal your `XAI_API_KEY` or `XAI_API_AUTH_TOKEN`. They only show the API structure.

### Q: Should I protect docs in production?

**A: It depends:**
- **Public API** (like Stripe, Twilio) → Public docs are standard
- **Internal API** (company private) → Protect docs
- **Personal project** → Use BasicAuth at minimum

### Q: What about /health endpoint?

**A: Always public.** The health endpoint is always exempt from authentication because:
- Load balancers need it for health checks
- Monitoring tools need it without auth
- It reveals no sensitive information
- Standard practice for all APIs

### Q: Can I protect /health too?

**A: Not recommended.** If you absolutely need to:

1. Remove `/health` from exempt paths in middleware
2. Configure your load balancer to use authenticated health checks
3. Be aware this complicates deployment

## Summary Table

| Configuration | Docs Access | API Access | Use Case |
|--------------|-------------|------------|----------|
| `EXCLUDE_DOCS=true` | 🌐 Public | 🔒 Auth required | Public APIs, with Traefik BasicAuth |
| `EXCLUDE_DOCS=false` | 🔒 Auth required | 🔒 Auth required | Private/internal APIs |
| With Traefik BasicAuth | 🔒 BasicAuth | 🔒 BasicAuth + Token | Maximum security |

## Best Practice

**Recommended production setup:**

```env
# In Coolify
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=secure-random-token
XAI_API_AUTH_HEADER=X-API-Token
XAI_API_AUTH_EXCLUDE_DOCS=true  # Docs still accessible

# Enable Traefik BasicAuth in Coolify UI
# This protects EVERYTHING including docs
```

**Result:**
- Docs protected by BasicAuth (browser-friendly)
- API endpoints require BasicAuth + Token
- Defense in depth
- Easy for authorized developers to explore
