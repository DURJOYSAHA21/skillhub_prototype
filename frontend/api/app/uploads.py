"""Saving and serving user uploads safely.

Uploads are served from the same site as the app (and its login token), so a file
must never be rendered as a web page: only known media types open in the browser,
everything else is downloaded, and every response is locked down with nosniff + CSP.
"""
import os
import uuid
from fastapi import HTTPException
from fastapi.responses import FileResponse
from . import db

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
# Types the browser may show inline; anything else is sent as a download.
INLINE = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
          ".gif": "image/gif", ".webp": "image/webp", ".pdf": "application/pdf",
          ".mp4": "video/mp4", ".webm": "video/webm", ".mp3": "audio/mpeg",
          ".txt": "text/plain; charset=utf-8"}
MAX_BYTES = 20 * 1024 * 1024


def save_upload(file, images_only: bool = False) -> str:
    """Store an UploadFile under a random name and return that name."""
    base = os.path.basename((file.filename or "file").replace("\\", "/")) or "file"
    ext = os.path.splitext(base)[1].lower()
    if images_only and ext not in IMAGE_EXT:
        raise HTTPException(400, "Please choose a PNG, JPG, GIF or WebP image.")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "File is too large (20 MB max).")
    os.makedirs(db.UPLOAD_DIR, exist_ok=True)
    name = uuid.uuid4().hex[:10] + "-" + base
    with open(os.path.join(db.UPLOAD_DIR, name), "wb") as fh:
        fh.write(data)
    return name


def serve(name: str):
    safe = os.path.basename(name)
    path = os.path.join(db.UPLOAD_DIR, safe)
    if not safe or not os.path.isfile(path):
        raise HTTPException(404, "File not found.")
    ext = os.path.splitext(safe)[1].lower()
    headers = {"X-Content-Type-Options": "nosniff"}
    # Chrome's PDF viewer refuses to run inside a sandboxed document.
    if ext != ".pdf":
        headers["Content-Security-Policy"] = "default-src 'none'; img-src 'self'; media-src 'self'; sandbox"
    if ext in INLINE:
        return FileResponse(path, media_type=INLINE[ext], headers=headers)
    return FileResponse(path, media_type="application/octet-stream", filename=safe,
                        headers=headers)
