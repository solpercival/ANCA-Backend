from enum import StrEnum
from pydantic import BaseModel, Field


class ErrorCode(StrEnum):
    # auth
    unauthorized = "unauthorized"
    forbidden = "forbidden"
    # request
    validation_error = "validation_error"
    not_found = "not_found"
    unknown_alarm_code = "unknown_alarm_code"
    # upstream / infra
    retrieval_unavailable = "retrieval_unavailable"
    model_unavailable = "model_unavailable"
    upstream_timeout = "upstream_timeout"
    rate_limited = "rate_limited"
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

    def __init__(self, message: str | None = None, *, details: list[ErrorDetail] | None = None):
        self.message = message or self.message
        self.details = details or []
        super().__init__(self.message)


class Unauthorized(AppError):
    status_code, code, message = 401, ErrorCode.unauthorized, "Authentication required"

class Forbidden(AppError):
    status_code, code, message = 403, ErrorCode.forbidden, "Insufficient tier for this resource"

class UnknownAlarmCode(AppError):
    status_code, code, message = 404, ErrorCode.unknown_alarm_code, "Alarm code not found"

class RetrievalUnavailable(AppError):
    status_code, code, message = 503, ErrorCode.retrieval_unavailable, "Retrieval backend unavailable"

class ModelUnavailable(AppError):
    status_code, code, message = 503, ErrorCode.model_unavailable, "Model backend unavailable"

class UpstreamTimeout(AppError):
    status_code, code, message = 504, ErrorCode.upstream_timeout, "Upstream request timed out"

