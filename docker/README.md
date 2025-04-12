# Docker Setup for xAI API

This directory contains the Docker configuration for running the xAI API service in containers.

## Prerequisites

- Docker and Docker Compose installed on your system
- xAI API key

## Security Features

This Docker setup includes several security best practices:

- **Non-root user**: The container runs as a non-privileged user (UID 1001)
- **Read-only filesystem**: The container's filesystem is mounted as read-only
- **No new privileges**: Prevents privilege escalation
- **Minimal base image**: Uses Python slim to reduce attack surface
- **Health checks**: Regular health monitoring
- **Temporary filesystem**: Uses tmpfs for temporary files
- **Nginx reverse proxy**: Provides additional security layer with SSL and security headers
- **Rate limiting**: Nginx configuration limits request rates to prevent abuse

## Configuration

1. Create a `.env` file in the project root with your API key:

```
XAI_API_KEY=your_xai_api_key_here
```

You can also customize other environment variables as needed (see `.env.example` for all options).

## SSL Certificates

For development, generate self-signed SSL certificates:

```bash
cd docker/nginx/ssl
./generate-self-signed-cert.sh
```

For production, replace the certificates in `docker/nginx/ssl/` with proper ones from a trusted CA.

## Basic Authentication

The Nginx configuration includes support for HTTP Basic Authentication. By default, this is commented out. To enable it:

1. Edit `docker/nginx/conf.d/default.conf` and uncomment the `auth_basic` lines
2. Update the credentials in `docker/nginx/.htpasswd` for production use:

```bash
htpasswd -c docker/nginx/.htpasswd your_username
```

## Running the API

### Start the API Service

From the project root directory:

```bash
docker-compose -f docker/docker-compose.yaml up -d
```

The API will be available at:
- HTTP: http://localhost/api/v1 (redirects to HTTPS)
- HTTPS: https://localhost/api/v1

### Check Logs

```bash
# API logs
docker logs xai-api

# Nginx logs
docker logs xai-nginx
```

### Stop the Service

```bash
docker-compose -f docker/docker-compose.yaml down
```

## Development Mode

For development with hot reloading, uncomment the volume mapping in `docker-compose.yaml`:

```yaml
volumes:
  - ../app:/app/app  # For hot reloading during development
  - ../images:/app/images:rw
```

## Health Check

Both containers include health checks. Check their health status with:

```bash
docker inspect --format='{{json .State.Health}}' xai-api
docker inspect --format='{{json .State.Health}}' xai-nginx
```

## Nginx Configuration

The Nginx setup includes:

- HTTP to HTTPS redirection
- Modern TLS configuration with strong cipher suites
- Security headers (HSTS, X-Content-Type-Options, CSP, etc.)
- Request rate limiting
- Proxy buffer settings optimized for API responses
- Long timeouts for image generation endpoints

## Troubleshooting

If you encounter any issues:

1. Check that your API key is valid
2. Verify SSL certificates are present in `docker/nginx/ssl/`
3. Check container logs for error messages
4. If file permission issues occur, verify the volume mounts have correct permissions 