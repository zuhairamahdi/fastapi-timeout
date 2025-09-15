import asyncio
import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from fastapi_timeout import TimeoutMiddleware
import time


@pytest.fixture
def app_with_timeout():
    """Create a FastAPI app with timeout middleware for testing."""
    app = FastAPI()
    
    app.add_middleware(
        TimeoutMiddleware,
        timeout_seconds=1.0,  # 1 second timeout for fast tests
        timeout_status_code=504,  # Gateway Timeout instead of 408
        timeout_message="Test timeout",
        include_process_time=True
    )
    
    @app.get("/fast")
    async def fast_endpoint():
        await asyncio.sleep(0.1)  # 100ms - should complete
        return {"status": "fast"}
    
    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(2.0)  # 2 seconds - should timeout
        return {"status": "slow"}
    
    @app.get("/instant")
    async def instant_endpoint():
        return {"status": "instant"}
    
    return app


@pytest.fixture
def client(app_with_timeout):
    """Create a test client."""
    return TestClient(app_with_timeout)


def test_fast_endpoint_completes(client):
    """Test that fast endpoints complete successfully."""
    response = client.get("/fast")
    assert response.status_code == 200
    assert response.json() == {"status": "fast"}


def test_instant_endpoint_completes(client):
    """Test that instant endpoints complete successfully."""
    response = client.get("/instant")
    assert response.status_code == 200
    assert response.json() == {"status": "instant"}


def test_slow_endpoint_times_out(client):
    """Test that slow endpoints trigger timeout."""
    response = client.get("/slow")
    assert response.status_code == 504  # Gateway Timeout instead of 408
    
    json_response = response.json()
    assert "detail" in json_response
    assert json_response["detail"] == "Test timeout"
    assert "timeout_seconds" in json_response
    assert json_response["timeout_seconds"] == 1.0
    assert "processing_time" in json_response
    assert json_response["processing_time"] >= 1.0


def test_custom_timeout_handler():
    """Test custom timeout handler functionality."""
    app = FastAPI()
    
    def custom_handler(request: Request, process_time: float) -> Response:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Custom timeout",
                "path": request.url.path,
                "time": process_time
            }
        )
    
    app.add_middleware(
        TimeoutMiddleware,
        timeout_seconds=0.5,
        custom_timeout_handler=custom_handler
    )
    
    @app.get("/test")
    async def test_endpoint():
        await asyncio.sleep(1.0)
        return {"status": "done"}
    
    client = TestClient(app)
    response = client.get("/test")
    
    assert response.status_code == 503
    json_response = response.json()
    assert json_response["error"] == "Custom timeout"
    assert json_response["path"] == "/test"
    assert json_response["time"] >= 0.5


def test_timeout_configuration():
    """Test different timeout configurations."""
    app = FastAPI()
    
    app.add_middleware(
        TimeoutMiddleware,
        timeout_seconds=2.0,
        timeout_status_code=504,
        timeout_message="Gateway timeout",
        include_process_time=False
    )
    
    @app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(3.0)
        return {"status": "done"}
    
    client = TestClient(app)
    response = client.get("/slow")
    
    assert response.status_code == 504
    json_response = response.json()
    assert json_response["detail"] == "Gateway timeout"
    assert json_response["timeout_seconds"] == 2.0
    assert "processing_time" not in json_response  # Should be excluded


@pytest.mark.asyncio
async def test_multiple_concurrent_requests():
    """Test that middleware handles multiple concurrent requests properly."""
    app = FastAPI()
    
    app.add_middleware(TimeoutMiddleware, timeout_seconds=1.0)
    
    @app.get("/concurrent")
    async def concurrent_endpoint():
        await asyncio.sleep(0.5)
        return {"status": "concurrent"}
    
    client = TestClient(app)
    
    # Make multiple concurrent requests
    responses = []
    for _ in range(5):
        response = client.get("/concurrent")
        responses.append(response)
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200
        assert response.json() == {"status": "concurrent"}


