"""Skillhub API application entry point."""
import os
import time
from collections import defaultdict, deque
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from . import db
from . import security
from .routers import (auth, courses, enroll, assess, chat, admin, match, product,
                     mentor, learner, bot)

app = FastAPI(title="Skillhub API", description="One Platform to Learn Every Skill",
              version="1.0.0")

# CORS: restrict to the real frontend origin(s) in production via SKILLHUB_ORIGINS
# (comma-separated). Unset -> open (local dev convenience).
_origins = [o.strip() for o in os.environ.get("SKILLHUB_ORIGINS", "").split(",") if o.strip()]
if not _origins:
    _origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_methods=["*"],
                   allow_headers=["*"], allow_credentials=("*" not in _origins))

# Simple per-client rate limits for auth-sensitive endpoints: (max_requests, window_seconds).
_RATE_LIMITS = {
    "/auth/login": (10, 60),
    "/auth/signup": (5, 600),
    "/auth/verify": (15, 600),
    "/auth/forgot": (5, 600),
    "/auth/forgot-confirm": (15, 600),
    "/auth/change-password": (10, 60),
    "/pay/start": (10, 300),
}
_hits = defaultdict(deque)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if not security.is_production():
        return await call_next(request)
    if request.method == "POST":
        limit = _RATE_LIMITS.get(request.url.path)
        if limit:
            maxn, win = limit
            fwd = request.headers.get("x-forwarded-for", "")
            ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "")
            key = (request.url.path, ip)
            now = time.time()
            q = _hits[key]
            while q and now - q[0] > win:
                q.popleft()
            if len(q) >= maxn:
                return JSONResponse(status_code=429,
                                    content={"detail": "Too many requests, please slow down."})
            q.append(now)
    return await call_next(request)


@app.on_event("startup")
def startup():
    security.validate_production_config()
    db.init_db()


for r in (auth.router, courses.router, enroll.router, assess.router,
          chat.router, admin.router, match.router, product.router,
          mentor.router, learner.router, bot.router):
    app.include_router(r)


@app.get("/files/{name}")
def get_file(name: str):
    safe = os.path.basename(name)
    path = os.path.join(db.UPLOAD_DIR, safe)
    if not os.path.isfile(path):
        raise HTTPException(404, "File not found.")
    return FileResponse(path)


@app.get("/api/health")
@app.get("/health")
def health():
    s = db.Session()
    try:
        return {"ok": True, "users": s.query(db.User).count(),
                "courses": s.query(db.Course).count()}
    finally:
        s.close()