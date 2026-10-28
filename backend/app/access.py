"""Optional protections for a public deployment."""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

LIMITED_PATHS = ("/chat", "/compare", "/guarded-chat")
WINDOW_SECONDS = 3600


def extra_origins() -> list[str]:
    return [
        o.strip() for o in os.getenv("AEGIS_CORS_ORIGINS", "").split(",") if o.strip()
    ]


def client_id(request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int, clock=time.monotonic):
        super().__init__(app)
        self.limit, self.clock = limit, clock
        self.hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request, call_next):
        if request.method == "POST" and request.url.path in LIMITED_PATHS:
            now, hits = self.clock(), self.hits[client_id(request)]
            while hits and now - hits[0] > WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= self.limit:
                return JSONResponse(
                    {"detail": f"Rate limit reached: {self.limit} questions per hour."},
                    status_code=429,
                )
            hits.append(now)
        return await call_next(request)


def rate_limit() -> int:
    try:
        return max(0, int(os.getenv("AEGIS_RATE_LIMIT_PER_HOUR", "0")))
    except ValueError:
        return 0
