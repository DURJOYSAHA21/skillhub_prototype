"""Learning, quizzes, assignments, progress, certificates (SRS 9, 10, 15)."""
import json, os, uuid
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, current_user
from ..reports import certificate_pdf

router = APIRouter(tags=["assess"])


def _enr(session, u, cid):
    e = session.query(db.Enrollment).filter_by(learner_id=u.id, course_id=cid).first()
    if not e:
        raise HTTPException(403, "Please enroll in this course first.")
    return e


def _recalc(e, c):
    lessons = list(c.lessons)
    quizzes = [q for q in c.quizzes if q.published]
    done_l = set(json.loads(e.done_lessons or "[]"))
    passed_q = set(json.loads(e.passed_quizzes or "[]"))
    if not quizzes:
        prog = 100.0 * len(done_l) / max(1, len(lessons))
    else:
        prog = 70.0 * len(done_l) / max(1, len(lessons)) + \
               30.0 * len(passed_q) / len(quizzes)
    e.progress = round(min(100.0, prog), 1)
    e.completed = bool(lessons) and done_l >= {l.id for l in lessons} and \
        passed_q >= {q.id for q in quizzes}


def _save_upload(file: UploadFile) -> str:
    os.makedirs(db.UPLOAD_DIR, exist_ok=True)
    name = uuid.uuid4().hex[:10] + "-" + os.path.basename(file.filename or "file")
    with open(os.path.join(db.UPLOAD_DIR, name), "wb") as fh:
        fh.write(file.file.read())
    return name


