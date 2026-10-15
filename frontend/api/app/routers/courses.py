"""Course catalog + lessons (SRS items 7, 11, 12, 14, 15)."""
import json, os, uuid
from datetime import datetime
from fastapi import (APIRouter, Depends, File, Form, HTTPException, Header,
                     Request, UploadFile)
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


def _course_dict(c: db.Course, mentor_name: str = "", owner: bool = False,
                 students: int = 0, mentor_id_of=None):
    return {"id": c.id, "title": c.title, "description": c.description,
            "category": c.category, "language": c.language, "price": c.price,
            "type": c.type, "level": c.level, "tags": c.tags or "",
            "thumbnail": c.thumbnail or "", "duration_hours": c.duration_hours,
            "status": c.status, "students": students,
            "featured": bool(c.featured),
            "note": (c.review_note or "") if owner else "",
            "rating": c.rating, "reviews": c.reviews, "mentor": mentor_name,
            "mentor_id": c.mentor_id,
            "lessons": [{"id": l.id, "title": l.title, "position": l.position,
                         "file": bool(l.file),
                         "notes": bool(l.content or l.video_url)}
                        for l in c.lessons],
            "quizzes": [{"id": q.id, "title": q.title, "published": q.published,
                         "questions": len(q.questions)}
                        for q in c.quizzes if q.published or owner],
            "assignments": [{"id": a.id, "title": a.title,
                             "instructions": a.instructions} for a in c.assignments]}


@router.get("/courses")
def list_courses(q: str = "", category: str = "", language: str = "",
                 max_price: float = 0, min_rating: float = 0, min_price: float = -1,
                 level: str = "", sort: str = "rating", mentor_id: int = 0,
                 mine: str = "", authorization: str = Header(default=""),
                 session: Session = Depends(get_db)):
    query = session.query(db.Course)
    me = _optional_user(authorization, session)
    if mine == "mentor" and me and me.role == "mentor":
        query = query.filter(db.Course.mentor_id == me.id)   # incl. pending
    elif mine == "enrolled" and me:
        ids = [e.course_id for e in session.query(db.Enrollment)
               .filter_by(learner_id=me.id).all()]
        query = query.filter(db.Course.id.in_(ids or [-1]))
    else:
        query = query.filter(db.Course.status == "published")
    if mentor_id:
        query = query.filter(db.Course.mentor_id == mentor_id)
    if level:
        query = query.filter(db.Course.level == level)
    if min_price >= 0 and not mine:
        query = query.filter(db.Course.price >= min_price)
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
    if sort == "newest":
        query = query.order_by(db.Course.id.desc())
    elif sort == "price_low":
        query = query.order_by(db.Course.price.asc())
    elif sort == "price_high":
        query = query.order_by(db.Course.price.desc())
    elif sort == "popular":
        query = query.order_by(db.Course.reviews.desc())
    else:
        query = query.order_by(db.Course.rating.desc())
    mine_ids = {e.course_id for e in session.query(db.Enrollment).filter_by(
        learner_id=me.id).all()} if me else set()
    wish_ids = {w.course_id for w in session.query(db.Wishlist).filter_by(
        user_id=me.id).all()} if me else set()
    out = []
    for c in query.all():
        m = session.get(db.User, c.mentor_id)
        d = _course_dict(c, m.name if m else "",
                         owner=bool(me and me.id == c.mentor_id),
                         students=session.query(db.Enrollment)
                         .filter_by(course_id=c.id).count())
        d["enrolled"] = c.id in mine_ids
        d["saved"] = c.id in wish_ids
        out.append(d)
    return {"count": len(out), "courses": out}


class CourseIn(BaseModel):
    title: str
    description: str = ""
    category: str = "Tech"
    language: str = "en"
    price: float = 0
    duration_hours: float = 4
    level: str = "Beginner"
    tags: str = ""


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
                  level=body.level or "Beginner", tags=body.tags.strip(),
                  duration_hours=body.duration_hours, status="pending",
                  rating=0.0, reviews=0)
    session.add(c)
    session.flush()
    db.notify_role(session, "admin",
                   "New course awaiting review: '%s' by %s (\u09f3%s, %s)"
                   % (c.title, u.name, c.price, c.category),
                   "/dashboard", "course")
    session.commit()
    return {"message": "Course submitted for admin approval. You will be notified "
                       "as soon as it is reviewed.",
            "id": c.id, "status": c.status,
            "course": _course_dict(c, u.name, owner=True)}


