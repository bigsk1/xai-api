# API Authentication

This API supports optional Bearer token authentication via middleware. When enabled, all API endpoints (except health check and documentation) require a valid Bearer token in the `Authorization` header.

## Configuration

Authentication is controlled by two environment variables in your `.env` file:

```bash
# Enable/disable authentication (default: false)
XAI_API_AUTH=true

# The bearer token clients must provide (required if XAI_API_AUTH=true)
XAI_API_AUTH_TOKEN=your_secure_random_token_here
```

### Generating a Secure Token

Generate a cryptographically secure random token:

```bash
# Using OpenSSL (recommended)
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## Usage

### When Authentication is Disabled (XAI_API_AUTH=false)

All endpoints are accessible without authentication:

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### When Authentication is Enabled (XAI_API_AUTH=true)

All protected endpoints require a Bearer token:

```bash
curl -X POST http://localhost:8000/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_secure_random_token_here" \
  -d '{
    "model": "grok-4-1-fast-non-reasoning",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Exempt Endpoints

The following endpoints are **always accessible** without authentication:

- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI specification

## Error Responses

### Missing Authorization Header

**Status:** `401 Unauthorized`

```json
{
  "error": {
    "message": "Missing or invalid Authorization header. Expected format: 'Bearer <token>'",
    "type": "authentication_error",
    "code": "missing_authorization"
  }
}
```

**Headers:**
```
WWW-Authenticate: Bearer
```

### Invalid Token

**Status:** `401 Unauthorized`

```json
{
  "error": {
    "message": "Invalid API token",
    "type": "authentication_error",
    "code": "invalid_token"
  }
}
```

**Headers:**
```
WWW-Authenticate: Bearer
```

### Server Misconfiguration

**Status:** `500 Internal Server Error`

This occurs when `XAI_API_AUTH=true` but `XAI_API_AUTH_TOKEN` is not set.

```json
{
  "error": {
    "message": "Server authentication configuration error",
    "type": "server_error",
    "code": "auth_misconfigured"
  }
}
```

## Security Best Practices

1. **Use Strong Tokens**: Generate tokens with at least 32 bytes of entropy (64 hex characters)
2. **HTTPS Only**: In production, always use HTTPS to prevent token interception
3. **Environment Variables**: Never commit tokens to version control. Always use `.env` files
4. **Token Rotation**: Periodically rotate your API tokens
5. **Single Token**: This implementation uses a single shared token. For production with multiple clients, consider implementing per-client tokens with a database backend
6. **Rate Limiting**: The rate limiter tracks tokens separately, so each unique token gets its own rate limit quota

## Using with OpenAI SDK

When using the OpenAI Python SDK, pass the token as the `api_key` parameter:

```python
from openai import OpenAI

client = OpenAI(
    api_key="your_secure_random_token_here",  # Your XAI_API_AUTH_TOKEN
    base_url="http://localhost:8000/api/v1"
)

response = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

## Testing

A test script is provided to verify authentication is working correctly:

```bash
# Test with authentication disabled
XAI_API_AUTH=false python tests/test_auth.py

# Test with authentication enabled
XAI_API_AUTH=true XAI_API_AUTH_TOKEN=test_token_123 python tests/test_auth.py
```

## Implementation Details

The authentication is implemented as ASGI middleware in `app/core/middleware.py`:

- **Class:** `APIAuthMiddleware`
- **Order:** Runs before rate limiting and request logging
- **Performance:** Minimal overhead - simple string comparison
- **Logging:** Invalid auth attempts are logged with client IP

## Middleware Execution Order

Middlewares are executed in reverse order of registration:

1. `APIAuthMiddleware` - Authentication check (runs first if enabled)
2. `RateLimitMiddleware` - Rate limiting
3. `RequestLoggerMiddleware` - Request/response logging
4. Route handlers - Your API endpoints

## Deployment Considerations

### Development

For local development, authentication can be disabled:

```bash
XAI_API_AUTH=false
```

### Production

For production deployments, enable authentication:

```bash
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=<generated-secure-token>
```

### Reverse Proxy

If you're using a reverse proxy (Nginx, Traefik, etc.), you can:

1. Use this middleware for application-level auth
2. Use Basic Auth at the reverse proxy level (additional layer)
3. Use both for defense in depth

### Docker

In Docker deployments, pass the token via environment variables:

```yaml
# docker-compose.yml
services:
  api:
    environment:
      - XAI_API_AUTH=true
      - XAI_API_AUTH_TOKEN=${XAI_API_AUTH_TOKEN}
```

Then set `XAI_API_AUTH_TOKEN` in your host's `.env` file.

## Troubleshooting

### "Server authentication configuration error"

**Problem:** `XAI_API_AUTH=true` but `XAI_API_AUTH_TOKEN` is not set

**Solution:** Set a token in your `.env` file:
```bash
XAI_API_AUTH_TOKEN=$(openssl rand -hex 32)
```

### Authentication not working after enabling

**Problem:** Requests still work without token after setting `XAI_API_AUTH=true`

**Solution:** Restart the server to reload environment variables:
```bash
# Kill existing server (Ctrl+C)
uvicorn app.main:app --reload
```

### Token rejected despite being correct

**Problem:** Valid token returns 401

**Solution:** 
1. Check for whitespace in token (no spaces or newlines)
2. Ensure correct header format: `Authorization: Bearer <token>`
3. Check server logs for actual error message

## Future Enhancements

Potential improvements for production systems:

1. **Per-Client Tokens**: Database-backed token management with multiple API keys
2. **Token Scopes**: Limit what each token can access (read-only, specific endpoints, etc.)
3. **Token Expiration**: Time-limited tokens with refresh mechanism
4. **API Key Management UI**: Web interface for creating/revoking tokens
5. **Audit Logging**: Track all API usage by token
6. **JWT Support**: Use JSON Web Tokens for stateless auth with claims
