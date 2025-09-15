import time
import asyncio
from typing import Optional, Callable, Dict, Any
from functools import wraps
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.status import HTTP_504_GATEWAY_TIMEOUT


class TimeoutMiddleware:
    """
    Timeout middleware for FastAPI applications.
    
    This middleware automatically times out requests that exceed a specified duration
    and returns a configurable error response.
    
    Args:
        timeout_seconds (float): Maximum time in seconds to wait for request completion.
                                Defaults to 30.0 seconds.
        timeout_status_code (int): HTTP status code to return on timeout.
                                  Defaults to 504 (Gateway Timeout).
                                  WARNING: Do not use 408 (Request Timeout) as it causes 
                                  browsers and HTTP clients to automatically retry requests.
        timeout_message (str): Error message to include in timeout response.
                              Defaults to "Request processing time exceeded limit".
        include_process_time (bool): Whether to include actual processing time in response.
                                   Defaults to True.
        custom_timeout_handler (Callable): Optional custom function to handle timeout response.
                                         Should accept (request, process_time) and return Response.
    
    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_timeout import TimeoutMiddleware
        
        app = FastAPI()
        app.add_middleware(TimeoutMiddleware, timeout_seconds=5.0)
        ```
    
    Example with custom configuration:
        ```python
        app.add_middleware(
            TimeoutMiddleware,
            timeout_seconds=10.0,
            timeout_status_code=503,  # Service Unavailable
            timeout_message="Request took too long!",
            include_process_time=False
        )
        ```
    """
    
    def __init__(
        self,
        app,
        timeout_seconds: float = 30.0,
        timeout_status_code: int = HTTP_504_GATEWAY_TIMEOUT,
        timeout_message: str = "Request processing time exceeded limit",
        include_process_time: bool = True,
        custom_timeout_handler: Optional[Callable[[Request, float], Response]] = None
    ):
        # Validate timeout_status_code to prevent problematic codes
        if timeout_status_code == 408:
            raise ValueError(
                "HTTP 408 (Request Timeout) should not be used as it causes browsers "
                "and HTTP clients to automatically retry requests. Use 504 (Gateway Timeout) "
                "or 503 (Service Unavailable) instead."
            )
        
        self.app = app
        self.timeout_seconds = timeout_seconds
        self.timeout_status_code = timeout_status_code
        self.timeout_message = timeout_message
        self.include_process_time = include_process_time
        self.custom_timeout_handler = custom_timeout_handler

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        
        try:
            await asyncio.wait_for(
                self.app(scope, receive, send),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            process_time = time.time() - start_time
            
            # Use custom timeout handler if provided
            if self.custom_timeout_handler:
                request = Request(scope, receive)
                response = self.custom_timeout_handler(request, process_time)
            else:
                response = self._default_timeout_response(process_time)
            
            await response(scope, receive, send)

    def _default_timeout_response(self, process_time: float) -> Response:
        """Create the default timeout response."""
        content: Dict[str, Any] = {
            "detail": self.timeout_message,
            "timeout_seconds": self.timeout_seconds
        }
        
        if self.include_process_time:
            content["processing_time"] = round(process_time, 3)
        
        return JSONResponse(
            content=content,
            status_code=self.timeout_status_code
        )


# Decorator-style middleware for easier use
def timeout_middleware(
    timeout_seconds: float = 30.0,
    timeout_status_code: int = HTTP_504_GATEWAY_TIMEOUT,
    timeout_message: str = "Request processing time exceeded limit",
    include_process_time: bool = True,
    custom_timeout_handler: Optional[Callable[[Request, float], Response]] = None
):
    """
    Decorator-style timeout middleware for FastAPI applications.
    
    This provides an alternative way to add timeout middleware using the @app.middleware decorator.
    
    Args:
        timeout_seconds (float): Maximum time in seconds to wait for request completion.
        timeout_status_code (int): HTTP status code to return on timeout.
                                  WARNING: Do not use 408 (Request Timeout) as it causes 
                                  browsers to automatically retry requests.
        timeout_message (str): Error message to include in timeout response.
        include_process_time (bool): Whether to include actual processing time in response.
        custom_timeout_handler (Callable): Optional custom function to handle timeout response.
    
    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_timeout import timeout_middleware
        
        app = FastAPI()
        
        @app.middleware("http")
        async def add_timeout(request: Request, call_next):
            return await timeout_middleware(timeout_seconds=5.0)(request, call_next)
        ```
    """
    
    # Validate timeout_status_code to prevent problematic codes
    if timeout_status_code == 408:
        raise ValueError(
            "HTTP 408 (Request Timeout) should not be used as it causes browsers "
            "and HTTP clients to automatically retry requests. Use 504 (Gateway Timeout) "
            "or 503 (Service Unavailable) instead."
        )
    
    def middleware_decorator(request: Request, call_next):
        return _timeout_middleware_function(
            request, call_next, timeout_seconds, timeout_status_code,
            timeout_message, include_process_time, custom_timeout_handler
        )
    
    return middleware_decorator


async def _timeout_middleware_function(
    request: Request,
    call_next,
    timeout_seconds: float,
    timeout_status_code: int,
    timeout_message: str,
    include_process_time: bool,
    custom_timeout_handler: Optional[Callable[[Request, float], Response]]
):
    """Internal function to handle timeout logic for decorator-style middleware."""
    try:
        start_time = time.time()
        response = await asyncio.wait_for(call_next(request), timeout=timeout_seconds)
        return response
    except asyncio.TimeoutError:
        process_time = time.time() - start_time
        
        if custom_timeout_handler:
            return custom_timeout_handler(request, process_time)
        
        content: Dict[str, Any] = {
            "detail": timeout_message,
            "timeout_seconds": timeout_seconds
        }
        
        if include_process_time:
            content["processing_time"] = round(process_time, 3)
        
        return JSONResponse(
            content=content,
            status_code=timeout_status_code
        )


# Per-endpoint timeout decorator
def timeout(
    timeout_seconds: float,
    timeout_status_code: int = HTTP_504_GATEWAY_TIMEOUT,
    timeout_message: str = "Request processing time exceeded limit",
    include_process_time: bool = True,
    custom_timeout_handler: Optional[Callable[[Request, float], Response]] = None
):
    """
    Decorator for applying timeout to individual FastAPI endpoints.
    
    This decorator allows you to set different timeout values for specific endpoints
    without using global middleware. The timeout is applied per endpoint invocation.
    
    Args:
        timeout_seconds (float): Maximum time in seconds to wait for endpoint completion.
        timeout_status_code (int): HTTP status code to return on timeout.
                                  WARNING: Do not use 408 (Request Timeout) as it causes 
                                  browsers to automatically retry requests.
        timeout_message (str): Error message to include in timeout response.
        include_process_time (bool): Whether to include actual processing time in response.
        custom_timeout_handler (Callable): Optional custom function to handle timeout response.
                                         Should accept (request, process_time) and return Response.
    
    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_timeout import timeout
        
        app = FastAPI()
        
        @app.get("/fast")
        @timeout(5.0)
        async def fast_endpoint():
            return {"message": "Fast endpoint with 5s timeout"}
            
        @app.get("/slow")
        @timeout(30.0, timeout_status_code=503, timeout_message="Slow operation timeout")
        async def slow_endpoint():
            return {"message": "Slow endpoint with 30s timeout"}
        ```
    
    Note: 
        - The decorator should be placed below the FastAPI route decorator
        - Each decorated endpoint will have its own timeout independent of global middleware
        - This approach gives you fine-grained control over timeout behavior per endpoint
    """
    
    # Validate timeout_status_code to prevent problematic codes
    if timeout_status_code == 408:
        raise ValueError(
            "HTTP 408 (Request Timeout) should not be used as it causes browsers "
            "and HTTP clients to automatically retry requests. Use 504 (Gateway Timeout) "
            "or 503 (Service Unavailable) instead."
        )
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from arguments if present
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # If no Request object found in args, check kwargs
            if request is None:
                request = kwargs.get('request')
            
            start_time = time.time()
            
            try:
                # Execute the original endpoint function with timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
                return result
                
            except asyncio.TimeoutError:
                process_time = time.time() - start_time
                
                # Use custom timeout handler if provided
                if custom_timeout_handler and request:
                    return custom_timeout_handler(request, process_time)
                
                # Create default timeout response
                content: Dict[str, Any] = {
                    "detail": timeout_message,
                    "timeout_seconds": timeout_seconds
                }
                
                if include_process_time:
                    content["processing_time"] = round(process_time, 3)
                
                return JSONResponse(
                    content=content,
                    status_code=timeout_status_code
                )
        
        return wrapper
    return decorator


# Alias for backward compatibility and convenience
endpoint_timeout = timeout
