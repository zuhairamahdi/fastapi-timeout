# FastAPI Timeout - Installation and Development Guide

## For Users (Installing the Package)

### Install from PyPI (when published)
```bash
pip install fastapi-timeout
```

### Install from Source
```bash
git clone https://github.com/zuhairamahdi/fastapi-timeout.git
cd fastapi-timeout
pip install .
```

### Install for Development
```bash
git clone https://github.com/zuhairamahdi/fastapi-timeout.git
cd fastapi-timeout
pip install -e ".[dev]"
```

## Usage Examples

### Basic Usage
```python
from fastapi import FastAPI
from fastapi_timeout import TimeoutMiddleware

app = FastAPI()
app.add_middleware(TimeoutMiddleware, timeout_seconds=5.0)
```

### With Custom Configuration
```python
app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=10.0,
    timeout_status_code=408,
    timeout_message="Request took too long!",
    include_process_time=True
)
```

### With Custom Timeout Handler
```python
from fastapi import Request, Response
from fastapi.responses import JSONResponse

def my_timeout_handler(request: Request, process_time: float) -> Response:
    return JSONResponse(
        status_code=503,
        content={"error": "Service busy", "retry_after": 30}
    )

app.add_middleware(
    TimeoutMiddleware,
    timeout_seconds=5.0,
    custom_timeout_handler=my_timeout_handler
)
```

## Development

### Running Examples
```bash
# Basic example
python examples/basic_example.py

# Advanced example with custom handler
python examples/advanced_example.py
```

### Running Tests
```bash
pip install pytest pytest-asyncio httpx
pytest tests/
```

### Building the Package
```bash
pip install build
python -m build
```

### Publishing (for maintainers)
```bash
pip install twine
python -m build
twine upload dist/*
```

## Project Structure
```
fastapi-timeout/
├── fastapi_timeout/          # Main package
│   ├── __init__.py          # Package exports
│   ├── middleware.py        # Timeout middleware implementation
│   └── py.typed            # Type hints marker
├── examples/               # Usage examples
│   ├── basic_example.py    # Simple usage
│   └── advanced_example.py # Advanced features
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_middleware.py  # Middleware tests
├── main.py                # Demo application
├── pyproject.toml         # Modern Python packaging
├── setup.py              # Legacy setup (compatibility)
├── README.md             # Documentation
├── LICENSE               # MIT license
└── MANIFEST.in           # Package file inclusion rules
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout_seconds` | float | 30.0 | Maximum request processing time |
| `timeout_status_code` | int | 504 | HTTP status code for timeouts |
| `timeout_message` | str | "Request processing time exceeded limit" | Error message |
| `include_process_time` | bool | True | Include actual processing time in response |
| `custom_timeout_handler` | Callable | None | Custom timeout response handler |

## Response Format

Default timeout response:
```json
{
    "detail": "Request processing time exceeded limit",
    "timeout_seconds": 5.0,
    "processing_time": 5.002
}
```