def test_status_code_408_is_rejected():
    """Test that using status code 408 raises a ValueError."""
    app = FastAPI()
    
    with pytest.raises(ValueError, match="HTTP 408.*should not be used"):
        app.add_middleware(
            TimeoutMiddleware,
            timeout_seconds=1.0,
            timeout_status_code=408  # This should raise an error
        )


def test_timeout_middleware_function_408_is_rejected():
    """Test that decorator-style middleware also rejects 408."""
    from fastapi_timeout import timeout_middleware
    
    with pytest.raises(ValueError, match="HTTP 408.*should not be used"):
        timeout_middleware(timeout_seconds=1.0, timeout_status_code=408)


def test_timeout_decorator():
    """Test the timeout decorator functionality."""
    from fastapi_timeout import timeout
    
    app = FastAPI()
    
    @app.get("/decorated")
    @timeout(1.0, timeout_message="Decorated endpoint timeout")
    async def decorated_endpoint():
        await asyncio.sleep(2.0)  # Will timeout
        return {"status": "done"}
    
    @app.get("/decorated-fast") 
    @timeout(2.0)
    async def decorated_fast_endpoint():
        await asyncio.sleep(0.5)  # Should complete
        return {"status": "fast"}
    
    client = TestClient(app)
    
    # Test timeout
    response = client.get("/decorated")
    assert response.status_code == 504
    json_response = response.json()
    assert json_response["detail"] == "Decorated endpoint timeout"
    assert json_response["timeout_seconds"] == 1.0
    assert "processing_time" in json_response
    
    # Test successful completion
    response = client.get("/decorated-fast")
    assert response.status_code == 200
    assert response.json() == {"status": "fast"}


def test_timeout_decorator_custom_handler():
    """Test timeout decorator with custom handler."""
    from fastapi_timeout import timeout
    
    def custom_handler(request, process_time):
        return JSONResponse(
            status_code=503,
            content={"custom": "timeout", "time": process_time}
        )
    
    app = FastAPI()
    
    @app.get("/custom")
    @timeout(0.5, custom_timeout_handler=custom_handler)
    async def custom_endpoint():
        await asyncio.sleep(1.0)
        return {"status": "done"}
    
    client = TestClient(app)
    response = client.get("/custom")
    
    assert response.status_code == 503
    json_response = response.json()
    assert json_response["custom"] == "timeout"
    assert "time" in json_response


def test_timeout_decorator_408_rejection():
    """Test that timeout decorator rejects 408 status code."""
    from fastapi_timeout import timeout
    
    with pytest.raises(ValueError, match="HTTP 408.*should not be used"):
        @timeout(1.0, timeout_status_code=408)
        async def bad_endpoint():
            return {"status": "bad"}


def test_mixed_timeout_approaches():
    """Test combination of middleware and decorator timeouts."""
    from fastapi_timeout import timeout
    
    app = FastAPI()
    
    # Add global middleware
    app.add_middleware(
        TimeoutMiddleware,
        timeout_seconds=5.0,
        timeout_message="Global timeout"
    )
    
    @app.get("/global")
    async def global_endpoint():
        await asyncio.sleep(6.0)  # Will hit global timeout
        return {"status": "global"}
    
    @app.get("/decorated")
    @timeout(2.0, timeout_message="Decorator timeout")
    async def decorated_endpoint():
        await asyncio.sleep(3.0)  # Will hit decorator timeout first
        return {"status": "decorated"}
    
    client = TestClient(app)
    
    # Test global timeout
    response = client.get("/global")
    assert response.status_code == 504
    json_response = response.json()
    assert "Global timeout" in json_response["detail"]
    
    # Test decorator timeout (should override global)
    response = client.get("/decorated")  
    assert response.status_code == 504
    json_response = response.json()
    assert json_response["detail"] == "Decorator timeout"
    assert json_response["timeout_seconds"] == 2.0
