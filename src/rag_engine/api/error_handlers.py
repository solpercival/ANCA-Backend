"""Exception handlers that render every error as the ErrorResponse envelope.

Registered once at app start (register_error_handlers). Covers the app's own
AppError subclasses, framework HTTP errors, request validation failures, and a
catch-all that logs the full exception but returns only a generic 500 body, so
internals never leak to clients.
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from rag_engine.api.errors import AppError, ErrorBody, ErrorCode, ErrorDetail, ErrorResponse

log = logging.getLogger("rag_engine.errors")


def _json(status_code: int, body: ErrorBody, headers: dict[str, str] | None = None,) -> JSONResponse:
    headers = dict(headers or {})
    # Set the id here rather than relying on the request-id middleware: the catch-all
    # handler runs outside all middleware, and the middleware's own early 413 returns
    # never reach the line that adds it, so those responses would lose the header.
    if body.request_id:
        headers.setdefault("x-request-id", body.request_id)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(error=body).model_dump(),
        headers=headers,
    )


def _request_id(request: Request) -> str | None:
    # set by the request-id middleware in main.py; fall back to the raw header
    return getattr(request.state, "request_id", None) or request.headers.get("x-request-id")


def register_error_handlers(app: FastAPI) -> None:
    """Attach the error handlers to `app`."""

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
        # framework errors (unknown route, wrong method, raised HTTPException):
        # map the status to the closest ErrorCode
        code = {401: ErrorCode.unauthorized, 403: ErrorCode.forbidden,
                404: ErrorCode.not_found, 409: ErrorCode.conflict,
                413: ErrorCode.payload_too_large, 429: ErrorCode.rate_limited}.get(
                    exc.status_code, ErrorCode.internal_error
                )
        return _json(exc.status_code, ErrorBody(
            code=code, message=str(exc.detail), request_id=_request_id(request)),
            headers=dict(exc.headers or {}))

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