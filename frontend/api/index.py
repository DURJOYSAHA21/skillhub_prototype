"""Vercel Python serverless entry: exposes the FastAPI app as an ASGI callable.

Vercel routes every request under /api/index (and subpaths) here while keeping
the full URL path, so we strip the function-mount prefix before handing the
request to FastAPI. Requests like /api/auth/login are rewritten to
/api/index/auth/login by vercel.json, which also gets stripped here.
"""
import re
import sys, os

if os.environ.get('VERCEL'):
    os.environ.setdefault('SKILLHUB_DB', '/tmp/skillhub.db')
    os.environ.setdefault('SKILLHUB_UPLOADS', '/tmp/sh_uploads')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.main import app as fastapi_app  # noqa: E402

_STRIP = re.compile(r"^/api(?:/index)?(?=/|$)(?P<rest>/.*)?$")


async def app(scope, receive, send):
    if scope.get("type") == "http":
        m = _STRIP.match(scope.get("path", "/"))
        if m:
            scope = dict(scope)
            new_path = m.group("rest") or "/"
            scope["path"] = new_path
            scope["raw_path"] = new_path.encode("utf-8")
    await fastapi_app(scope, receive, send)