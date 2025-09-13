# FastAPI Timeout Middleware

A configurable timeout middleware for FastAPI applications that automatically handles request timeouts with customizable error responses.

## Features

- ⏱️ **Configurable timeout duration** - Set custom timeout values per application
- 📝 **Customizable error responses** - Configure status codes, messages, and response format
- 🔧 **Multiple integration methods** - Use as ASGI middleware or HTTP middleware decorator
- 📊 **Processing time tracking** - Optional inclusion of actual processing time in timeout responses
- 🎯 **Custom timeout handlers** - Provide your own timeout response logic
- 🚀 **High performance** - Minimal overhead using asyncio
- 📚 **Type hints included** - Full typing support for better IDE integration

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

## Configuration Options

### Basic Configuration

```python
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=10.0,              # Timeout after 10 seconds
    timeout_status_code=408,           # Return 408 Request Timeout
    timeout_message="Request timeout", # Custom error message
    include_process_time=True          # Include processing time in response
)
```

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

- `timeout_status_code`: HTTP status code (default: 504)
- `timeout_message`: Error message (default: "Request processing time exceeded limit")
- `include_process_time`: Whether to include actual processing time (default: True)

## Use Cases

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
