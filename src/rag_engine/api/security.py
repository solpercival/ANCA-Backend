"""
HTTP hardening via host validation, security response headers, and compression.

    TrustedHost  -> rejects a forged Host header before any work is done
    SecurityHeaders -> stamps every response, including errors and CORS preflights
    GZip -> compresses bodies over the configured size
    CORS -> (added by main) browser access rules

Starlette applies the most recently added middleware first, so these are added in
reverse of the above list.
"""

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request
from starlette.responses import Response

from rag_engine.config import Settings

# Applied to every response
SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",        # no MIME sniffing of a JSON body into HTML
    "x-frame-options": "DENY",                  # legacy clickjacking guard; CSP covers modern browsers
    "referrer-policy": "no-referrer",           # alarm codes must not leak in Referer headers
    "cross-origin-opener-policy": "same-origin",
    "permissions-policy": "geolocation=(), camera=(), microphone=()",
}

# An API response should load nothing and frame nothing.
API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"

# Swagger and ReDoc pull scripts and styles from a CDN, so the API policy would break
# them. They get no CSP rather than a policy that silently blanks the page.
DOCS_PATHS = frozenset({"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"})


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add the standard security headers to every response.

    Uses setdefault throughout, so a route that deliberately sets its own policy
    keeps it. HSTS is sent only over HTTPS: browsers ignore it on plain HTTP
    """

    def __init__(self, app, *, hsts_max_age: int = 63072000):
        super().__init__(app)
        self._hsts = f"max-age={hsts_max_age}; includeSubDomains"

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)

        if request.url.path not in DOCS_PATHS:
            response.headers.setdefault("content-security-policy", API_CSP)

        # url.scheme is https only when TLS terminated here or uvicorn runs with
        # --proxy-headers and the proxy sets X-Forwarded-Proto.
        if request.url.scheme == "https":
            response.headers.setdefault("strict-transport-security", self._hsts)

        return response


def add_security_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Install compression, security headers and host validation, outermost last.

    Call after the CORS middleware is added, so host checking and security headers
    wrap CORS and apply to preflight responses too.
    """
    app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)
    app.add_middleware(SecurityHeadersMiddleware, hsts_max_age=settings.hsts_max_age)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
