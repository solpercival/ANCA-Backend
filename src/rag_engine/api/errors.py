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
    """The `error` object of the envelope: what went wrong and how to trace it."""

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
    """401: the request has no valid access token (missing, malformed, expired, or
    for an account that is no longer active)."""

    status_code, code, message = 401, ErrorCode.unauthorized, "Authentication required"
    headers = {"WWW-Authenticate": "Bearer"}


class InvalidCredentials(AppError):
    """401: login failed. One message for a wrong username and a wrong password, so
    the response doesn't reveal which usernames exist."""

    status_code, code = 401, ErrorCode.invalid_credentials
    message = "Incorrect username or password"
    headers = {"WWW-Authenticate": "Bearer"}


class SessionExpired(AppError):
    """401: the refresh session is gone or no longer valid; the user must log in again."""

    status_code, code, message = 401, ErrorCode.session_expired, "Session expired; log in again"
    headers = {"WWW-Authenticate": "Bearer"}


class Forbidden(AppError):
    """403: authenticated, but the caller's tier may not use this resource."""

    status_code, code, message = 403, ErrorCode.forbidden, "Insufficient tier for this resource"


class UnknownAlarmCode(AppError):
    """404: a well-formed alarm code that is not in the alarm catalogue."""

    status_code, code, message = 404, ErrorCode.unknown_alarm_code, "Alarm code not found"


class RetrievalUnavailable(AppError):
    """503: the alarm lookup or documentation search (database, embedder, reranker)
    could not run, or the orchestrator could not be built."""

    status_code, code, message = (
        503,
        ErrorCode.retrieval_unavailable,
        "Retrieval backend unavailable",
    )


class Conflict(AppError):
    """409: the resource being created already exists (e.g. a taken username)."""

    status_code, code, message = 409, ErrorCode.conflict, "Resource already exists"


class RateLimited(AppError):
    """429: too many attempts in the current window; carries a Retry-After header."""

    status_code, code, message = 429, ErrorCode.rate_limited, "Too many attempts; try again later"

    def __init__(self, retry_after: int):
        """retry_after: seconds until the caller may retry (sent as Retry-After)."""
        super().__init__(headers={"Retry-After": str(retry_after)})


class ModelUnavailable(AppError):
    """503: the LLM that writes the answer could not be reached or returned an error."""

    status_code, code, message = 503, ErrorCode.model_unavailable, "Model backend unavailable"


class AuthUnavailable(AppError):
    """503: the user database or session store behind authentication is unreachable."""

    status_code, code = 503, ErrorCode.auth_unavailable
    message = "Authentication backend unavailable"


class UpstreamTimeout(AppError):
    """504: a dependency (model server, database) did not answer in time."""

    status_code, code, message = 504, ErrorCode.upstream_timeout, "Upstream request timed out"


class RateLimitUnavailable(AppError):
    """503: the rate-limit counters (Redis) are unreachable, so the request is refused
    rather than let through unlimited."""

    status_code, code, message = (
        503,
        ErrorCode.rate_limit_unavailable,
        "Rate-limit backend unavailable",
    )
