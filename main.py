"""
Example of using the fastapi-timeout library in your FastAPI application.
"""

import asyncio
from fastapi import FastAPI
from fastapi_timeout import TimeoutMiddleware

app = FastAPI()

# Add the timeout middleware with 1 second timeout
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=1.0,
    timeout_status_code=504,  # Gateway Timeout (safe choice)
    timeout_message="Request processing time exceeded limit",
    include_process_time=True
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/fast")
async def fast_endpoint():
    """A fast endpoint that completes within the timeout"""
    await asyncio.sleep(0.5)  # Simulate 0.5 second of work (within 1s timeout)
    return {"message": "This is a fast response"}


@app.get("/slow")
async def slow_endpoint():
    """A slow endpoint that will trigger the timeout"""
    await asyncio.sleep(2.0)  # Simulate 2 seconds of work (exceeds 1s timeout)
    return {"message": "This response will timeout"}


@app.get("/timeout/{seconds}")
async def custom_timeout(seconds: int):
    """Endpoint with configurable delay for testing"""
    await asyncio.sleep(seconds)
    return {"message": f"Completed after {seconds} seconds"}


if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI with timeout middleware (1 second timeout)...")
    print("Try these endpoints:")
    print("  GET /fast      - Should complete (0.5s delay)")
    print("  GET /slow      - Should timeout (2s delay)")
    print("  GET /timeout/0 - Should complete immediately")
    print("  GET /timeout/2 - Should timeout (2s > 1s timeout)")
    uvicorn.run(app, host="0.0.0.0", port=8000)

