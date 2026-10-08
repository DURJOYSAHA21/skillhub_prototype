"""Auth & profile endpoints (SRS items 1-6)."""
import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, current_user
from ..security import (hash_password, verify_password, password_ok, phone_ok,
                        create_token, gen_otp)

router = APIRouter(prefix="/auth", tags=["auth"])
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


class SignupIn(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    confirm_password: str
    role: str
    lang: str = "en"


def _issue(session, email, purpose, owner_id=None):
    code = gen_otp()
    session.query(db.Otp).filter_by(email=email, purpose=purpose,
                                    used=False).update({"used": True})
    session.add(db.Otp(email=email, code=code, purpose=purpose, owner_id=owner_id,
                       expires=datetime.utcnow() + timedelta(minutes=5)))
    session.commit()
    return code

def _public(u: db.User):
    return {"id": u.id, "name": u.name, "email": u.email, "phone": u.phone,
            "role": u.role, "lang": u.lang, "status": u.status}


@router.post("/signup")
def signup(body: SignupIn, session: Session = Depends(get_db)):
    if not body.name.strip() or not body.email or not body.phone or \
            not body.password or not body.confirm_password or not body.role:
        raise HTTPException(400, "Please enter all required information.")
    if body.role not in ("admin", "mentor", "learner"):
        raise HTTPException(400, "Please select a user role.")
    if not EMAIL_RE.match(body.email):
        raise HTTPException(400, "Invalid email format.")
    if not phone_ok(body.phone):
        raise HTTPException(400, "Phone number must be an 11-digit Bangladeshi number (start 01).")
    if body.password != body.confirm_password:
        raise HTTPException(400, "Password and Confirm Password must match.")
    if not password_ok(body.password):
        raise HTTPException(400, "Password must be >=8 chars with 1 uppercase and 1 number.")
    if session.query(db.User).filter_by(email=body.email).first():
        raise HTTPException(400, "Email is already registered.")
    u = db.User(name=body.name.strip(), email=body.email.lower(),
                phone=body.phone, password_hash=hash_password(body.password),
                role=body.role, lang=body.lang, status="unverified")
    session.add(u)
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise HTTPException(400, "Email or phone already registered.")
    code = _issue(session, u.email, "signup", u.id)
    return {"message": "Account created. Verify OTP to activate.", "dev_otp": code}


class VerifyIn(BaseModel):
    email: str
    otp: str


@router.post("/verify")
def verify(body: VerifyIn, session: Session = Depends(get_db)):
    u = session.query(db.User).filter_by(email=body.email.lower()).first()
    if not u:
        raise HTTPException(400, "Email not found.")
    if u.status == "active":
        raise HTTPException(400, "Account already verified.")
    if not db.check_otp(session, u.email, "signup", body.otp, u.id):
        raise HTTPException(400, "Invalid or expired OTP.")
    u.status = "active"
    session.commit()
    return {"message": "Email verified successfully.", "token": create_token(u.id, u.role),
            "user": _public(u)}


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginIn, session: Session = Depends(get_db)):
    if not body.email or not body.password:
        raise HTTPException(400, "Email and Password are required.")
    u = session.query(db.User).filter_by(email=body.email.lower()).first()
    if not u:
        raise HTTPException(400, "Email not found.")
    if u.status == "blocked":
        raise HTTPException(403, "Your account has been blocked by the admin.")
    if u.locked_until and u.locked_until > datetime.utcnow():
        raise HTTPException(403, "Too many failed attempts. Try again later.")
    if not verify_password(body.password, u.password_hash):
        u.fail_count = (u.fail_count or 0) + 1
        if u.fail_count >= 5:
            u.locked_until = datetime.utcnow() + timedelta(minutes=30)
            u.fail_count = 0
        session.commit()
        raise HTTPException(400, "Incorrect password.")
    u.fail_count = 0
    u.locked_until = None
    session.commit()
    return {"token": create_token(u.id, u.role), "user": _public(u)}

class EmailIn(BaseModel):
    email: str


class ResetIn(BaseModel):
    email: str
    otp: str
    new_password: str
    confirm_password: str


@router.post("/forgot")
def forgot(body: EmailIn, session: Session = Depends(get_db)):
    if not body.email:
        raise HTTPException(400, "Email is required.")
    u = session.query(db.User).filter_by(email=body.email.lower()).first()
    if not u:
        raise HTTPException(400, "Email not found.")
    code = _issue(session, u.email, "reset", u.id)
    return {"message": "OTP sent to registered email.", "dev_otp": code}


@router.post("/forgot-confirm")
def forgot_confirm(body: ResetIn, session: Session = Depends(get_db)):
    u = session.query(db.User).filter_by(email=body.email.lower()).first()
    if not u:
        raise HTTPException(400, "Email not found.")
    if body.new_password != body.confirm_password:
        raise HTTPException(400, "Password and Confirm Password must match.")
    if not password_ok(body.new_password):
        raise HTTPException(400, "Password must be >=8 chars with 1 uppercase and 1 number.")
    if not db.check_otp(session, u.email, "reset", body.otp, u.id):
        raise HTTPException(400, "Invalid or expired OTP.")
    u.password_hash = hash_password(body.new_password)
    u.fail_count = 0
    u.locked_until = None
    session.commit()
    return {"message": "Password updated successfully."}


class ChangePwIn(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


@router.post("/change-password")
def change_pw(body: ChangePwIn, session: Session = Depends(get_db),
              u: db.User = Depends(current_user)):
    if not verify_password(body.current_password, u.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    if body.new_password != body.confirm_password:
        raise HTTPException(400, "Password and Confirm Password must match.")
    if not password_ok(body.new_password):
        raise HTTPException(400, "Password must be >=8 chars with 1 uppercase and 1 number.")
    u.password_hash = hash_password(body.new_password)
    session.commit()
    return {"message": "Password changed successfully."}


@router.get("/me")
def me(u: db.User = Depends(current_user)):
    return _public(u)


class ProfileIn(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    dob: str = ""
    gender: str = ""
    lang: str = ""


@router.put("/profile")
def update_profile(body: ProfileIn, session: Session = Depends(get_db),
                   u: db.User = Depends(current_user)):
    name = body.name.strip() or u.name
    email = (body.email or u.email).lower()
    phone = body.phone or u.phone
    if not name:
        raise HTTPException(400, "Please enter all required information.")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Invalid email format.")
    if not phone_ok(phone):
        raise HTTPException(400, "Phone number must be an 11-digit Bangladeshi number (start 01).")
    dup = session.query(db.User).filter(db.User.id != u.id,
                                        (db.User.email == email) | (db.User.phone == phone)).first()
    if dup:
        raise HTTPException(400, "Email or phone already registered by another user.")
    if body.dob and body.dob > datetime.utcnow().date().isoformat():
        raise HTTPException(400, "Date of birth cannot be a future date.")
    if body.lang and body.lang not in ("en", "bn"):
        raise HTTPException(400, "Unsupported language.")
    u.name, u.email, u.phone = name, email, phone
    u.dob = body.dob or u.dob
    u.gender = body.gender or u.gender
    u.lang = body.lang or u.lang          # req #13: preference persisted per user
    session.commit()
    return {"message": "Profile info updated successfully.", "user": _public(u)}
