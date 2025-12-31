"""
Global Error Handler Middleware

Catches all exceptions and converts them to standardized JSON error responses.
Handles both custom APIError exceptions and standard FastAPI/Pydantic errors.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError as PydanticValidationError
from typing import Union
import logging

from ..utils.errors import APIError

logger = logging.getLogger(__name__)


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handle custom APIError exceptions.

    Returns standardized error response format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "field": "optional_field_name",
            "details": {}
        }
    }
    """
    logger.warning(
        f"API Error: {exc.code} - {exc.message} "
        f"(path: {request.url.path}, method: {request.method})"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException.
    Convert to standardized error format for consistency.
    """
    # Map HTTP status codes to error codes
    status_code_to_error_code = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_REQUIRED",
        403: "INSUFFICIENT_PERMISSIONS",
        404: "RESOURCE_NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "RESOURCE_CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE"
    }

    error_code = status_code_to_error_code.get(exc.status_code, "UNKNOWN_ERROR")

    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} "
        f"(path: {request.url.path}, method: {request.method})"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": str(exc.detail),
                "details": {}
            }
        }
    )


async def validation_error_handler(
    request: Request,
    exc: Union[RequestValidationError, PydanticValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors from request body/query params.
    Converts validation errors to user-friendly format.
    """
    errors = []

    # Extract validation errors
    if isinstance(exc, RequestValidationError):
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
    else:
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })

    logger.warning(
        f"Validation Error: {len(errors)} field(s) failed validation "
        f"(path: {request.url.path}, method: {request.method})"
    )

    # Return first error as main message, include all in details
    first_error = errors[0] if errors else {"field": "unknown", "message": "Validation failed"}

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"{first_error['field']}: {first_error['message']}",
                "field": first_error['field'],
                "details": {
                    "validation_errors": errors
                }
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.
    Logs full error details but returns sanitized response to client.
    """
    # Log full exception details for debugging
    logger.error(
        f"Unexpected error: {type(exc).__name__}: {str(exc)} "
        f"(path: {request.url.path}, method: {request.method})",
        exc_info=True
    )

    # Don't expose internal error details to client in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {
                    "error_type": type(exc).__name__
                }
            }
        }
    )


def register_error_handlers(app):
    """
    Register all error handlers with the FastAPI application.

    Call this in main.py after creating the app instance:
        from .middleware.error_handler import register_error_handlers
        register_error_handlers(app)
    """
    # Custom API errors
    app.add_exception_handler(APIError, api_error_handler)

    # FastAPI built-in exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("✅ Error handlers registered")
