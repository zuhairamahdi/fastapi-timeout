# FastAPI Timeout Middleware

A configurable timeout middleware for FastAPI applications that automatically handles request timeouts with customizable error responses.

## Features

- ⏱️ **Configurable timeout duration** - Set custom timeout values per application or per endpoint
- 🎯 **Per-endpoint control** - Use `@timeout()` decorator for fine-grained timeout control
- 📝 **Customizable error responses** - Configure status codes, messages, and response format
- 🔧 **Multiple integration methods** - Use as ASGI middleware, HTTP middleware, or endpoint decorator
- 📊 **Processing time tracking** - Optional inclusion of actual processing time in timeout responses
- � **Custom timeout handlers** - Provide your own timeout response logic
- 🚀 **High performance** - Minimal overhead using asyncio
- 📚 **Type hints included** - Full typing support for better IDE integration
- ⚠️ **Safe defaults** - Prevents problematic HTTP 408 status code usage

## Installation

```bash
pip install fastapi-timeout
```

## Quick Start

### Method 1: ASGI Middleware (Recommended)

```python
from fastapi import FastAPI
from fastapi_timeout import TimeoutMiddleware

app = FastAPI()

# Add timeout middleware with 5 second timeout
app.add_middleware(TimeoutMiddleware, timeout_seconds=5.0)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/slow")
async def slow_endpoint():
    import asyncio
    await asyncio.sleep(10)  # This will timeout after 5 seconds
    return {"message": "This will never be reached"}
```

### Method 2: HTTP Middleware Decorator

```python
from fastapi import FastAPI, Request
from fastapi_timeout import timeout_middleware

app = FastAPI()

@app.middleware("http")
async def add_timeout(request: Request, call_next):
    timeout_handler = timeout_middleware(timeout_seconds=5.0)
    return await timeout_handler(request, call_next)
```

### Method 3: Per-Endpoint Decorator

```python
from fastapi import FastAPI
from fastapi_timeout import timeout

app = FastAPI()

@app.get("/fast-endpoint")
@timeout(5.0)  # 5 second timeout for this endpoint only
async def fast_endpoint():
    return {"message": "Fast endpoint with 5s timeout"}

@app.get("/slow-endpoint")  
@timeout(30.0, timeout_status_code=503, timeout_message="Slow operation timeout")
async def slow_endpoint():
    return {"message": "Slow endpoint with 30s timeout"}
```

## Configuration Options

### Basic Configuration

```python
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=10.0,              # Timeout after 10 seconds
    timeout_status_code=503,           # Return 503 Service Unavailable  
    timeout_message="Request timeout", # Custom error message
    include_process_time=True          # Include processing time in response
)
```

**⚠️ Important:** Do not use HTTP status code 408 (Request Timeout) as it causes browsers and HTTP clients to automatically retry requests, which can lead to unexpected behavior and increased server load. Use 504 (Gateway Timeout) or 503 (Service Unavailable) instead.

### Advanced Configuration with Custom Handler

```python
from fastapi import Request, Response
from fastapi.responses import JSONResponse

def custom_timeout_handler(request: Request, process_time: float) -> Response:
    return JSONResponse(
        status_code=503,
        content={
            "error": "Service temporarily unavailable",
            "path": request.url.path,
            "method": request.method,
            "timeout_duration": process_time,
            "retry_after": 60
        },
        headers={"Retry-After": "60"}
    )

app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=15.0,
    custom_timeout_handler=custom_timeout_handler
)
```

## Per-Endpoint Timeout Control

### Using the @timeout Decorator

For fine-grained control, you can apply different timeouts to specific endpoints using the `@timeout` decorator:

```python
from fastapi import FastAPI, Request
from fastapi_timeout import timeout, TimeoutMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Optional: Global fallback timeout
app.add_middleware(TimeoutMiddleware, timeout_seconds=30.0)

@app.get("/api/quick")
@timeout(2.0)  # 2 second timeout
async def quick_operation():
    return {"message": "Quick operation"}

@app.get("/api/medium")
@timeout(10.0, timeout_message="Medium operation timed out")
async def medium_operation():
    return {"message": "Medium operation"}

@app.get("/api/batch")
@timeout(60.0, timeout_status_code=503)
async def batch_operation():
    return {"message": "Long batch operation"}

# Custom timeout handler for specific endpoint
def vip_timeout_handler(request: Request, process_time: float):
    return JSONResponse(
        status_code=503,
        content={
            "error": "VIP service busy",
            "retry_after": 30,
            "processing_time": process_time
        }
    )

@app.get("/api/vip")
@timeout(5.0, custom_timeout_handler=vip_timeout_handler)
async def vip_endpoint():
    return {"message": "VIP operation"}
```

### Decorator Features

- **Per-endpoint control**: Each endpoint can have its own timeout
- **Overrides global middleware**: Decorator timeouts take precedence
- **All configuration options**: Supports custom messages, status codes, and handlers
- **Easy to apply**: Simply add `@timeout(seconds)` below your route decorator

### Mixed Approach

You can combine global middleware with per-endpoint decorators:

```python
# Global timeout for most endpoints
app.add_middleware(TimeoutMiddleware, timeout_seconds=10.0)

# Override for specific endpoints
@app.get("/slow-report")
@timeout(60.0)  # This endpoint gets 60 seconds instead of 10
async def generate_report():
    return {"message": "Report generated"}
```

## Response Format

### Default Timeout Response

When a request times out, the middleware returns a JSON response:

```json
{
    "detail": "Request processing time exceeded limit",
    "timeout_seconds": 5.0,
    "processing_time": 5.002
}
```

### Customizable Fields

- `timeout_status_code`: HTTP status code (default: 504 Gateway Timeout)
  - **⚠️ Avoid 408 (Request Timeout)** - causes automatic retries in browsers/clients
  - **Recommended**: 504 (Gateway Timeout) or 503 (Service Unavailable)
- `timeout_message`: Error message (default: "Request processing time exceeded limit")
- `include_process_time`: Whether to include actual processing time (default: True)

## Use Cases

### Different Timeouts for Different Operations
```python
@app.get("/api/search")
@timeout(5.0)  # Quick search
async def search(): pass

@app.post("/api/upload")
@timeout(120.0)  # File upload
async def upload(): pass

@app.get("/api/report")
@timeout(300.0)  # Long report generation
async def generate_report(): pass
```

### Web APIs with Database Queries
```python
# Prevent hanging database queries
app.add_middleware(TimeoutMiddleware, timeout_seconds=30.0)
```

### Microservices with External Dependencies
```python
# Timeout requests that depend on external services
app.add_middleware(
    TimeoutMiddleware, 
    timeout_seconds=10.0,
    timeout_status_code=503,
    timeout_message="Service temporarily unavailable"
)
```

### File Upload Endpoints
```python
# Different timeout for file upload routes
from starlette.middleware.base import BaseHTTPMiddleware

class ConditionalTimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/upload"):
            # Longer timeout for uploads
            timeout_handler = timeout_middleware(timeout_seconds=60.0)
            return await timeout_handler(request, call_next)
        else:
            # Standard timeout for other endpoints
            timeout_handler = timeout_middleware(timeout_seconds=5.0)
            return await timeout_handler(request, call_next)

app.add_middleware(ConditionalTimeoutMiddleware)
```

## Testing

The package includes comprehensive tests. To run them:

```bash
pip install fastapi-timeout[dev]
pytest
```

## Requirements

- Python 3.7+
- FastAPI 0.65.0+
- Starlette 0.14.0+

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
