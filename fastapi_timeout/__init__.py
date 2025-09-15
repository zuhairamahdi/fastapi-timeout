"""
FastAPI Timeout Middleware

A configurable timeout middleware for FastAPI applications that automatically
handles request timeouts with customizable error responses.
"""

from .middleware import TimeoutMiddleware, timeout, endpoint_timeout, timeout_middleware

__version__ = "0.1.1-2"
__all__ = ["TimeoutMiddleware", "timeout", "endpoint_timeout", "timeout_middleware"]
