"""Course catalog + lessons (SRS items 7, 11, 12, 14, 15)."""
import os, uuid
from fastapi import APIRouter, Depends, File, HTTPException, Header, UploadFile
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, user_from_token
from ..security import decode_token

router = APIRouter(tags=["courses"])


def _optional_user(authorization: str, session: Session):
    if authorization and authorization.startswith("Bearer "):
        payload = decode_token(authorization[7:])
        if payload:
            return session.get(db.User, int(payload["sub"]))
    return None


def _course_dict(c: db.Course, mentor_name: str = ""):
    return {"id": c.id, "title": c.title, "description": c.description,
            "category": c.category, "language": c.language, "price": c.price,
            "type": c.type, "duration_hours": c.duration_hours, "status": c.status,
            "rating": c.rating, "reviews": c.reviews, "mentor": mentor_name,
            "mentor_id": c.mentor_id,
            "lessons": [{"id": l.id, "title": l.title, "position": l.position,
                         "file": bool(l.file)} for l in c.lessons],
            "quizzes": [{"id": q.id, "title": q.title, "published": q.published}
                        for q in c.quizzes if q.published],
            "assignments": [{"id": a.id, "title": a.title,
                             "instructions": a.instructions} for a in c.assignments]}


@router.get("/courses")
def list_courses(q: str = "", category: str = "", language: str = "",
                 max_price: float = 0, min_rating: float = 0,
                 mine: str = "", authorization: str = Header(default=""),
                 session: Session = Depends(get_db)):
    query = session.query(db.Course)
    me = _optional_user(authorization, session)
    if mine == "mentor" and me and me.role == "mentor":
        query = query.filter(db.Course.mentor_id == me.id)   # incl. pending
    else:
        query = query.filter(db.Course.status == "published")
    if q:
        like = f"%{q}%"
        query = query.filter(or_(db.Course.title.ilike(like),
                                 db.Course.description.ilike(like)))
    if category:
        query = query.filter(db.Course.category == category)
    if language:
        query = query.filter(db.Course.language == language)
    if max_price > 0:
        query = query.filter(db.Course.price <= max_price)
    if min_rating > 0:
        query = query.filter(db.Course.rating >= min_rating)
    out = []
    for c in query.order_by(db.Course.rating.desc()).all():
        m = session.get(db.User, c.mentor_id)
        out.append(_course_dict(c, m.name if m else ""))
    return {"count": len(out), "courses": out}


class CourseIn(BaseModel):
    title: str
    description: str = ""
    category: str = "Tech"
    language: str = "en"
    price: float = 0
    duration_hours: float = 4


from ..deps import current_user


def _save_upload(file: UploadFile) -> str:
    os.makedirs(db.UPLOAD_DIR, exist_ok=True)
    name = uuid.uuid4().hex[:10] + "-" + os.path.basename(file.filename or "file")
    with open(os.path.join(db.UPLOAD_DIR, name), "wb") as fh:
        fh.write(file.file.read())
    return name


@router.post("/courses")
def create_course(body: CourseIn, session: Session = Depends(get_db),
                  u: db.User = Depends(current_user)):
    if u.role != "mentor":
        raise HTTPException(403, "Please select a user role.")
    if not body.title.strip():
        raise HTTPException(400, "Title is required.")
    c = db.Course(mentor_id=u.id, title=body.title.strip(),
                  description=body.description, category=body.category,
                  language=body.language, price=max(0.0, body.price),
                  type="paid" if body.price > 0 else "free",
                  duration_hours=body.duration_hours, status="pending")
    session.add(c)
    session.commit()
    return {"message": "Course saved. Status: Pending until admin approval.",
            "course": _course_dict(c, u.name)}


@router.put("/courses/{cid}")
def edit_course(cid: int, body: CourseIn, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    c.title, c.description, c.category = body.title.strip(), body.description, body.category
    c.language, c.duration_hours = body.language, body.duration_hours
    c.price = max(0.0, body.price)
    c.type = "paid" if c.price > 0 else "free"
    session.commit()
    return {"message": "Course info updated successfully."}


@router.delete("/courses/{cid}")
def delete_course(cid: int, session: Session = Depends(get_db),
                  u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    session.delete(c)
    session.commit()
    return {"message": "Course deleted successfully."}


class LessonIn(BaseModel):
    title: str
    description: str = ""


@router.post("/courses/{cid}/lessons")
async def add_lesson(cid: int, title: str = "", description: str = "",
                     file: UploadFile = File(default=None),
                     session: Session = Depends(get_db),
                     u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c or c.mentor_id != u.id:
        raise HTTPException(404, "Course not found.")
    if not title.strip():
        raise HTTPException(400, "Title is required.")
    pos = len(c.lessons) + 1
    l = db.Lesson(course_id=cid, title=title.strip(), description=description,
                  position=pos, file=_save_upload(file) if file else None)
    session.add(l)
    session.commit()
    return {"message": "Content uploaded successfully.", "lesson_id": l.id}


@router.delete("/lessons/{lid}")
def delete_lesson(lid: int, session: Session = Depends(get_db),
                  u: db.User = Depends(current_user)):
    l = session.get(db.Lesson, lid)
    c = session.get(db.Course, l.course_id) if l else None
    if not l or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Lesson not found.")
    session.delete(l)
    session.commit()
    return {"message": "Lesson removed."}
