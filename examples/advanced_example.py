"""
Example usage with custom timeout handler and different configurations.
"""

import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi_timeout import TimeoutMiddleware

app = FastAPI(title="Advanced FastAPI Timeout Example")


def custom_timeout_handler(request: Request, process_time: float) -> Response:
    """Custom timeout handler with detailed error information."""
    return JSONResponse(
        status_code=503,  # Service Unavailable
        content={
            "error": "Service Temporarily Unavailable",
            "message": "The server is currently unable to handle the request due to timeout",
            "details": {
                "path": request.url.path,
                "method": request.method,
                "processing_time_seconds": round(process_time, 3),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            },
            "retry_after_seconds": 30,
            "support_contact": "support@example.com"
        },
        headers={
            "Retry-After": "30",
            "X-Timeout-Reason": "processing-timeout",
            "X-Processing-Time": str(round(process_time, 3))
        }
    )


# Add timeout middleware with custom handler
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=2.0,
    custom_timeout_handler=custom_timeout_handler
)


@app.get("/")
async def root():
    return {"message": "Advanced timeout example", "timeout": "2 seconds"}


@app.get("/api/data")
async def get_data():
    """Simulate data fetching that might timeout."""
    await asyncio.sleep(1.5)  # Just under timeout
    return {
        "data": ["item1", "item2", "item3"],
        "count": 3,
        "processing_time": "1.5s"
    }


@app.get("/api/slow-query")
async def slow_database_query():
    """Simulate a slow database query that will timeout."""
    await asyncio.sleep(3.0)  # Will timeout after 2s
    return {"query_result": "This won't be returned"}


@app.post("/api/upload")
async def upload_file():
    """Simulate file upload processing."""
    await asyncio.sleep(2.5)  # Will timeout
    return {"upload_status": "completed"}


@app.get("/health")
async def health_check():
    """Quick health check endpoint."""
    return {"status": "healthy", "timestamp": "2025-01-01T00:00:00Z"}


if __name__ == "__main__":
    import uvicorn
    print("Starting advanced example with 2 second timeout...")
    print("Custom timeout handler will return 503 with detailed error info")
    uvicorn.run(app, host="0.0.0.0", port=8001)
