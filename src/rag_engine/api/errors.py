"""API error model: machine-readable codes, the JSON error envelope, and the
exceptions that produce them.

Raise an AppError subclass anywhere in request handling; the handlers in
error_handlers.py turn it into

    {"error": {"code": "...", "message": "...", "request_id": "...", "details": [...]}}

with the subclass's HTTP status and headers. Clients should branch on `code`,
never on `message`.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    """Stable error identifiers returned in `error.code`; part of the API contract."""

    # auth
    unauthorized = "unauthorized"
    forbidden = "forbidden"
    invalid_credentials = "invalid_credentials"
    session_expired = "session_expired"
    # request
    validation_error = "validation_error"
    payload_too_large = "payload_too_large"
    not_found = "not_found"
    conflict = "conflict"
    unknown_alarm_code = "unknown_alarm_code"
    # upstream / infra
    retrieval_unavailable = "retrieval_unavailable"
    model_unavailable = "model_unavailable"
    auth_unavailable = "auth_unavailable"
    upstream_timeout = "upstream_timeout"
    rate_limited = "rate_limited"
    rate_limit_unavailable = "rate_limit_unavailable"
    # catch-all
    internal_error = "internal_error"


class ErrorDetail(BaseModel):
    """One problem with the request, e.g. a failed field validation."""

    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    request_id: str | None = None  # echoes X-Request-ID so logs can be matched to a report
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Top-level envelope: every error response body is {"error": ErrorBody}."""

    error: ErrorBody


class AppError(Exception):
    """Base for errors that map to a specific HTTP response.

    Subclasses set status_code, code, message and optionally headers as class
    attributes; a raise site may override the message, add details, or add headers.
    """

    status_code: int = 500
    code: ErrorCode = ErrorCode.internal_error
    message: str = "Internal server error"
    headers: dict[str, str] | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        details: list[ErrorDetail] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.message = message or self.message
        self.details = details or []
        self.headers = headers or self.headers
        super().__init__(self.message)


# --- concrete errors (401s carry WWW-Authenticate: Bearer per RFC 6750) ----------


class Unauthorized(AppError):
    status_code, code, message = 401, ErrorCode.unauthorized, "Authentication required"
    headers = {"WWW-Authenticate": "Bearer"}


class InvalidCredentials(AppError):
    status_code, code = 401, ErrorCode.invalid_credentials
    message = "Incorrect username or password"
    headers = {"WWW-Authenticate": "Bearer"}


class SessionExpired(AppError):
    status_code, code, message = 401, ErrorCode.session_expired, "Session expired; log in again"
    headers = {"WWW-Authenticate": "Bearer"}


class Forbidden(AppError):
    status_code, code, message = 403, ErrorCode.forbidden, "Insufficient tier for this resource"


class UnknownAlarmCode(AppError):
    status_code, code, message = 404, ErrorCode.unknown_alarm_code, "Alarm code not found"


class RetrievalUnavailable(AppError):
    status_code, code, message = (
        503,
        ErrorCode.retrieval_unavailable,
        "Retrieval backend unavailable",
    )


class Conflict(AppError):
    status_code, code, message = 409, ErrorCode.conflict, "Resource already exists"


class RateLimited(AppError):
    status_code, code, message = 429, ErrorCode.rate_limited, "Too many attempts; try again later"

    def __init__(self, retry_after: int):
        """retry_after: seconds until the caller may retry (sent as Retry-After)."""
        super().__init__(headers={"Retry-After": str(retry_after)})


class ModelUnavailable(AppError):
    status_code, code, message = 503, ErrorCode.model_unavailable, "Model backend unavailable"


class AuthUnavailable(AppError):
    status_code, code = 503, ErrorCode.auth_unavailable
    message = "Authentication backend unavailable"


class UpstreamTimeout(AppError):
    status_code, code, message = 504, ErrorCode.upstream_timeout, "Upstream request timed out"


class RateLimitUnavailable(AppError):
    status_code, code, message = (
        503,
        ErrorCode.rate_limit_unavailable,
        "Rate-limit backend unavailable",
    )
