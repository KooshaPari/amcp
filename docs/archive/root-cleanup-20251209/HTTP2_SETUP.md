# HTTP/2 + SSE Streaming Setup Guide

This guide covers configuring HTTP/2 protocol support with SSE streaming for SmartCP.

## Overview

HTTP/2 provides several benefits for streaming applications:
- **Multiplexing**: Multiple concurrent streams over single connection
- **Server Push**: Server can proactively send data
- **Header Compression**: HPACK compression reduces overhead
- **Binary Framing**: More efficient than HTTP/1.1 text
- **Flow Control**: Better management of bandwidth

## Prerequisites

1. **Python 3.10+** with FastAPI installed
2. **Hypercorn** (recommended for full HTTP/2 support):
   ```bash
   pip install hypercorn>=0.15.0
   ```

3. **SSL/TLS Certificates** (required for HTTP/2):
   - Self-signed (for development): See "Generating Self-Signed Certs"
   - Production: Use trusted CA (Let's Encrypt, etc.)

## Installation

1. **Install dependencies**:
   ```bash
   pip install hypercorn httpx h2
   ```

2. **Update `requirements.txt`** (if needed):
   ```
   hypercorn>=0.15.0
   httpx>=0.24.0
   h2>=4.1.0
   ```

## Configuration

### Environment Variables

Create a `.env` file for HTTP/2 configuration:

```bash
# HTTP/2 Protocol Settings
HTTP2_ENABLED=true
HTTP1_ENABLED=true
ALPN_PROTOCOLS=h2,http/1.1

# SSL/TLS Settings (required for HTTP/2)
SSL_ENABLED=true
SSL_KEYFILE=/path/to/key.pem
SSL_CERTFILE=/path/to/cert.pem

# Server Settings
SERVER_HOST=0.0.0.0
SERVER_PORT=443
WORKERS=1

# HTTP/2 Performance Tuning
HTTP2_MAX_STREAMS=100
HTTP2_MAX_HEADER_SIZE=16384

# Logging
LOG_LEVEL=info
```

### Programmatic Configuration

```python
from optimization import HTTP2Config, setup_http2_app
from fastapi import FastAPI

# Create app with HTTP/2 config
app = FastAPI()

# Configure HTTP/2
config = HTTP2Config(
    enable_http2=True,
    enable_http1=True,
    ssl_enabled=True,
    ssl_keyfile="certs/server.key",
    ssl_certfile="certs/server.crt",
    host="0.0.0.0",
    port=443,
)

# Setup HTTP/2 support
app = setup_http2_app(app, config)
```

## Starting the Server

### Using Hypercorn (Recommended)

```bash
# HTTP/2 with SSL
hypercorn app:app \
  --bind 0.0.0.0:443 \
  --certfile certs/server.crt \
  --keyfile certs/server.key \
  --alpn-protocols h2,http/1.1

# HTTP/2 with development SSL (self-signed)
hypercorn app:app \
  --bind 0.0.0.0:443 \
  --certfile certs/dev-cert.pem \
  --keyfile certs/dev-key.pem \
  --alpn-protocols h2,http/1.1

# With environment variables
hypercorn app:app \
  $(python -m optimization.http2_config | tail -1)
```

### Using Python Script

```python
#!/usr/bin/env python
"""Start SmartCP with HTTP/2 support."""

import asyncio
from fastapi import FastAPI
from optimization import setup_http2_app, HTTP2Config

# Create app
app = FastAPI(title="SmartCP with HTTP/2")

# Setup HTTP/2
config = HTTP2Config.from_env()
app = setup_http2_app(app, config)

if __name__ == "__main__":
    import uvicorn
    from optimization.http2_config import get_server_startup_command

    print("\n" + "="*80)
    print("Starting SmartCP with HTTP/2 Support")
    print("="*80)
    
    # Print config
    print(f"Server: {config.server_type}")
    print(f"Host: {config.host}:{config.port}")
    print(f"HTTP/2: {config.enable_http2}")
    print(f"SSL: {config.ssl_enabled}")
    print()
    print("Startup Command:")
    print(get_server_startup_command(config))
    print("="*80 + "\n")
    
    # Run server
    uvicorn.run(app, host=config.host, port=config.port)
```

## Generating Self-Signed Certificates

For development and testing:

```bash
# Create certs directory
mkdir -p certs

# Generate private key
openssl genrsa -out certs/server.key 2048

# Generate certificate (valid for 365 days)
openssl req -new -x509 -key certs/server.key -out certs/server.crt -days 365 \
  -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"

# Alternative: Generate both in one command
openssl req -x509 -newkey rsa:2048 -keyout certs/server.key \
  -out certs/server.crt -days 365 -nodes \
  -subj "/C=US/ST=State/L=City/O=Org/CN=localhost"
```

## Testing HTTP/2 Connection

### Using curl (HTTP/2)

```bash
# Test HTTP/2 connection
curl -I --http2 --insecure https://localhost/health/http2

# Check protocol negotiation
curl -v --http2 --insecure https://localhost/health/http2 2>&1 | grep "ALPN"

# With verbose output
curl -v --http2 --insecure https://localhost/info/protocol
```

### Using Python (httpx)

```python
import httpx
import asyncio

async def test_http2():
    """Test HTTP/2 connection."""
    async with httpx.AsyncClient(
        http2=True,
        verify=False,  # For self-signed certs
    ) as client:
        # Test health endpoint
        response = await client.get("https://localhost/health/http2")
        print(f"Status: {response.status_code}")
        print(f"HTTP Version: {response.http_version}")
        print(f"Data: {response.json()}")
        
        # Stream test
        async with client.stream(
            "GET",
            "https://localhost/v1/stream/status"
        ) as resp:
            print(f"Streaming HTTP Version: {resp.http_version}")

asyncio.run(test_http2())
```

### Using h2 (HTTP/2 specific)

```python
import h2.connection
import h2.config
import ssl
import socket

def test_http2_direct():
    """Test HTTP/2 using h2 library."""
    # Setup SSL
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    # Connect
    conn = socket.create_connection(("localhost", 443))
    conn = context.wrap_socket(conn, server_hostname="localhost")
    
    # H2 connection
    config = h2.config.H2Configuration(client_side=True)
    h2_conn = h2.connection.H2Connection(config=config)
    h2_conn.initiate_upgrade_connection()
    conn.sendall(h2_conn.data_to_send())
    
    # Send request
    h2_conn.send_headers(1, [
        (":method", "GET"),
        (":path", "/health/http2"),
        (":scheme", "https"),
        (":authority", "localhost:443"),
    ])
    conn.sendall(h2_conn.data_to_send())
    
    # Receive response
    while True:
        data = conn.recv(1024)
        if not data:
            break
        h2_conn.receive_data(data)
        for event in h2_conn.events:
            print(f"Event: {event}")

test_http2_direct()
```

## Streaming with HTTP/2

### Starting a Stream

```bash
# Start streaming
curl -X POST https://localhost/v1/stream/start \
  --insecure \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "process_data",
    "params": {"batch_size": 10}
  }'

# Response:
# {
#   "stream_id": "550e8400-e29b-41d4-a716-446655440000",
#   "operation": "process_data",
#   "subscribe_url": "/v1/stream/550e8400-e29b-41d4-a716-446655440000"
# }
```

### Subscribing to Events (HTTP/2 Multiplexed)

```bash
# Subscribe via HTTP/2
curl --http2 --insecure \
  https://localhost/v1/stream/550e8400-e29b-41d4-a716-446655440000

# With Python
import httpx
import asyncio

async def stream_events():
    """Subscribe to events via HTTP/2 SSE."""
    async with httpx.AsyncClient(
        http2=True,
        verify=False,
    ) as client:
        stream_id = "550e8400-e29b-41d4-a716-446655440000"
        
        async with client.stream(
            "GET",
            f"https://localhost/v1/stream/{stream_id}"
        ) as response:
            print(f"Protocol: {response.http_version}")
            
            async for line in response.aiter_lines():
                print(line)

asyncio.run(stream_events())
```

## Performance Optimization

### For High Throughput

```python
from optimization import HTTP2Config

config = HTTP2Config(
    h2_max_concurrent_streams=200,  # Increase for more concurrent streams
    h2_flow_control_window=131072,  # 128KB window
    workers=4,  # Multiple workers
    limit_concurrency=1000,
)
```

### For Low Latency

```python
from optimization import HTTP2Config

config = HTTP2Config(
    h2_max_concurrent_streams=50,  # Fewer concurrent
    timeout_keep_alive=30,
    timeout_graceful_shutdown=5,
)
```

## HTTP/2 Best Practices

1. **Always use SSL/TLS**: HTTP/2 requires SSL for most clients
2. **Server Push**: Consider using Server Push for critical assets
3. **Multiplexing**: Leverage multiple concurrent streams
4. **Header Compression**: Reduces bandwidth usage automatically
5. **Flow Control**: HTTP/2 handles flow control automatically
6. **Connection Reuse**: Clients reuse connections for multiple requests

## Troubleshooting

### "ALPN negotiation failed"
- Ensure SSL certificates are valid
- Check if client supports HTTP/2
- Verify ALPN protocols configuration

### "h2 connection error"
- Update h2 library: `pip install --upgrade h2`
- Check certificate validity
- Verify server is advertising h2 via ALPN

### "Connection refused"
- Check port is accessible (443 for HTTPS)
- Ensure firewall allows traffic
- Verify server is running

### "HTTP/1.1 only"
- Update to hypercorn (uvicorn has limited HTTP/2)
- Verify ALPN protocols are configured
- Check if client supports HTTP/2

## Production Deployment

### With Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d example.com

# Use in server
hypercorn app:app \
  --bind 0.0.0.0:443 \
  --certfile /etc/letsencrypt/live/example.com/fullchain.pem \
  --keyfile /etc/letsencrypt/live/example.com/privkey.pem \
  --alpn-protocols h2,http/1.1
```

### With Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## References

- [HTTP/2 Specification](https://http2.github.io/)
- [Hypercorn Documentation](https://pgjones.gitlab.io/hypercorn/)
- [ALPN (Application-Layer Protocol Negotiation)](https://en.wikipedia.org/wiki/Application-Layer_Protocol_Negotiation)
- [SSL/TLS Configuration](https://wiki.mozilla.org/Security/Server_Side_TLS)

