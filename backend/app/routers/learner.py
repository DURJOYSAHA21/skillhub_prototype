"""Learner workspace: progress stats, grades, certificates, notes, goals."""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, current_user

router = APIRouter(tags=["learner"])


def _learner(u: db.User = Depends(current_user)):
    if u.role != "learner":
        raise HTTPException(403, "Learner only.")
    return u


@router.get("/learner/overview")
def overview(session: Session = Depends(get_db), u: db.User = Depends(_learner)):
    ens = session.query(db.Enrollment).filter_by(learner_id=u.id).all()
    done = [e for e in ens if e.completed]
    hours = 0.0
    for e in ens:
        c = session.get(db.Course, e.course_id)
        if c:
            hours += c.duration_hours * (e.progress / 100.0)
    subs = session.query(db.Submission).filter_by(learner_id=u.id).all()
    grades = [s.score for s in subs]
    assigns = (session.query(db.AssignSubmit).filter_by(learner_id=u.id).all())
    graded = [a for a in assigns if a.grade is not None]
    return {
        "courses": len(ens),
        "completed": len(done),
        "in_progress": len([e for e in ens if not e.completed and e.progress > 0]),
        "hours_learned": round(hours, 1),
        "certificates": len(done),
        "wishlist": session.query(db.Wishlist).filter_by(user_id=u.id).count(),
        "avg_quiz_score": round(sum(grades) / len(grades), 1) if grades else 0,
        "quizzes_taken": len(subs),
        "assignments_submitted": len([a for a in assigns if not a.draft]),
        "assignments_graded": len(graded),
        "unread": session.query(db.Notification).filter_by(user_id=u.id,
                                                           read=False).count(),
    }


@router.get("/my/results")
def results(session: Session = Depends(get_db), u: db.User = Depends(_learner)):
    rows = []
    for s in session.query(db.Submission).filter_by(learner_id=u.id) \
            .order_by(db.Submission.submitted.desc()).all():
        qz = session.get(db.Quiz, s.quiz_id)
        c = session.get(db.Course, qz.course_id) if qz else None
        rows.append({"kind": "quiz", "course": c.title if c else "",
                     "course_id": c.id if c else 0, "item": qz.title if qz else "",
                     "score": s.score, "passed": bool(s.passed),
                     "detail": "%s%% - %d attempt(s)" % (s.score, s.attempts),
                     "date": s.submitted.strftime("%Y-%m-%d")})
    for a in session.query(db.AssignSubmit).filter_by(learner_id=u.id) \
            .order_by(db.AssignSubmit.submitted.desc()).all():
        asm = session.get(db.Assignment, a.assignment_id)
        c = session.get(db.Course, asm.course_id) if asm else None
        rows.append({"kind": "assignment", "course": c.title if c else "",
                     "course_id": c.id if c else 0, "item": asm.title if asm else "",
                     "score": a.grade, "passed": a.grade is not None,
                     "detail": (("graded %s" % a.grade) if a.grade is not None
                                else ("draft" if a.draft else "submitted, waiting for grade")),
                     "feedback": a.feedback or "",
                     "date": a.submitted.strftime("%Y-%m-%d")})
    return {"results": rows}


@router.get("/my/certificates")
def certificates(session: Session = Depends(get_db), u: db.User = Depends(_learner)):
    out = []
    for e in session.query(db.Enrollment).filter_by(learner_id=u.id,
                                                   completed=True).all():
        c = session.get(db.Course, e.course_id)
        if c:
            out.append({"course_id": c.id, "title": c.title,
                        "hours": c.duration_hours, "mentor":
                        (session.get(db.User, c.mentor_id) or db.User(name="")).name,
                        "issued": (e.enrolled or datetime.utcnow()).strftime("%Y-%m-%d")})
    return {"certificates": out}


class NoteIn(BaseModel):
    text: str


@router.put("/lessons/{lid}/note")
def save_note(lid: int, body: NoteIn, session: Session = Depends(get_db),
              u: db.User = Depends(current_user)):
    l = session.get(db.Lesson, lid)
    if not l:
        raise HTTPException(404, "Lesson not found.")
    if not session.query(db.Enrollment).filter_by(learner_id=u.id,
                                                 course_id=l.course_id).first():
        raise HTTPException(403, "Enroll in this course first.")
    n = session.query(db.LessonNote).filter_by(lesson_id=lid, user_id=u.id).first()
    if not n:
        n = db.LessonNote(lesson_id=lid, user_id=u.id)
        session.add(n)
    n.text = body.text.strip()
    n.updated = datetime.utcnow()
    session.commit()
    return {"message": "Note saved."}


@router.get("/my/notes")
def all_notes(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    out = []
    for n in session.query(db.LessonNote).filter_by(user_id=u.id) \
            .order_by(db.LessonNote.updated.desc()).all():
        l = session.get(db.Lesson, n.lesson_id)
        c = session.get(db.Course, l.course_id) if l else None
        out.append({"lesson_id": n.lesson_id, "lesson": l.title if l else "",
                    "course": c.title if c else "", "course_id": c.id if c else 0,
                    "text": n.text, "date": n.updated.strftime("%Y-%m-%d")})
    return {"notes": out}


@router.delete("/enrollments/{cid}")
def unenroll(cid: int, session: Session = Depends(get_db), u: db.User = Depends(_learner)):
    e = session.query(db.Enrollment).filter_by(learner_id=u.id, course_id=cid).first()
    if not e:
        raise HTTPException(404, "You are not enrolled in this course.")
    c = session.get(db.Course, cid)
    paid = session.query(db.Txn).filter_by(learner_id=u.id, course_id=cid,
                                           status="success").first()
    session.delete(e)
    session.commit()
    if c:
        db.notify(session, c.mentor_id,
                  "'%s' left your course '%s'" % (u.name, c.title),
                  "/dashboard", "course")
    return {"message": "Removed from My Learning.",
            "refund_needed": bool(paid),
            "hint": ("Your payment stays recorded; ask the instructor or admin for a "
                     "refund if you want one." if paid else "")}


class GoalsIn(BaseModel):
    goals: list


@router.put("/my/goals")
def save_goals(body: GoalsIn, session: Session = Depends(get_db),
               u: db.User = Depends(_learner)):
    names = [str(g).strip() for g in body.goals if str(g).strip()][:12]
    u.goals = json.dumps(names)
    session.commit()
    return {"message": "Learning goals saved.", "goals": names}


@router.get("/my/goals")
def get_goals(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    return {"goals": json.loads(u.goals or "[]")}