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
    for e in session.query(db.Enrollment).filter_by(learner_id=u.id) \
            .order_by(db.Enrollment.id.desc()).all():
        c = session.get(db.Course, e.course_id)
        if c:
            m = session.get(db.User, c.mentor_id)
            nxt = next((l.id for l in c.lessons if l.id not in
                        set(json.loads(e.done_lessons or "[]"))), 0)
            rows.append({"enrollment_id": e.id, "course_id": c.id, "title": c.title,
                         "language": c.language, "progress": e.progress,
                         "lessons": len(c.lessons), "hours": c.duration_hours,
                         "price": c.price, "category": c.category,
                         "mentor": m.name if m else "", "mentor_id": c.mentor_id,
                         "next_lesson": nxt, "resume": "/learn/%d" % c.id,
                         "completed": e.completed, "last_lesson": e.last_lesson,
                         "enrolled": e.enrolled.strftime("%Y-%m-%d")})
    return {"count": len(rows), "courses": rows}


@router.get("/courses/{cid}/learn")
def learn(cid: int, session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    c = session.get(db.Course, cid)
    if not c:
        raise HTTPException(404, "Course not found.")
    e = _enr(session, u, cid)
    done = set(json.loads(e.done_lessons or "[]"))
    notes = {n.lesson_id: n.text for n in session.query(db.LessonNote)
             .filter_by(user_id=u.id).all()
             if n.lesson_id in {l.id for l in c.lessons}}
    m = session.get(db.User, c.mentor_id)
    subs = {s.quiz_id: s for s in session.query(db.Submission)
            .filter_by(learner_id=u.id).all()}
    asubs = {x.assignment_id: x for x in session.query(db.AssignSubmit)
             .filter_by(learner_id=u.id).all()}
    return {"course_id": cid, "title": c.title, "progress": e.progress,
            "completed": e.completed, "last_lesson": e.last_lesson,
            "mentor": m.name if m else "", "mentor_id": c.mentor_id,
            "price": c.price, "level": c.level, "category": c.category,
            "lessons_total": len(c.lessons), "lessons_done": len(done),
            "hours": c.duration_hours,
            "lessons": [{"id": l.id, "title": l.title, "position": l.position,
                         "description": l.description, "file": l.file,
                         "content": l.content or "", "video_url": l.video_url or "",
                         "note": notes.get(l.id, ""), "done": l.id in done}
                        for l in c.lessons],
            "quizzes": [{"id": q.id, "title": q.title, "questions": len(q.questions),
                         "time_limit_min": q.time_limit_min,
                         "passing_score": q.passing_score,
                         "attempts_left": max(0, q.max_attempts -
                                              (subs[q.id].attempts if q.id in subs else 0)),
                         "best_score": subs[q.id].score if q.id in subs else None,
                         "passed": bool(subs[q.id].passed) if q.id in subs else False,
                         "max_attempts": q.max_attempts}
                        for q in c.quizzes if q.published],
            "assignments": [{"id": a.id, "title": a.title, "marks": a.marks,
                             "instructions": a.instructions,
                             "due": a.due.strftime("%Y-%m-%d") if a.due else "",
                             "submitted": bool(a.id in asubs and not asubs[a.id].draft),
                             "grade": asubs[a.id].grade if a.id in asubs else None,
                             "feedback": (asubs[a.id].feedback or "") if a.id in asubs else ""}
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
    was_done = bool(e.completed)
    _recalc(e, c)
    session.commit()
    if e.completed and not was_done:
        db.notify(session, u.id,
                  "Course complete: '%s'. Your certificate is ready!" % c.title,
                  "/learn/%d" % c.id)
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
    pset = set(json.loads(e.passed_quizzes or "[]"))
    first_pass = passed and qid not in pset
    if passed:
        pset.add(qid)
        e.passed_quizzes = json.dumps(sorted(pset))
    c = session.get(db.Course, qz.course_id)
    was_done = bool(e.completed)
    _recalc(e, c)
    session.commit()
    if first_pass:
        db.notify(session, u.id, "You passed '%s' with %s%%" % (qz.title, score),
                  "/learn/%d" % c.id)
    if e.completed and not was_done:
        db.notify(session, u.id,
                  "Course complete: '%s'. Your certificate is ready!" % c.title,
                  "/learn/%d" % c.id)
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
    if not draft:
        crs = session.get(db.Course, a.course_id)
        if crs:
            db.notify(session, crs.mentor_id,
                      "%s submitted '%s' for grading" % (u.name, a.title),
                      "/dashboard", "grade")
    return {"message": "Draft saved." if draft else
            "Assignment submitted. Your instructor will grade it."}


@router.get("/assignments/{aid}/submissions")
def assignment_subs(aid: int, session: Session = Depends(get_db),
                    u: db.User = Depends(current_user)):
    a = session.get(db.Assignment, aid)
    c = session.get(db.Course, a.course_id) if a else None
    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(403, "Mentor only.")
    rows = [{"id": s.id, "learner_id": s.learner_id,
              "learner": (session.get(db.User, s.learner_id) or db.User(name="")).name,
              "file": s.file, "comment": s.comment, "draft": s.draft,
              "grade": s.grade, "feedback": s.feedback or "",
              "marks": a.marks,
              "submitted": s.submitted.strftime("%Y-%m-%d %H:%M")}
             for s in session.query(db.AssignSubmit).filter_by(assignment_id=aid).all()]
    return {"assignment": a.title, "marks": a.marks,
            "ungraded": len([r for r in rows if not r["draft"] and r["grade"] is None]),
            "submissions": rows}


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
