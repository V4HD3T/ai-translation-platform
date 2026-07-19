"""
Adds standard security-relevant response headers to every response.

This is a defense-in-depth measure -- none of these headers replace
proper input validation or auth checks, but they close off several classes
of browser-side attacks (clickjacking, MIME-sniffing, some XSS vectors)
essentially for free.

CSP here is deliberately conservative (default-src 'self') since this API
doesn't serve HTML/JS itself -- if you later add server-rendered pages or
Swagger UI in production, you'll need to loosen it for /docs specifically
(Swagger UI loads assets from a CDN by default).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.services.rate_limiter import api_rate_limiter, client_ip
from app.services.security_logging import log_event


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Note: microphone is deliberately NOT denied here. The frontend's
        # speech-recognition features (MicButton, pronunciation practice)
        # need it, and while today the SPA is served from a separate origin
        # (so this header wouldn't reach it), a future single-origin
        # deployment (e.g. FastAPI serving the built frontend from one
        # container) would silently break the mic with a very confusing
        # failure mode if microphone=() were sent.
        response.headers["Permissions-Policy"] = "geolocation=(), camera=()"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        # Only meaningful over HTTPS; harmless to send over HTTP (browsers ignore it there).
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


class GeneralRateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP request-rate backstop across the whole API (v0.0.8).

    Endpoint-specific limiters (the auth flows, /translate) enforce
    tight, targeted budgets; this is the coarse outer net that stops
    plain request flooding against everything else. /health is exempt
    because deployment platforms poll it aggressively, and a health check
    that can answer 429 reads as an outage.

    Returns JSONResponse directly instead of raising HTTPException:
    exceptions raised inside BaseHTTPMiddleware don't go through
    FastAPI's exception handlers, so a raise here would surface as a 500.
    """

    EXEMPT_PATHS = {"/health"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        key = client_ip(request)
        if not api_rate_limiter.check(key):
            log_event("rate_limit_exceeded", endpoint="global", key=key)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many attempts. Please wait a bit before trying again."},
                headers={"Retry-After": str(int(api_rate_limiter.window.total_seconds()))},
            )
        return await call_next(request)
