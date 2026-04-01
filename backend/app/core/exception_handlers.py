"""
Global exception handlers — catch unhandled errors and return structured responses.

Consistent error response format: {"detail": "error message"}
This matches FastAPI's built-in HTTPException format so all errors look the same.
"""
import logging

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger("app.exceptions")


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions.

    Returns a structured JSON error response instead of a raw 500 error.
    Logs the full traceback for debugging.
    """
    logger.error(
        f"Unhandled error on {request.method} {request.url.path}: {type(exc).__name__}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with a consistent format.

    Extracts the first error message for a clean, user-friendly response
    while keeping the full validation details in the body for debugging.
    """
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = " → ".join(str(loc) for loc in first_error.get("loc", []))
    message = first_error.get("msg", "Validation error")

    return JSONResponse(
        status_code=422,
        content={
            "detail": f"Invalid input: {field}: {message}" if field else f"Invalid input: {message}",
            "errors": [
                {
                    "field": " → ".join(str(loc) for loc in err.get("loc", [])),
                    "message": err.get("msg", ""),
                    "type": err.get("type", "")
                }
                for err in errors
            ]
        }
    )
