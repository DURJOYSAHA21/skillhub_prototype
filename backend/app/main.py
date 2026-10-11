"""Skillhub API application entry point."""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from . import db
from .routers import auth, courses, enroll, assess, chat, admin, match, product

app = FastAPI(title="Skillhub API", description="One Platform to Learn Every Skill",
              version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])


@app.on_event("startup")
def startup():
    db.init_db()


for r in (auth.router, courses.router, enroll.router, assess.router,
          chat.router, admin.router, match.router, product.router):
    app.include_router(r)


@app.get("/files/{name}")
def get_file(name: str):
    safe = os.path.basename(name)
    path = os.path.join(db.UPLOAD_DIR, safe)
    if not os.path.isfile(path):
        raise HTTPException(404, "File not found.")
    return FileResponse(path)


@app.get("/api/health")
def health():
    s = db.Session()
    try:
        return {"ok": True, "users": s.query(db.User).count(),
                "courses": s.query(db.Course).count(),
                "enrollments": s.query(db.Enrollment).count()}
    finally:
        s.close()
