"""Mentor workspace: course studio, lessons, roster, grading, replies, profile."""
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, current_user

router = APIRouter(tags=["mentor"])


def _mentor(u: db.User = Depends(current_user)):
    if u.role != "mentor":
        raise HTTPException(403, "Mentor only.")
    return u


def _own(cid: int, session: Session, u: db.User) -> db.Course:
    c = session.get(db.Course, cid)
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    return c


def _my_courses(session, u):
    return session.query(db.Course).filter(db.Course.mentor_id == u.id).all()


@router.get("/mentor/overview")
def overview(session: Session = Depends(get_db), u: db.User = Depends(_mentor)):
    courses = _my_courses(session, u)
    ids = [c.id for c in courses]
    students = (session.query(db.Enrollment).filter(db.Enrollment.course_id.in_(ids or [-1]))
                .count())
    txns = session.query(db.Txn).filter(db.Txn.course_id.in_(ids or [-1]),
                                         db.Txn.status == "success").all()
    revenue = round(sum(t.amount for t in txns), 2)
    published = [c for c in courses if c.status == "published"]
    ratings = [c.rating for c in published if c.reviews]
    ungraded = (session.query(db.AssignSubmit).join(db.Assignment)
                .filter(db.Assignment.course_id.in_(ids or [-1]),
                        db.AssignSubmit.draft.is_(False),
                        db.AssignSubmit.grade.is_(None)).count())
    new_reviews = (session.query(db.Review).join(db.Course)
                   .filter(db.Course.mentor_id == u.id).count())
    seen = (session.query(db.Review).filter(db.Review.reply != "",
                                            db.Review.course_id.in_(ids or [-1])).count())
    lessons = sum(len(c.lessons) for c in courses)
    quiz_attempts = (session.query(db.Submission).join(db.Quiz)
                     .filter(db.Quiz.course_id.in_(ids or [-1])).count())
    return {
        "courses": len(courses),
        "published": len(published),
        "pending": len([c for c in courses if c.status == "pending"]),
        "rejected": len([c for c in courses if c.status == "rejected"]),
        "lessons": lessons,
        "students": students,
        "revenue": revenue,
        "quiz_attempts": quiz_attempts,
        "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
        "reviews_total": new_reviews,
        "reviews_unanswered": max(0, new_reviews - seen),
        "ungraded": ungraded,
    }


@router.get("/courses/{cid}/students")
def roster(cid: int, session: Session = Depends(get_db), u: db.User = Depends(_mentor)):
    c = _own(cid, session, u)
    rows = []
    for e in session.query(db.Enrollment).filter_by(course_id=cid) \
            .order_by(db.Enrollment.progress.desc()).all():
        x = session.get(db.User, e.learner_id)
        if not x:
            continue
        grades = [s.grade for s in
                  session.query(db.AssignSubmit).join(db.Assignment)
                  .filter(db.Assignment.course_id == cid,
                          db.AssignSubmit.learner_id == x.id,
                          db.AssignSubmit.grade != None)  # noqa: E711
                  ]
        rows.append({"user_id": x.id, "name": x.name, "email": x.email,
                     "progress": e.progress, "completed": bool(e.completed),
                     "enrolled": e.enrolled.strftime("%Y-%m-%d"),
                     "graded_avg": round(sum(grades) / len(grades), 1) if grades else None})
    return {"course": c.title, "status": c.status, "count": len(rows),
            "students": rows}


class LessonEdit(BaseModel):
    title: str = ""
    description: str = ""
    content: str = ""
    video_url: str = ""


@router.put("/lessons/{lid}")
async def edit_lesson(lid: int, request: Request,
                     session: Session = Depends(get_db), u: db.User = Depends(_mentor)):
    l = session.get(db.Lesson, lid)
    if not l:
        raise HTTPException(404, "Lesson not found.")
    _own(l.course_id, session, u)
    fields = await request.form()
    if not fields:
        fields = request.query_params

    def get(k, d=""):
        try:
            v = fields.get(k, d)
        except AttributeError:
            v = d
        return (v if isinstance(v, str) else d) or d

    if get("title").strip():
        l.title = get("title").strip()
    if "description" in fields:
        l.description = get("description")
    if "content" in fields:
        l.content = get("content")
    if "video_url" in fields:
        l.video_url = get("video_url").strip() or None
    up = fields.get("file") if hasattr(fields, "get") else None
    if up is not None and hasattr(up, "filename") and up.filename:
        from .courses import _save_upload
        l.file = _save_upload(up)
    session.commit()
    return {"message": "Lesson updated.", "lesson_id": l.id}


@router.put("/lessons/{lid}/move")
def move_lesson(lid: int, direction: str = "up", session: Session = Depends(get_db),
                u: db.User = Depends(_mentor)):
    l = session.get(db.Lesson, lid)
    if not l:
        raise HTTPException(404, "Lesson not found.")
    c = _own(l.course_id, session, u)
    les = sorted(c.lessons, key=lambda x: x.position)
    i = next((k for k, x in enumerate(les) if x.id == lid), None)
    if i is None:
        raise HTTPException(404, "Lesson not found.")
    j = i - 1 if direction == "up" else i + 1
    if j < 0 or j >= len(les):
        return {"message": "Already at that end."}
    les[i].position, les[j].position = les[j].position, les[i].position
    session.commit()
    return {"message": "Order saved."}


