import io, ast
BOOK = "\U0001F4DA"
def load(p): return io.open(p, encoding="utf-8-sig").read().replace("\r\n","\n")
def save(p, src):
    ast.parse(src); io.open(p,"w",encoding="utf-8",newline="\n").write(src)
def rep(src, old, new, tag):
    assert src.count(old)==1, "MARKER FAIL "+tag
    return src.replace(old,new)

P="app/routers/admin.py"; src=load(P)
out=[]
hit=0
for line in src.split("\n"):
    if "db.Category(name=name," in line:
        line = '    session.add(db.Category(name=name, icon=body.icon or "%s"))' % BOOK
        hit += 1
    out.append(line)
assert hit == 1, hit
src = "\n".join(out)
src = src.replace('''@router.post("/reviews/{rid}/hide")
def hide_note(rid: int, session: Session = Depends(get_db),
              a: db.User = Depends(_admin)):
    r = session.get(db.Review, rid)
    if not r:
        raise HTTPException(404, "Review not found.")
    return {"message": "Flagged for follow-up.", "review_id": rid}


''', "")
assert "hide_note" not in src
save(P, src); print("admin fixed")

P="app/routers/assess.py"; src=load(P)
src = rep(src, '''@router.get("/my/courses")
def my_courses(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    rows = []
    for e in session.query(db.Enrollment).filter_by(learner_id=u.id).all():
        c = session.get(db.Course, e.course_id)
        if c:
            rows.append({"enrollment_id": e.id, "course_id": c.id, "title": c.title,
                         "language": c.language, "progress": e.progress,
                         "completed": bool(e.completed), "last_lesson": e.last_lesson})
    return {"count": len(rows), "courses": rows}''',
'''@router.get("/my/courses")
def my_courses(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    rows = []
    for e in session.query(db.Enrollment).filter_by(learner_id=u.id) \\
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
                         "completed": bool(e.completed), "last_lesson": e.last_lesson,
                         "enrolled": e.enrolled.strftime("%Y-%m-%d")})
    return {"count": len(rows), "courses": rows}''', "my-courses")
src = rep(src, '''    done = set(json.loads(e.done_lessons or "[]"))
    return {"course_id": cid, "title": c.title, "progress": e.progress,
            "completed": e.completed, "last_lesson": e.last_lesson,
            "lessons": [{"id": l.id, "title": l.title, "position": l.position,
                         "description": l.description, "file": l.file,
                         "content": l.content or "", "video_url": l.video_url or "",
                         "done": l.id in done} for l in c.lessons],
            "quizzes": [{"id": q.id, "title": q.title, "time_limit_min": q.time_limit_min,
                         "passing_score": q.passing_score, "max_attempts": q.max_attempts}
                        for q in c.quizzes if q.published],
            "assignments": [{"id": a.id, "title": a.title, "instructions": a.instructions,
                             "due": a.due.strftime("%Y-%m-%d") if a.due else ""}
                            for a in c.assignments]}''',
'''    done = set(json.loads(e.done_lessons or "[]"))
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
                            for a in c.assignments]}''', "learn")
src = rep(src, '''    s.comment = comment
    s.draft = draft
    s.file = _save_upload(file) if file else s.file
    s.submitted = datetime.utcnow()
    session.add(s)
    session.commit()
    return {"message": "Draft saved." if draft else "Assignment submitted."}''',
'''    s.comment = comment
    s.draft = draft
    s.file = _save_upload(file) if file else s.file
    s.submitted = datetime.utcnow()
    session.add(s)
    session.commit()
    if not draft:
        m = session.get(db.User, c_mentor(session, a.course_id))
        if m:
            db.notify(session, m.id,
                      "%s submitted '%s' for grading" % (u.name, a.title),
                      "/dashboard", "grade")
    return {"message": "Draft saved." if draft else
            "Assignment submitted. Your instructor will grade it."}


def c_mentor(session, cid):
    c = session.get(db.Course, cid)
    return c.mentor_id if c else None''', "assign-submit")
save(P, src); print("assess ok")