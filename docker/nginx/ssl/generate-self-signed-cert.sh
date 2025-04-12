#!/bin/bash
set -e

# Generate self-signed SSL certificate for local development
echo "Generating self-signed SSL certificate for local development..."

# Generate private key
openssl genrsa -out server.key 2048

# Generate certificate signing request
openssl req -new -key server.key -out server.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Generate self-signed certificate valid for 365 days
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt

# Clean up CSR file
rm server.csr

echo "Self-signed certificate generated successfully!"
echo "server.key and server.crt are ready for use with Nginx."
echo "Note: For production, replace these with proper certificates from a trusted CA." 