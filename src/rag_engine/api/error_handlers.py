import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from rag_engine.api.errors import AppError, ErrorBody, ErrorCode, ErrorDetail, ErrorResponse

log = logging.getLogger("rag_engine.errors")


def _json(status_code: int, body: ErrorBody, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content=ErrorResponse(error=body).model_dump(), headers=headers
    )


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or request.headers.get("x-request-id")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        # 5xx is our fault → log with stack; 4xx is the caller's → info
        if exc.status_code >= 500:
            log.exception("app_error code=%s", exc.code)
        return _json(exc.status_code, ErrorBody(
            code=exc.code, message=exc.message,
            request_id=_request_id(request), details=exc.details,
        ), exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        code = {401: ErrorCode.unauthorized, 403: ErrorCode.forbidden,
                404: ErrorCode.not_found, 409: ErrorCode.conflict,
                429: ErrorCode.rate_limited}.get(exc.status_code, ErrorCode.internal_error)
        return _json(exc.status_code, ErrorBody(
            code=code, message=str(exc.detail), request_id=_request_id(request)), exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        details = [ErrorDetail(field=".".join(str(p) for p in e["loc"][1:]), message=e["msg"])
                   for e in exc.errors()]
        return _json(status.HTTP_422_UNPROCESSABLE_ENTITY, ErrorBody(
            code=ErrorCode.validation_error, message="Request validation failed",
            request_id=_request_id(request), details=details))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("unhandled_error")                       # full detail to logs/Langfuse
        return _json(status.HTTP_500_INTERNAL_SERVER_ERROR, ErrorBody(
            code=ErrorCode.internal_error, message="Internal server error",  # generic to client
            request_id=_request_id(request)))