@router.get("/my/courses")
def my_courses(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    rows = []
    for e in session.query(db.Enrollment).filter_by(learner_id=u.id).all():
        c = session.get(db.Course, e.course_id)
        if c:
            rows.append({"enrollment_id": e.id, "course_id": c.id, "title": c.title,
                         "language": c.language, "progress": e.progress,
                         "completed": e.completed, "last_lesson": e.last_lesson})
    return {"count": len(rows), "courses": rows}


@router.get("/courses/{cid}/learn")
def learn(cid: int, session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c:
        raise HTTPException(404, "Course not found.")
    e = _enr(session, u, cid)
    done = set(json.loads(e.done_lessons or "[]"))
    return {"course_id": cid, "title": c.title, "progress": e.progress,
            "completed": e.completed, "last_lesson": e.last_lesson,
            "lessons": [{"id": l.id, "title": l.title, "position": l.position,
                         "description": l.description, "file": l.file,
                         "done": l.id in done} for l in c.lessons],
            "quizzes": [{"id": q.id, "title": q.title, "time_limit_min": q.time_limit_min,
                         "passing_score": q.passing_score, "max_attempts": q.max_attempts}
                        for q in c.quizzes if q.published],
            "assignments": [{"id": a.id, "title": a.title, "instructions": a.instructions,
                             "due": a.due.strftime("%Y-%m-%d") if a.due else ""}
                            for a in c.assignments]}

@router.post("/lessons/{lid}/complete")
def complete_lesson(lid: int, session: Session = Depends(get_db),
                    u: db.User = Depends(current_user)):
    l = session.get(db.Lesson, lid)
    if not l:
        raise HTTPException(404, "Lesson not found.")
    c = session.get(db.Course, l.course_id)
    e = _enr(session, u, c.id)
    done = set(json.loads(e.done_lessons or "[]"))
    done.add(lid)
    e.done_lessons = json.dumps(sorted(done))
    e.last_lesson = lid
    _recalc(e, c)
    session.commit()
    return {"message": "Progress saved.", "progress": e.progress,
            "completed": e.completed}


@router.get("/quizzes/{qid}")
def quiz(qid: int, session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    qz = session.get(db.Quiz, qid)
    if not qz or not qz.published:
        raise HTTPException(404, "Quiz not found.")
    _enr(session, u, qz.course_id)
    return {"id": qz.id, "title": qz.title, "time_limit_min": qz.time_limit_min,
            "passing_score": qz.passing_score, "max_attempts": qz.max_attempts,
            "questions": [{"id": x.id, "text": x.text,
                           "options": json.loads(x.options)} for x in qz.questions]}


class QuizIn(BaseModel):
    answers: dict  # {question_id(str): chosen index}


@router.post("/quizzes/{qid}/submit")
def submit_quiz(qid: int, body: QuizIn, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    qz = session.get(db.Quiz, qid)
    if not qz:
        raise HTTPException(404, "Quiz not found.")
    e = _enr(session, u, qz.course_id)
    prev = session.query(db.Submission).filter_by(quiz_id=qid, learner_id=u.id).first()
    if prev and prev.attempts >= qz.max_attempts:
        raise HTTPException(400, "Maximum attempts reached for this quiz.")
    total = sum(x.marks for x in qz.questions) or 1.0
    got = 0.0
    detail = []
    for x in qz.questions:
        chosen = body.answers.get(str(x.id))
        ok = chosen is not None and int(chosen) == x.correct
        if ok:
            got += x.marks
        detail.append({"question_id": x.id, "correct": x.correct, "got": ok})
    score = round(100.0 * got / total, 1)
    passed = score >= qz.passing_score
    sub = prev or db.Submission(quiz_id=qid, learner_id=u.id, attempts=0)
    sub.answers = json.dumps(detail)
    sub.score = score
    sub.passed = passed
    sub.attempts = (prev.attempts + 1) if prev else 1
    sub.submitted = datetime.utcnow()
    session.add(sub)
    if passed:
        pset = set(json.loads(e.passed_quizzes or "[]"))
        pset.add(qid)
        e.passed_quizzes = json.dumps(sorted(pset))
    c = session.get(db.Course, qz.course_id)
    _recalc(e, c)
    session.commit()
    return {"score_percent": score, "passed": passed, "attempts_used": sub.attempts,
            "results": detail, "progress": e.progress, "completed": e.completed}


@router.post("/assignments/{aid}/submit")
async def submit_assignment(aid: int, comment: str = Form(""),
                            draft: bool = Form(False),
                            file: UploadFile = File(default=None),
                            session: Session = Depends(get_db),
                            u: db.User = Depends(current_user)):
    a = session.get(db.Assignment, aid)
    if not a:
        raise HTTPException(404, "Assignment not found.")
    _enr(session, u, a.course_id)
    s = session.query(db.AssignSubmit).filter_by(assignment_id=aid, learner_id=u.id).first() \
        or db.AssignSubmit(assignment_id=aid, learner_id=u.id)
    s.comment = comment
    s.draft = draft
    s.file = _save_upload(file) if file else s.file
    s.submitted = datetime.utcnow()
    session.add(s)
    session.commit()
    return {"message": "Draft saved." if draft else "Assignment submitted."}


@router.get("/assignments/{aid}/submissions")
def assignment_subs(aid: int, session: Session = Depends(get_db),
                    u: db.User = Depends(current_user)):
    a = session.get(db.Assignment, aid)
    c = session.get(db.Course, a.course_id) if a else None
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(403, "Mentor only.")
    rows = [{"learner": (session.get(db.User, s.learner_id) or db.User(name="")).name,
             "file": s.file, "comment": s.comment, "draft": s.draft,
             "submitted": s.submitted.strftime("%Y-%m-%d %H:%M")}
            for s in session.query(db.AssignSubmit).filter_by(assignment_id=aid).all()]
    return {"assignment": a.title, "submissions": rows}


@router.get("/courses/{cid}/certificate")
def certificate(cid: int, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    e = _enr(session, u, cid)
    if not e.completed:
        raise HTTPException(400, "Course not completed yet. Progress: "
                                 f"{e.progress}%.")
    pdf = certificate_pdf(u.name, c.title, c.duration_hours, e.enrolled or datetime.utcnow())
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"inline; filename=certificate-{cid}.pdf"})
