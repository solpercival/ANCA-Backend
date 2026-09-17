from enum import StrEnum

from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    # auth
    unauthorized = "unauthorized"
    forbidden = "forbidden"
    invalid_credentials = "invalid_credentials"
    session_expired = "session_expired"
    # request
    validation_error = "validation_error"
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
    field: str | None = None
    message: str


class ErrorBody(BaseModel):
    code: ErrorCode
    message: str
    request_id: str | None = None
    details: list[ErrorDetail] = Field(default_factory=list)

class ErrorResponse(BaseModel):
    error: ErrorBody

class AppError(Exception):
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


class Unauthorized(AppError):
    status_code, code, message = 401, ErrorCode.unauthorized, "Authentication required"
    headers = {"WWW-Authenticate": "Bearer"}

class InvalidCredentials(AppError):
    status_code, code = 401, ErrorCode.invalid_credentials
    message = "Incorrect username or password"
    headers = {"WWW-Authenticate": "Bearer"}

class SessionExpired(AppError):
    status_code, code, message = 401, ErrorCode.session_expired, "Session expired; log in again"

class Forbidden(AppError):
    status_code, code, message = 403, ErrorCode.forbidden, "Insufficient tier for this resource"

class UnknownAlarmCode(AppError):
    status_code, code, message = 404, ErrorCode.unknown_alarm_code, "Alarm code not found"

class RetrievalUnavailable(AppError): 
    status_code, code, message = (503, ErrorCode.retrieval_unavailable, "Retrieval backend unavailable", )
class Conflict(AppError):
    status_code, code, message = 409, ErrorCode.conflict, "Resource already exists"

class RateLimited(AppError):
    status_code, code, message = 429, ErrorCode.rate_limited, "Too many attempts; try again later"

    def __init__(self, retry_after: int):
        super().__init__(headers={"Retry-After": str(retry_after)})

class ModelUnavailable(AppError):
    status_code, code, message = 503, ErrorCode.model_unavailable, "Model backend unavailable"

class AuthUnavailable(AppError):
    status_code, code = 503, ErrorCode.auth_unavailable
    message = "Authentication backend unavailable"

class UpstreamTimeout(AppError):
    status_code, code, message = 504, ErrorCode.upstream_timeout, "Upstream request timed out"

class RateLimitUnavailable(AppError):
    status_code, code, message = (503,ErrorCode.rate_limit_unavailable,"Rate-limit backend unavailable", )

