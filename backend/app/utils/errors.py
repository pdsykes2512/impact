"""
Standardized Error Classes for API

This module defines custom exception classes for consistent error handling
across all API routes. All errors follow a standard format for frontend consumption.

Error Response Format:
{
    "error": {
        "code": "RESOURCE_NOT_FOUND",     # Machine-readable error code
        "message": "Patient P-123 not found",  # Human-readable message
        "field": "patient_id",             # Optional: field that caused error
        "details": {}                      # Optional: additional context
    }
}
"""

from typing import Optional, Dict, Any


class APIError(Exception):
    """Base class for all API errors"""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 500,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.field = field
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON response"""
        error_dict = {
            "code": self.code,
            "message": self.message
        }
        if self.field:
            error_dict["field"] = self.field
        if self.details:
            error_dict["details"] = self.details
        return {"error": error_dict}


class ResourceNotFoundError(APIError):
    """Raised when a requested resource doesn't exist (404)"""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            field=field,
            details=details
        )


class ValidationError(APIError):
    """Raised when request data fails validation (422)"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            field=field,
            details=details
        )


class AuthenticationError(APIError):
    """Raised when authentication fails (401)"""

    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_REQUIRED",
            status_code=401,
            details=details
        )


class AuthorizationError(APIError):
    """Raised when user lacks permission for action (403)"""

    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if required_permission:
            message = f"{message}: requires '{required_permission}' permission"
        super().__init__(
            message=message,
            code="INSUFFICIENT_PERMISSIONS",
            status_code=403,
            details=details
        )


class ConflictError(APIError):
    """Raised when resource already exists or conflicts with existing data (409)"""

    def __init__(
        self,
        resource_type: str,
        conflict_field: str,
        conflict_value: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{resource_type} with {conflict_field}='{conflict_value}' already exists"
        super().__init__(
            message=message,
            code="RESOURCE_CONFLICT",
            status_code=409,
            field=conflict_field,
            details=details
        )


class DatabaseError(APIError):
    """Raised when database operation fails (500)"""

    def __init__(
        self,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Database operation failed: {operation}"
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=500,
            details=details
        )


class ExternalServiceError(APIError):
    """Raised when external service call fails (503)"""

    def __init__(
        self,
        service_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"External service '{service_name}' unavailable"
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=503,
            details=details
        )


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if retry_after:
            details = details or {}
            details["retry_after_seconds"] = retry_after
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


class InvalidStateError(APIError):
    """Raised when operation is invalid in current state (400)"""

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if current_state:
            details = details or {}
            details["current_state"] = current_state
        super().__init__(
            message=message,
            code="INVALID_STATE",
            status_code=400,
            details=details
        )
