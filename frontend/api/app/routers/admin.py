"""Admin: user management, course approval, payment methods, analytics
(SRS items 16, 20, 21, 22, 23, 24)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _admin(u: db.User = Depends(current_user)):
    if u.role != "admin":
        raise HTTPException(403, "Admin only.")
    return u


@router.get("/users")
def list_users(role: str = "", status: str = "",
               session: Session = Depends(get_db), a: db.User = Depends(_admin)):
    q = session.query(db.User)
    if role:
        q = q.filter(db.User.role == role)
    if status:
        q = q.filter(db.User.status == status)
    return {"users": [{"id": x.id, "name": x.name, "email": x.email, "phone": x.phone,
                       "role": x.role, "status": x.status,
                       "created": x.created.strftime("%Y-%m-%d")} for x in q.all()]}


class StatusIn(BaseModel):
    status: str


@router.put("/users/{uid}/status")
def set_status(uid: int, body: StatusIn, session: Session = Depends(get_db),
               a: db.User = Depends(_admin)):
    if body.status not in ("active", "blocked"):
        raise HTTPException(400, "Status must be active or blocked.")
    x = session.get(db.User, uid)
    if not x:
        raise HTTPException(404, "User not found.")
    if x.role == "admin":
        raise HTTPException(400, "Cannot change another admin.")
    x.status = body.status
    session.commit()
    return {"message": f"User {body.status}."}


@router.delete("/users/{uid}")
def delete_user(uid: int, session: Session = Depends(get_db),
                a: db.User = Depends(_admin)):
    x = session.get(db.User, uid)
    if not x:
        raise HTTPException(404, "User not found.")
    if x.role == "admin":
        raise HTTPException(400, "Cannot delete an admin.")
    session.delete(x)
    session.commit()
    return {"message": "User deleted."}


@router.get("/courses/pending")
def pending_courses(session: Session = Depends(get_db), a: db.User = Depends(_admin)):
    rows = session.query(db.Course).filter_by(status="pending").all()
    return {"courses": [{"id": c.id, "title": c.title, "mentor":
                         (session.get(db.User, c.mentor_id) or db.User(name="")).name,
                         "price": c.price, "language": c.language} for c in rows]}


class ApproveIn(BaseModel):
    status: str  # published | rejected | pending


@router.put("/courses/{cid}/status")
def approve_course(cid: int, body: ApproveIn, session: Session = Depends(get_db),
                   a: db.User = Depends(_admin)):
    if body.status not in ("published", "rejected", "pending"):
        raise HTTPException(400, "Invalid status.")
    c = session.get(db.Course, cid)
    if not c:
        raise HTTPException(404, "Course not found.")
    c.status = body.status
    session.commit()
    return {"message": f"Course {body.status}."}


@router.get("/payment-methods")
def list_pm(session: Session = Depends(get_db), a: db.User = Depends(_admin)):
    return {"methods": [{"id": m.id, "name": m.name, "account": m.account,
                         "status": m.status}
                        for m in session.query(db.PaymentMethod).all()]}


class PmIn(BaseModel):
    name: str
    account: str = ""


@router.post("/payment-methods")
def add_pm(body: PmIn, session: Session = Depends(get_db), a: db.User = Depends(_admin)):
    if not body.name.strip():
        raise HTTPException(400, "Name is required.")
    if session.query(db.PaymentMethod).filter_by(name=body.name.strip()).first():
        raise HTTPException(400, "Payment method already exists.")
    m = db.PaymentMethod(name=body.name.strip(), account=body.account)
    session.add(m)
    session.commit()
    return {"message": "Payment method added.", "id": m.id}


@router.put("/payment-methods/{mid}")
def toggle_pm(mid: int, body: StatusIn, session: Session = Depends(get_db),
              a: db.User = Depends(_admin)):
    if body.status not in ("active", "inactive"):
        raise HTTPException(400, "Status must be active or inactive.")
    m = session.get(db.PaymentMethod, mid)
    if not m:
        raise HTTPException(404, "Payment method not found.")
    m.status = body.status
    session.commit()
    return {"message": "Payment method updated."}


@router.get("/analytics")
def analytics(session: Session = Depends(get_db), a: db.User = Depends(_admin)):
    txns = session.query(db.Txn).all()
    by = {}
    for t in txns:
        by[t.status] = by.get(t.status, 0) + 1
    top = session.query(db.Course).filter_by(status="published") \
        .order_by(db.Course.rating.desc()).limit(5).all()
    return {
        "users": {r: session.query(db.User).filter_by(role=r).count()
                  for r in ("admin", "mentor", "learner")},
        "courses": {s: session.query(db.Course).filter_by(status=s).count()
                    for s in ("pending", "published", "rejected")},
        "enrollments": session.query(db.Enrollment).count(),
        "completed": session.query(db.Enrollment).filter_by(completed=True).count(),
        "transactions_by_status": by,
        "revenue": round(sum(t.amount for t in txns if t.status == "success"), 2),
        "top_courses": [{"title": c.title, "rating": c.rating} for c in top],
    }
