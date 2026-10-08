"""Shared FastAPI dependencies: DB session, bearer auth, role guards."""
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from . import db
from .security import decode_token


def get_db():
    s = db.Session()
    try:
        yield s
    finally:
        s.close()


def user_from_token(token: str, session: Session):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token")
    u = session.get(db.User, int(payload["sub"]))
    if not u:
        raise HTTPException(401, "User not found")
    if u.status == "blocked":
        raise HTTPException(403, "Your account is blocked")
    return u


def current_user(authorization: str = Header(default=""),
                 session: Session = Depends(get_db)) -> db.User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    return user_from_token(authorization[7:], session)


def require_role(*roles):
    def guard(u: db.User = Depends(current_user)):
        if u.role not in roles:
            raise HTTPException(403, "Please select a user role.")
        return u
    return guard
