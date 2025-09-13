"""
Exampl# Add timeout middleware with 3 second timeout
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=3.0,
    timeout_status_code=503,  # Service Unavailable (safe choice)
    timeout_message="Your request took too long to process",
    include_process_time=True
)of fastapi-timeout middleware with ASGI middleware approach.
"""

import asyncio
from fastapi import FastAPI
from fastapi_timeout import TimeoutMiddleware

app = FastAPI(title="FastAPI Timeout Example")

# Add timeout middleware with 3 second timeout
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=3.0,
    timeout_status_code=504,  # Request Timeout
    timeout_message="Your request took too long to process",
    include_process_time=True
)


@app.get("/")
async def root():
    """Fast endpoint that completes quickly."""
    return {"message": "Hello World", "status": "success"}


@app.get("/fast")
async def fast_endpoint():
    """Fast endpoint that completes within timeout."""
    await asyncio.sleep(1.0)  # 1 second - within 3s timeout
    return {
        "message": "This is a fast response", 
        "delay": 1.0,
        "status": "completed"
    }


@app.get("/slow")
async def slow_endpoint():
    """Slow endpoint that will trigger timeout."""
    await asyncio.sleep(5.0)  # 5 seconds - exceeds 3s timeout
    return {
        "message": "This will never be reached",
        "delay": 5.0,
        "status": "completed"
    }


@app.get("/custom-delay/{seconds}")
async def custom_delay(seconds: int):
    """Endpoint with configurable delay for testing."""
    await asyncio.sleep(seconds)
    return {
        "message": f"Completed after {seconds} seconds",
        "delay": seconds,
        "status": "completed"
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting server with 3 second timeout...")
    print("Try these endpoints:")
    print("  GET /fast      - Should complete (1s delay)")
    print("  GET /slow      - Should timeout (5s delay)")
    print("  GET /custom-delay/2  - Should complete (2s delay)")
    print("  GET /custom-delay/4  - Should timeout (4s delay)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
