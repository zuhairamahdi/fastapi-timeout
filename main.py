"""
Example of using the fastapi-timeout library in your FastAPI application.
Shows both global middleware and per-endpoint decorator usage.
"""

import asyncio
from fastapi import FastAPI
from fastapi_timeout import TimeoutMiddleware, timeout

app = FastAPI()

# Add global timeout middleware as fallback (optional)
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=5.0,
    timeout_status_code=504,  # Gateway Timeout (safe choice)
    timeout_message="Global timeout - request took too long",
    include_process_time=False
)


@app.get("/")
async def root():
    """Root endpoint using global timeout (5s)."""
    return {"message": "Hello World", "timeout": "global (5s)"}


@app.get("/fast")
@timeout(2.0)  # Override global timeout with 2 seconds
async def fast_endpoint():
    """Fast endpoint with 2 second timeout via decorator."""
    await asyncio.sleep(1.0)  # Should complete
    return {
        "message": "This is a fast response", 
        "timeout": "2 seconds (decorator)",
        "delay": "1 second"
    }


@app.get("/slow")  
@timeout(3.0, timeout_message="Slow endpoint timeout")
async def slow_endpoint():
    """Slow endpoint with custom timeout message."""
    await asyncio.sleep(4.0)  # Will timeout after 3 seconds
    return {"message": "This response will timeout"}

@app.get("/slow-without-decorator")
async def slow_without_decorator():
    """Slow endpoint without decorator - uses global middleware timeout (5s)."""
    await asyncio.sleep(6.0)  # Will timeout after 5 seconds
    return {"message": "This response will timeout due to global middleware"}

@app.get("/timeout/{seconds}")
@timeout(6.0)
async def custom_timeout(seconds: int):
    """Endpoint with configurable delay and 6 second timeout."""
    await asyncio.sleep(seconds)
    return {"message": f"Completed after {seconds} seconds"}


if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI with timeout middleware and decorators...")
    print("Timeout configuration:")
    print("  GET /               - Global timeout (5s)")
    print("  GET /fast           - Decorator timeout (2s, should complete in 1s)")
    print("  GET /slow           - Decorator timeout (3s, will timeout after 4s)")
    print("  GET /timeout/{n}    - Decorator timeout (6s)")
    print("")
    print("Try these endpoints:")
    print("  GET /fast           - Should complete")
    print("  GET /slow           - Should timeout with custom message")
    print("  GET /timeout/2      - Should complete")
    print("  GET /timeout/8      - Should timeout")
    uvicorn.run(app, host="0.0.0.0", port=8000)

