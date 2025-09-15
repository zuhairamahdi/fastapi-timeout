"""
Example usage of fastapi-timeout with per-endpoint timeout decorators.
"""

import asyncio
from fastapi import FastAPI, Request
from fastapi_timeout import timeout, TimeoutMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Per-Endpoint Timeout Example")

# Optional: Add global timeout middleware as fallback
# This will apply to endpoints that don't have the @timeout decorator
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=10.0,  # Global fallback timeout
    timeout_message="Global timeout - request took too long"
)


@app.get("/")
async def root():
    """Endpoint without decorator - uses global middleware timeout (10s)."""
    return {"message": "Hello World", "timeout": "global (10s)"}


@app.get("/quick")
@timeout(2.0)  # 2 second timeout
async def quick_endpoint():
    """Quick endpoint with 2 second timeout."""
    await asyncio.sleep(1.0)  # Should complete
    return {
        "message": "Quick response", 
        "timeout": "2 seconds",
        "delay": 1.0
    }


@app.get("/medium")
@timeout(5.0, timeout_message="Medium operation timed out")
async def medium_endpoint():
    """Medium endpoint with 5 second timeout and custom message."""
    await asyncio.sleep(3.0)  # Should complete
    return {
        "message": "Medium response", 
        "timeout": "5 seconds",
        "delay": 3.0
    }


@app.get("/slow")
@timeout(3.0, timeout_status_code=503, timeout_message="Slow operation unavailable")
async def slow_endpoint():
    """Slow endpoint that will timeout after 3 seconds."""
    await asyncio.sleep(6.0)  # Will timeout
    return {
        "message": "This will never be reached",
        "timeout": "3 seconds",
        "delay": 6.0
    }


@app.get("/custom-delay/{seconds}")
@timeout(4.0)
async def custom_delay_endpoint(seconds: int):
    """Endpoint with configurable delay and 4 second timeout."""
    await asyncio.sleep(seconds)
    return {
        "message": f"Completed after {seconds} seconds",
        "timeout": "4 seconds",
        "delay": seconds
    }


# Example with custom timeout handler
def custom_timeout_handler(request: Request, process_time: float):
    """Custom timeout handler for VIP endpoint."""
    return JSONResponse(
        status_code=503,
        content={
            "error": "VIP service temporarily unavailable",
            "message": "Please try again in a moment",
            "path": request.url.path,
            "processing_time": round(process_time, 3),
            "support": "contact@example.com"
        },
        headers={
            "Retry-After": "30",
            "X-Service": "VIP"
        }
    )


@app.get("/vip")
@timeout(2.0, custom_timeout_handler=custom_timeout_handler)
async def vip_endpoint():
    """VIP endpoint with custom timeout handler."""
    await asyncio.sleep(5.0)  # Will timeout with custom response
    return {"message": "VIP response"}


# Example with endpoint that includes Request parameter
@app.post("/upload")
@timeout(30.0, timeout_message="File upload timeout")
async def upload_endpoint(request: Request):
    """File upload endpoint with 30 second timeout."""
    # Simulate file processing
    await asyncio.sleep(2.0)
    return {
        "message": "File uploaded successfully",
        "timeout": "30 seconds",
        "client": request.client.host if request.client else "unknown"
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting server with per-endpoint timeouts...")
    print("Endpoint timeouts:")
    print("  GET /           - Global timeout (10s)")
    print("  GET /quick      - 2s timeout (should complete in 1s)")
    print("  GET /medium     - 5s timeout (should complete in 3s)")  
    print("  GET /slow       - 3s timeout (will timeout after 6s delay)")
    print("  GET /custom-delay/{seconds} - 4s timeout")
    print("  GET /vip        - 2s timeout with custom handler")
    print("  POST /upload    - 30s timeout")
    uvicorn.run(app, host="0.0.0.0", port=8002)