@router.get("/quizzes/{qid}/results")
def quiz_results(qid: int, session: Session = Depends(get_db), u: db.User = Depends(_mentor)):
    qz = session.get(db.Quiz, qid)
    if not qz:
        raise HTTPException(404, "Quiz not found.")
    _own(qz.course_id, session, u)
    rows = []
    for s in session.query(db.Submission).filter_by(quiz_id=qid) \
            .order_by(db.Submission.score.desc()).all():
        x = session.get(db.User, s.learner_id)
        rows.append({"learner": x.name if x else "", "user_id": s.learner_id,
                     "score": s.score, "passed": bool(s.passed),
                     "attempts": s.attempts,
                     "date": s.submitted.strftime("%Y-%m-%d %H:%M")})
    sc = [r["score"] for r in rows]
    return {"quiz": qz.title, "published": bool(qz.published),
            "takers": len(rows),
            "avg_score": round(sum(sc) / len(sc), 1) if sc else 0,
            "pass_rate": round(100.0 * len([r for r in rows if r["passed"]]) /
                               len(rows), 1) if rows else 0,
            "results": rows}


class GradeIn(BaseModel):
    grade: float
    feedback: str = ""


@router.put("/assignments/submissions/{sid}/grade")
def grade_submission(sid: int, body: GradeIn, session: Session = Depends(get_db),
                     u: db.User = Depends(_mentor)):
    s = session.get(db.AssignSubmit, sid)
    if not s:
        raise HTTPException(404, "Submission not found.")
    a = session.get(db.Assignment, s.assignment_id)
    c = _own(a.course_id, session, u)
    if body.grade < 0 or body.grade > a.marks:
        raise HTTPException(400, "Grade must be between 0 and %s marks." % a.marks)
    s.grade = round(body.grade, 1)
    s.feedback = body.feedback.strip()
    session.commit()
    db.notify(session, s.learner_id,
              "Your '%s' submission was graded: %s/%s" % (a.title, s.grade, a.marks),
              "/learn/%d" % c.id, "grade")
    return {"message": "Grade saved and the learner was notified."}


class ReplyIn(BaseModel):
    reply: str


@router.post("/reviews/{rid}/reply")
def reply_review(rid: int, body: ReplyIn, session: Session = Depends(get_db),
                 u: db.User = Depends(_mentor)):
    r = session.get(db.Review, rid)
    if not r:
        raise HTTPException(404, "Review not found.")
    c = _own(r.course_id, session, u)
    if not body.reply.strip():
        raise HTTPException(400, "Write a reply first.")
    r.reply = body.reply.strip()
    session.commit()
    db.notify(session, r.user_id,
              "The instructor replied to your review of '%s'" % c.title,
              "/course/%d" % c.id, "course")
    return {"message": "Reply posted."}


class SkillIn(BaseModel):
    name: str
    proficiency: int = 3
    years: float = 2


class LangIn(BaseModel):
    code: str
    fluency: str = "fluent"


class MentorProfileIn(BaseModel):
    headline: str = ""
    about: str = ""
    country: str = "Bangladesh"
    skills: list = []
    langs: list = []


@router.put("/mentor/profile")
def save_profile(body: MentorProfileIn, session: Session = Depends(get_db),
                 u: db.User = Depends(_mentor)):
    p = session.get(db.MentorProfile, u.id) or db.MentorProfile(user_id=u.id)
    p.headline = body.headline.strip()
    p.about = body.about.strip()
    p.country = body.country.strip() or "Bangladesh"
    session.add(p)
    session.query(db.MentorSkill).filter_by(user_id=u.id).delete()
    for s in body.skills:
        name = (s.get("name") if isinstance(s, dict) else "").strip()
        if not name:
            continue
        sk = session.query(db.Skill).filter(db.Skill.name.ilike(name)).first()
        if not sk:
            sk = db.Skill(name=name, category="Other")
            session.add(sk)
            session.flush()
        prof = int(s.get("proficiency", 3)) if isinstance(s, dict) else 3
        yrs = float(s.get("years", 2)) if isinstance(s, dict) else 2
        session.add(db.MentorSkill(user_id=u.id, skill_id=sk.id,
                                   proficiency=max(1, min(5, prof)), years=yrs))
    session.query(db.MentorLanguage).filter_by(user_id=u.id).delete()
    for lg in body.langs:
        code = (lg.get("code") if isinstance(lg, dict) else "").strip()
        if not code:
            continue
        flu = (lg.get("fluency") if isinstance(lg, dict) else "fluent") or "fluent"
        session.add(db.MentorLanguage(user_id=u.id, code=code, fluency=flu))
    session.commit()
    return {"message": "Instructor profile updated.", "verified": bool(p.verified)}

@router.get("/courses/{cid}/lessons")
def lesson_list(cid: int, session: Session = Depends(get_db),
                u: db.User = Depends(_mentor)):
    """Full lesson text so the instructor can edit it (list payload is trimmed)."""
    c = _own(cid, session, u)
    out = []
    for l in sorted(c.lessons, key=lambda x: x.position):
        done = 0
        for e in session.query(db.Enrollment).filter_by(course_id=cid).all():
            ids = json.loads(e.done_lessons or "[]")
            if l.id in ids:
                done += 1
        out.append({"id": l.id, "title": l.title, "position": l.position,
                    "description": l.description or "", "content": l.content or "",
                    "video_url": l.video_url or "", "file": l.file or "",
                    "done_by": done})
    return {"course_id": cid, "course": c.title, "status": c.status,
            "price": c.price, "lessons": out}