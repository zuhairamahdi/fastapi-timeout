"""
FastAPI Timeout Middleware

A configurable timeout middleware for FastAPI applications that automatically
handles request timeouts with customizable error responses.
"""

from .middleware import TimeoutMiddleware

__version__ = "0.1.0"
__all__ = ["TimeoutMiddleware"]