@router.put("/courses/{cid}")
def edit_course(cid: int, body: CourseIn, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    c.title, c.description, c.category = body.title.strip(), body.description, body.category
    c.language, c.duration_hours = body.language, body.duration_hours
    c.price = max(0.0, body.price)
    c.level = body.level or c.level
    c.tags = body.tags.strip()
    c.type = "paid" if c.price > 0 else "free"
    c.updated = datetime.utcnow()
    if c.status == "rejected":
        c.status = "pending"
        db.notify_role(session, "admin",
                       "Rejected course resubmitted for review: '%s'" % c.title,
                       "/dashboard", "course")
    session.commit()
    return {"message": "Course info updated successfully.", "status": c.status}


@router.put("/courses/{cid}/resubmit")
def resubmit(cid: int, session: Session = Depends(get_db),
             u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c or c.mentor_id != u.id:
        raise HTTPException(404, "Course not found.")
    c.status = "pending"
    c.updated = datetime.utcnow()
    session.commit()
    db.notify_role(session, "admin",
                   "'%s' is waiting for your review again" % c.title,
                   "/dashboard", "course")
    return {"message": "Sent back to the review queue."}


@router.post("/courses/{cid}/thumbnail")
async def course_thumbnail(cid: int, request: Request,
                           session: Session = Depends(get_db),
                           u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    form = await request.form()
    up = form.get("file") if hasattr(form, "get") else None
    if up is None or not hasattr(up, "filename") or not up.filename:
        raise HTTPException(400, "Choose an image file first.")
    c.thumbnail = _save_upload(up)
    session.commit()
    return {"message": "Cover image saved.", "thumbnail": c.thumbnail}


@router.delete("/courses/{cid}")
def delete_course(cid: int, session: Session = Depends(get_db),
                  u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    mid = c.mentor_id
    session.delete(c)
    session.commit()
    if u.role == "admin":
        db.notify(session, mid, "Your course '%s' was removed by the admin team."
                  % c.title, "/dashboard", "course")
    return {"message": "Course deleted successfully."}


class LessonIn(BaseModel):
    title: str
    description: str = ""


@router.post("/courses/{cid}/lessons")
async def add_lesson(cid: int, request: Request,
                     session: Session = Depends(get_db),
                     u: db.User = Depends(current_user)):
    fields = await request.form()
    if not fields:
        fields = request.query_params

    def get(k, d=""):
        try:
            v = fields.get(k, d)
        except AttributeError:
            v = d
        return (v if isinstance(v, str) else d) or d

    c = session.get(db.Course, cid)
    if not c or c.mentor_id != u.id:
        raise HTTPException(404, "Course not found.")
    title = get("title").strip()
    if not title:
        raise HTTPException(400, "Title is required.")
    description, content = get("description"), get("content")
    video_url = get("video_url").strip()
    file = fields.get("file") if hasattr(fields, "get") else None
    if file is not None and not hasattr(file, "filename"):
        file = None
    pos = len(c.lessons) + 1
    l = db.Lesson(course_id=cid, title=title.strip(), description=description,
                  position=pos, file=_save_upload(file) if file else None,
                  content=content, video_url=video_url or None)
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


class QuestionIn(BaseModel):
    text: str
    options: list
    correct: int
    marks: float = 5.0


class QuizCreateIn(BaseModel):
    title: str
    description: str = ""
    time_limit_min: int = 15
    passing_score: float = 60.0
    max_attempts: int = 3
    published: bool = True
    questions: list = []


class AssignmentIn(BaseModel):
    title: str
    instructions: str = ""
    due: str = ""
    marks: float = 100.0


def _own_course(session, cid, u):
    c = session.get(db.Course, cid)
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    return c


@router.post("/courses/{cid}/quizzes")
def create_quiz(cid: int, body: QuizCreateIn, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    c = _own_course(session, cid, u)
    if not body.title.strip():
        raise HTTPException(400, "Title is required.")
    if len(body.questions) < 1:
        raise HTTPException(400, "Add at least one question.")
    qz = db.Quiz(course_id=c.id, title=body.title.strip(),
                 description=body.description,
                 time_limit_min=max(1, body.time_limit_min),
                 passing_score=max(0.0, min(100.0, body.passing_score)),
                 max_attempts=max(1, body.max_attempts), published=body.published)
    session.add(qz)
    session.flush()
    for i, q in enumerate(body.questions):
        opts = [str(o).strip() for o in list(q.get("options", []))[:6]] \
            if isinstance(q, dict) else []
        text = (q.get("text") or "").strip() if isinstance(q, dict) else ""
        corr = int(q.get("correct", -1)) if isinstance(q, dict) else -1
        if len(opts) != 4 or any(not o for o in opts) or not text:
            session.rollback()
            raise HTTPException(400, "Question %d: need text and 4 non-empty "
                                     "options." % (i + 1))
        if not (0 <= corr <= 3):
            session.rollback()
            raise HTTPException(400, "Question %d: pick the correct answer."
                                % (i + 1))
        session.add(db.Question(quiz_id=qz.id, text=text,
                                options=json.dumps(opts), correct=corr,
                                marks=max(1.0, float(q.get("marks", 5)))))
    session.commit()
    return {"message": "Quiz saved.", "quiz_id": qz.id,
            "questions": len(qz.questions)}


@router.put("/quizzes/{qid}/publish")
def publish_quiz(qid: int, published: bool = True,
                 session: Session = Depends(get_db),
                 u: db.User = Depends(current_user)):
    qz = session.get(db.Quiz, qid)
    if not qz:
        raise HTTPException(404, "Quiz not found.")
    _own_course(session, qz.course_id, u)
    qz.published = published
    session.commit()
    return {"message": "Quiz published." if published else "Quiz set to draft."}


@router.delete("/quizzes/{qid}")
def delete_quiz(qid: int, session: Session = Depends(get_db),
               u: db.User = Depends(current_user)):
    qz = session.get(db.Quiz, qid)
    if not qz:
        raise HTTPException(404, "Quiz not found.")
    _own_course(session, qz.course_id, u)
    session.delete(qz)
    session.commit()
    return {"message": "Quiz deleted."}


@router.post("/courses/{cid}/assignments")
def create_assignment(cid: int, body: AssignmentIn,
                      session: Session = Depends(get_db),
                      u: db.User = Depends(current_user)):
    c = _own_course(session, cid, u)
    if not body.title.strip():
        raise HTTPException(400, "Title is required.")
    due = None
    if body.due:
        try:
            due = datetime.fromisoformat(body.due)
        except ValueError:
            raise HTTPException(400, "Due date must be YYYY-MM-DD.")
    a = db.Assignment(course_id=c.id, title=body.title.strip(),
                      instructions=body.instructions, due=due,
                      marks=max(1.0, body.marks))
    session.add(a)
    session.commit()
    return {"message": "Assignment saved.", "assignment_id": a.id}
