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
from starlette.responses import Response


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
