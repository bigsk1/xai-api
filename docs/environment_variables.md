# Environment Variables Reference

Complete list of all environment variables for the xAI API proxy.

## Required

| Variable | Description | Example |
|----------|-------------|---------|
| `XAI_API_KEY` | Your xAI API key | `xai-your-key-here` |

## Optional - API Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `XAI_API_BASE` | `https://api.x.ai/v1` | xAI API base URL |
| `DEFAULT_CHAT_MODEL` | `grok-4-1-fast-non-reasoning` | Default chat model |
| `DEFAULT_IMAGE_GEN_MODEL` | `grok-2-image` | Default image generation model |
| `DEFAULT_VISION_MODEL` | `grok-2-vision-latest` | Default vision/image analysis model |

## Optional - Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `API_RATE_LIMIT` | `100` | Maximum requests per period |
| `API_RATE_LIMIT_PERIOD` | `3600` | Rate limit window in seconds (3600 = 1 hour) |

## Optional - Tools Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `XAI_TOOLS_ENABLED` | `false` | Enable client-side function calling (tools you execute) |
| `XAI_NATIVE_TOOLS_ENABLED` | `false` | Enable xAI native agentic tools (web_search, x_search, code_execution) |

## Optional - Tool Validation Limits

These limits apply when `XAI_TOOLS_ENABLED=true` to prevent abuse of client-side function calling:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_TOOLS_PER_REQUEST` | `20` | Maximum number of functions per request |
| `MAX_FUNCTION_NAME_LENGTH` | `64` | Maximum characters in function name |
| `MAX_FUNCTION_DESCRIPTION_LENGTH` | `1024` | Maximum characters in function description |
| `MAX_PARAMETER_DEPTH` | `5` | Maximum nesting depth for parameters (prevents deeply nested JSON schemas) |

## Optional - Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `XAI_API_AUTH` | `false` | Enable API token authentication |
| `XAI_API_AUTH_TOKEN` | ` ` (empty) | Bearer token for API access (generate with `openssl rand -hex 32`) |
| `XAI_API_AUTH_HEADER` | `Authorization` | Header to check for token: `Authorization` (Bearer) or `X-API-Token` (custom) |
| `XAI_API_AUTH_EXCLUDE_DOCS` | `true` | Exempt `/docs`, `/redoc`, `/openapi.json` from authentication |

## Example `.env` File

```bash
# Required
XAI_API_KEY=xai-your-key-here

# Optional: API Configuration
XAI_API_BASE=https://api.x.ai/v1
DEFAULT_CHAT_MODEL=grok-4-1-fast-non-reasoning
DEFAULT_IMAGE_GEN_MODEL=grok-2-image
DEFAULT_VISION_MODEL=grok-2-vision-latest

# Optional: Rate Limiting
API_RATE_LIMIT=100
API_RATE_LIMIT_PERIOD=3600

# Optional: Tools (both disabled by default for security)
XAI_TOOLS_ENABLED=false              # Client-side function calling
XAI_NATIVE_TOOLS_ENABLED=false       # xAI native tools (web/X search, code exec)

# Optional: Tool Validation Limits (commented out = use defaults)
# MAX_TOOLS_PER_REQUEST=20
# MAX_FUNCTION_NAME_LENGTH=64
# MAX_FUNCTION_DESCRIPTION_LENGTH=1024
# MAX_PARAMETER_DEPTH=5

# Optional: API Authentication (disabled by default)
XAI_API_AUTH=false
XAI_API_AUTH_TOKEN=
# Header: "Authorization" (Bearer token) or "X-API-Token" (custom, for use with Traefik BasicAuth)
XAI_API_AUTH_HEADER=Authorization
# Exempt docs from auth: true (docs public) or false (docs require token)
XAI_API_AUTH_EXCLUDE_DOCS=true
```

## Production Example (Coolify)

For Coolify deployment with maximum security:

```bash
# Required
XAI_API_KEY=xai-your-actual-key

# Recommended for production
XAI_API_AUTH=true
XAI_API_AUTH_TOKEN=generated-secure-token-here
XAI_API_AUTH_HEADER=X-API-Token  # Use custom header
XAI_API_AUTH_EXCLUDE_DOCS=true   # Docs protected by Traefik BasicAuth

# Enable tools if needed
XAI_TOOLS_ENABLED=true
XAI_NATIVE_TOOLS_ENABLED=true

# Use defaults for validation limits (secure)
# MAX_TOOLS_PER_REQUEST=20
# MAX_FUNCTION_NAME_LENGTH=64
# MAX_FUNCTION_DESCRIPTION_LENGTH=1024
# MAX_PARAMETER_DEPTH=5

# Also enable Traefik BasicAuth in Coolify UI for defense in depth
```

## Variable Categories

### Security Variables
- `XAI_API_AUTH` - Enable/disable authentication
- `XAI_API_AUTH_TOKEN` - API access token
- `XAI_API_AUTH_HEADER` - Authentication header name
- `XAI_API_AUTH_EXCLUDE_DOCS` - Docs access control
- `MAX_*` - Tool validation limits

### Feature Flags
- `XAI_TOOLS_ENABLED` - Client-side functions
- `XAI_NATIVE_TOOLS_ENABLED` - xAI native tools

### API Configuration
- `XAI_API_KEY` - xAI credentials
- `XAI_API_BASE` - API endpoint
- `DEFAULT_*_MODEL` - Model defaults

### Operational
- `API_RATE_LIMIT` - Rate limiting
- `API_RATE_LIMIT_PERIOD` - Rate limit window

## Docker Compose Usage

All variables are passed through docker-compose with sensible defaults:

```yaml
environment:
  - XAI_API_KEY=${XAI_API_KEY}
  - XAI_API_BASE=${XAI_API_BASE:-https://api.x.ai/v1}
  - DEFAULT_CHAT_MODEL=${DEFAULT_CHAT_MODEL:-grok-4-1-fast-non-reasoning}
  # ... etc
```

Variables not set in your environment will use the defaults specified after `:-`.

## Security Best Practices

1. **Never commit `.env` files** - Always in `.gitignore`
2. **Use strong tokens** - `openssl rand -hex 32` for `XAI_API_AUTH_TOKEN`
3. **Disable tools by default** - Only enable when needed
4. **Use custom header in production** - `X-API-Token` with Traefik BasicAuth
5. **Keep validation limits** - Don't increase unless necessary
6. **Rotate tokens regularly** - Change `XAI_API_AUTH_TOKEN` periodically

## Troubleshooting

### "XAI_API_AUTH is enabled but XAI_API_AUTH_TOKEN is not set"
**Solution:** Set `XAI_API_AUTH_TOKEN` or disable auth with `XAI_API_AUTH=false`

### "Tool calling is disabled on this server"
**Solution:** Set `XAI_TOOLS_ENABLED=true` in `.env` and restart server

### "Invalid tool format"
**Solution:** Check tool validation limits (`MAX_*` variables) and ensure your tools comply

### Server doesn't see environment changes
**Solution:** Restart the server after changing `.env` file

## References

- See `.env.example` for a complete template
- See `docker/docker-compose.yaml` for Docker configuration
- See `docs/authentication.md` for auth setup
- See `docs/dual_authentication.md` for Traefik + token auth
- See `docs/function_calling.md` for tools configuration
