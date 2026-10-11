"""Enrollment, simulated bank payment, transaction history, receipts
(SRS items 8, 17, 18, 19)."""
import random, re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, current_user
from ..reports import receipt_pdf

router = APIRouter(tags=["enroll"])


class FreeIn(BaseModel):
    course_id: int


@router.post("/enroll/free")
def enroll_free(body: FreeIn, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    if u.role != "learner":
        raise HTTPException(403, "Only learners can enroll.")
    c = session.get(db.Course, body.course_id)
    if not c or c.status != "published":
        raise HTTPException(404, "Course not found.")
    if c.price > 0:
        raise HTTPException(400, "This is a paid course. Use the payment flow.")
    if session.query(db.Enrollment).filter_by(learner_id=u.id, course_id=c.id).first():
        raise HTTPException(400, "Already enrolled in this course.")
    session.add(db.Enrollment(learner_id=u.id, course_id=c.id))
    session.commit()
    db.notify(session, c.mentor_id,
              "%s enrolled in '%s'" % (u.name, c.title), "/dashboard")
    return {"message": "Enrolled successfully.", "course": c.title}


class PayStartIn(BaseModel):
    course_id: int
    method: str
    card_number: str
    pin: str


@router.post("/pay/start")
def pay_start(body: PayStartIn, session: Session = Depends(get_db),
              u: db.User = Depends(current_user)):
    if u.role != "learner":
        raise HTTPException(403, "Only learners can pay.")
    c = session.get(db.Course, body.course_id)
    if not c or c.status != "published" or c.price <= 0:
        raise HTTPException(404, "Paid course not found.")
    pm = session.query(db.PaymentMethod).filter_by(name=body.method,
                                                   status="active").first()
    if not pm:
        raise HTTPException(400, "Payment method is not available.")
    if not re.fullmatch(r"\d{12,19}", body.card_number):
        raise HTTPException(400, "Card number must be 12-19 digits.")
    if not re.fullmatch(r"\d{4,6}", body.pin):
        raise HTTPException(400, "PIN must be 4-6 digits.")
    from .auth import _issue
    code, sent = _issue(session, u.email, "payment", u.id)
    out = {"message": f"OTP sent to {u.email} by the bank (simulated).",
           "amount": c.price}
    if not sent:
        out["dev_otp"] = code
    return out


class PayConfirmIn(BaseModel):
    course_id: int
    otp: str
    method: str = ""
    card_number: str = ""


@router.post("/pay/confirm")
def pay_confirm(body: PayConfirmIn, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    c = session.get(db.Course, body.course_id)
    if not c:
        raise HTTPException(404, "Course not found.")
    if not db.check_otp(session, u.email, "payment", body.otp, u.id):
        session.add(db.Txn(learner_id=u.id, course_id=c.id, amount=c.price,
                           method=body.method, status="failed",
                           ref="SH-FAIL-" + str(random.randint(1000, 9999))))
        session.commit()
        raise HTTPException(400, "Payment failed, try again.")
    ref = "SH-" + datetime.utcnow().strftime("%Y%m%d") + "-" + str(random.randint(1000, 9999))
    txn = db.Txn(learner_id=u.id, course_id=c.id, amount=c.price,
                 method=body.method or "Bank", card_last4=(body.card_number or "0000")[-4:],
                 status="success", ref=ref)
    session.add(txn)
    if not session.query(db.Enrollment).filter_by(learner_id=u.id, course_id=c.id).first():
        session.add(db.Enrollment(learner_id=u.id, course_id=c.id))
    session.commit()
    db.notify(session, u.id,
              "Payment confirmed for '%s' (%s)" % (c.title, ref),
              "/learn/%d" % c.id)
    db.notify(session, c.mentor_id,
              "New sale: '%s' bought by %s" % (c.title, u.name), "/dashboard")
    return {"message": "Payment successful. Course enrolled.", "txn_id": txn.id,
            "receipt_no": ref}


def _txn_rows(session, rows):
    return [{"id": t.id, "ref": t.ref, "date": t.created.strftime("%Y-%m-%d %H:%M"),
             "learner": (session.get(db.User, t.learner_id) or db.User(name="")).name,
             "course": (session.get(db.Course, t.course_id) or db.Course(title="")).title,
             "amount": t.amount, "method": t.method, "card_last4": t.card_last4,
             "status": t.status} for t in rows]


@router.get("/txns/me")
def txns_me(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    rows = session.query(db.Txn).filter_by(learner_id=u.id).order_by(db.Txn.id.desc()).all()
    return {"transactions": _txn_rows(session, rows)}


@router.get("/txns/mentor")
def txns_mentor(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    if u.role != "mentor":
        raise HTTPException(403, "Mentor only.")
    cids = [c.id for c in session.query(db.Course).filter_by(mentor_id=u.id).all()]
    rows = session.query(db.Txn).filter(db.Txn.course_id.in_(cids)).order_by(db.Txn.id.desc()).all()
    total = sum(t.amount for t in rows if t.status == "success")
    return {"transactions": _txn_rows(session, rows), "total_earned": total}


@router.get("/txns/admin")
def txns_admin(status: str = "", date_from: str = "", date_to: str = "",
               session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    if u.role != "admin":
        raise HTTPException(403, "Admin only.")
    q = session.query(db.Txn)
    if status:
        q = q.filter(db.Txn.status == status)
    if date_from:
        q = q.filter(db.Txn.created >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.filter(db.Txn.created <= datetime.fromisoformat(date_to) +
                    timedelta(days=1))
    rows = q.order_by(db.Txn.id.desc()).all()
    total = sum(t.amount for t in rows if t.status == "success")
    return {"transactions": _txn_rows(session, rows), "total_revenue": total}


@router.get("/txns/{txn_id}/receipt")
def receipt(txn_id: int, session: Session = Depends(get_db),
            u: db.User = Depends(current_user)):
    t = session.get(db.Txn, txn_id)
    if not t:
        raise HTTPException(404, "Transaction not found.")
    c = session.get(db.Course, t.course_id)
    m = session.get(db.User, c.mentor_id)
    learner = session.get(db.User, t.learner_id)
    if u.role != "admin" and u.id not in (t.learner_id, m.id):
        raise HTTPException(403, "Not your transaction.")
    pdf = receipt_pdf(t, c.title, learner.name, m.name)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"inline; filename=receipt-{t.ref}.pdf"})
