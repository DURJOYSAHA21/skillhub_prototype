"""Product features: course reviews, wishlist, in-app notifications."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, current_user

router = APIRouter(tags=["product"])


class ReviewIn(BaseModel):
    rating: int
    comment: str = ""


@router.get("/courses/{cid}/reviews")
def list_reviews(cid: int, session: Session = Depends(get_db)):
    rows = (session.query(db.Review).filter_by(course_id=cid)
            .order_by(db.Review.id.desc()).limit(50).all())
    out = []
    for r in rows:
        u = session.get(db.User, r.user_id)
        out.append({"id": r.id, "name": u.name if u else "", "rating": r.rating,
                    "comment": r.comment, "date": r.created.strftime("%Y-%m-%d")})
    return {"reviews": out}


@router.post("/courses/{cid}/reviews")
def add_review(cid: int, body: ReviewIn, session: Session = Depends(get_db),
               u: db.User = Depends(current_user)):
    if u.role != "learner":
        raise HTTPException(403, "Only learners can review courses.")
    c = session.get(db.Course, cid)
    if not c or c.status != "published":
        raise HTTPException(404, "Course not found.")
    if not session.query(db.Enrollment).filter_by(learner_id=u.id,
                                                  course_id=cid).first():
        raise HTTPException(403, "Please enroll in this course before reviewing.")
    if not (1 <= body.rating <= 5):
        raise HTTPException(400, "Rating must be between 1 and 5 stars.")
    own = session.query(db.Review).filter_by(course_id=cid, user_id=u.id).first()
    if own:
        delta = body.rating - own.rating
        own.rating = body.rating
        own.comment = body.comment.strip()
        base = c.rating * max(1, c.reviews) + delta
        c.rating = round(max(1.0, min(5.0, base / max(1, c.reviews))), 2)
    else:
        session.add(db.Review(course_id=cid, user_id=u.id, rating=body.rating,
                              comment=body.comment.strip()))
        c.rating = round((c.rating * c.reviews + body.rating) / (c.reviews + 1), 2)
        c.reviews += 1
    db.notify(session, c.mentor_id,
              "New %d-star review on '%s'" % (body.rating, c.title),
              "/course/%d" % cid)
    session.commit()
    return {"message": "Review saved.", "rating": c.rating, "reviews": c.reviews}


@router.get("/wishlist")
def my_wishlist(session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    out = []
    for w in session.query(db.Wishlist).filter_by(user_id=u.id).all():
        c = session.get(db.Course, w.course_id)
        if c and c.status == "published":
            m = session.get(db.User, c.mentor_id)
            out.append({"course_id": c.id, "title": c.title, "price": c.price,
                        "language": c.language, "rating": c.rating,
                        "mentor": m.name if m else ""})
    return {"courses": out}


@router.post("/wishlist/{cid}")
def toggle_wish(cid: int, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c:
        raise HTTPException(404, "Course not found.")
    w = session.query(db.Wishlist).filter_by(user_id=u.id, course_id=cid).first()
    if w:
        session.delete(w)
        session.commit()
        return {"saved": False, "message": "Removed from your saved list."}
    session.add(db.Wishlist(user_id=u.id, course_id=cid))
    session.commit()
    return {"saved": True, "message": "Saved for later."}


@router.get("/notifications")
def notifications(session: Session = Depends(get_db),
                  u: db.User = Depends(current_user)):
    rows = (session.query(db.Notification).filter_by(user_id=u.id)
            .order_by(db.Notification.id.desc()).limit(30).all())
    return {"notifications": [{"id": n.id, "message": n.message, "link": n.link,
                               "read": bool(n.read),
                               "date": n.created.strftime("%Y-%m-%d %H:%M")}
                              for n in rows],
            "unread": session.query(db.Notification).filter_by(
                user_id=u.id, read=False).count()}


@router.put("/notifications/read-all")
def read_all(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    session.query(db.Notification).filter_by(user_id=u.id, read=False) \
        .update({"read": True})
    session.commit()
    return {"message": "All marked as read."}


@router.put("/notifications/{nid}/read")
def read_one(nid: int, session: Session = Depends(get_db),
             u: db.User = Depends(current_user)):
    n = session.get(db.Notification, nid)
    if n and n.user_id == u.id:
        n.read = True
        session.commit()
    return {"message": "Ok."}