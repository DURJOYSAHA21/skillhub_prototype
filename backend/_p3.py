import io, ast
P = "app/routers/admin.py"
src = io.open(P, encoding="utf-8-sig").read().replace("\r\n", "\n")

def rep(old, new):
    global src
    assert src.count(old) == 1, "MARKER: " + old[:50]
    src = src.replace(old, new)

rep('''from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session''',
    '''import csv, io as _io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..reports import certificate_pdf  # noqa: F401  (kept for parity)''')

rep('''class ApproveIn(BaseModel):
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
    label = {"published": "approved and is now live",
             "rejected": "rejected. You can edit and resubmit it.",
             "pending": "moved back to the review queue"}.get(body.status, body.status)
    db.notify(session, c.mentor_id,
              "Course update: '%s' was %s" % (c.title, label), "/dashboard")
    return {"message": f"Course {body.status}."}''',
    '''class ApproveIn(BaseModel):
    status: str      # published | rejected | pending | unpublished
    note: str = ""   # shown to the mentor


@router.put("/courses/{cid}/status")
def approve_course(cid: int, body: ApproveIn, session: Session = Depends(get_db),
                   a: db.User = Depends(_admin)):
    if body.status not in ("published", "rejected", "pending", "unpublished"):
        raise HTTPException(400, "Invalid status.")
    c = session.get(db.Course, cid)
    if not c:
        raise HTTPException(404, "Course not found.")
    c.status = body.status
    c.review_note = body.note.strip()
    c.updated = datetime.utcnow()
    session.commit()
    label = {"published": "approved and is now live",
             "rejected": "rejected. You can edit and resubmit it.",
             "pending": "moved back to the review queue",
             "unpublished": "taken off the catalogue"}.get(body.status, body.status)
    msg = "Course update: '%s' was %s" % (c.title, label)
    if body.note.strip():
        msg += " Note from the review team: " + body.note.strip()
    db.notify(session, c.mentor_id, msg, "/dashboard", "course")
    return {"message": "Course %s." % body.status, "note": c.review_note}''')

ADD = '''

def _students_of(session, cid):
    return session.query(db.Enrollment).filter_by(course_id=cid).count()


@router.get("/courses")
def all_courses(q: str = "", status: str = "", session: Session = Depends(get_db),
                a: db.User = Depends(_admin)):
    query = session.query(db.Course)
    if status:
        query = query.filter(db.Course.status == status)
    if q:
        like = "%" + q.lower() + "%"
        query = query.filter(db.Course.title.ilike(like))
    rows = []
    for c in query.order_by(db.Course.id.desc()).all():
        m = session.get(db.User, c.mentor_id)
        rev = sum(t.amount for t in session.query(db.Txn).filter_by(
            course_id=c.id, status="success").all())
        rows.append({"id": c.id, "title": c.title, "mentor": m.name if m else "",
                     "mentor_id": c.mentor_id, "category": c.category,
                     "language": c.language, "price": c.price, "status": c.status,
                     "lessons": len(c.lessons), "students": _students_of(session, c.id),
                     "rating": c.rating, "reviews": c.reviews, "revenue": round(rev, 2),
                     "featured": bool(c.featured),
                     "created": c.created.strftime("%Y-%m-%d"),
                     "note": c.review_note or ""})
    return {"count": len(rows), "courses": rows}


class FeatureIn(BaseModel):
    featured: bool = True


@router.put("/courses/{cid}/feature")
def feature_course(cid: int, body: FeatureIn, session: Session = Depends(get_db),
                   a: db.User = Depends(_admin)):
    c = session.get(db.Course, cid)
    if not c:
        raise HTTPException(404, "Course not found.")
    c.featured = bool(body.featured)
    if c.featured:
        c.status = "published"
    session.commit()
    db.notify(session, c.mentor_id,
              ("Your course '%s' was featured on the homepage!" % c.title
               if c.featured else "Your course '%s' is no longer featured." % c.title),
              "/dashboard", "course")
    return {"message": "Featured." if c.featured else "Unfeatured."}


@router.delete("/courses/{cid}")
def remove_course(cid: int, session: Session = Depends(get_db),
                  a: db.User = Depends(_admin)):
    c = session.get(db.Course, cid)
    if not c:
        raise HTTPException(404, "Course not found.")
    mid, title = c.mentor_id, c.title
    session.delete(c)
    session.commit()
    db.notify(session, mid, "Course '%s' was removed by the admin team." % title,
              "/dashboard", "course")
    return {"message": "Course and its lessons/quizzes removed."}


class VerifyIn(BaseModel):
    verified: bool = True


@router.put("/mentors/{mid}/verify")
def verify_mentor(mid: int, body: VerifyIn, session: Session = Depends(get_db),
                  a: db.User = Depends(_admin)):
    u = session.get(db.User, mid)
    if not u or u.role != "mentor":
        raise HTTPException(404, "Mentor not found.")
    p = session.get(db.MentorProfile, mid) or db.MentorProfile(user_id=mid)
    p.verified = bool(body.verified)
    session.add(p)
    session.commit()
    db.notify(session, mid,
              "You are now a verified SkillHub instructor." if p.verified
              else "Your verification badge was removed.", "/dashboard", "system")
    return {"message": "Verification updated.", "verified": bool(p.verified)}


class RoleIn(BaseModel):
    role: str


@router.put("/users/{uid}/role")
def set_role(uid: int, body: RoleIn, session: Session = Depends(get_db),
             a: db.User = Depends(_admin)):
    if body.role not in ("learner", "mentor", "admin"):
        raise HTTPException(400, "Role must be learner, mentor or admin.")
    u = session.get(db.User, uid)
    if not u:
        raise HTTPException(404, "User not found.")
    u.role = body.role
    if body.role == "mentor" and not session.get(db.MentorProfile, uid):
        session.add(db.MentorProfile(user_id=uid, headline="", verified=False))
    session.commit()
    db.notify(session, uid, "Your account role is now '%s'." % body.role,
              "/dashboard", "system")
    return {"message": "Role updated.", "role": u.role}


@router.get("/users/{uid}")
def user_detail(uid: int, session: Session = Depends(get_db),
                a: db.User = Depends(_admin)):
    u = session.get(db.User, uid)
    if not u:
        raise HTTPException(404, "User not found.")
    p = session.get(db.MentorProfile, uid)
    out = {"id": u.id, "name": u.name, "email": u.email, "phone": u.phone,
           "role": u.role, "status": u.status, "lang": u.lang,
           "created": u.created.strftime("%Y-%m-%d"),
           "last_login_fail": u.fail_count,
           "locked": bool(u.locked_until and u.locked_until > datetime.utcnow())}
    if u.role == "mentor":
        out["courses"] = [c.title for c in session.query(db.Course)
                          .filter_by(mentor_id=uid).all()]
        out["verified"] = bool(p and p.verified)
        out["headline"] = p.headline if p else ""
    if u.role == "learner":
        ens = session.query(db.Enrollment).filter_by(learner_id=uid).all()
        out["enrollments"] = [{"course": (session.get(db.Course, e.course_id)
                                          or db.Course(title="")).title,
                               "progress": e.progress} for e in ens]
        out["spend"] = round(sum(t.amount for t in session.query(db.Txn)
                                 .filter_by(learner_id=uid, status="success").all()), 2)
    return out


class UnlockIn(BaseModel):
    pass


@router.put("/users/{uid}/unlock")
def unlock(uid: int, session: Session = Depends(get_db), a: db.User = Depends(_admin)):
    u = session.get(db.User, uid)
    if not u:
        raise HTTPException(404, "User not found.")
    u.locked_until = None
    u.fail_count = 0
    session.commit()
    return {"message": "Login lock cleared."}


class BroadcastIn(BaseModel):
    message: str
    role: str = ""


@router.post("/broadcast")
def broadcast(body: BroadcastIn, session: Session = Depends(get_db),
              a: db.User = Depends(_admin)):
    if len(body.message.strip()) < 4:
        raise HTTPException(400, "Write a longer announcement.")
    if body.role not in ("", "admin", "mentor", "learner"):
        raise HTTPException(400, "Unknown audience.")
    n = db.notify_role(session, body.role, body.message.strip(), "/dashboard", "system",
                       exclude=a.id)
    return {"message": "Announcement sent to %d users." % n, "sent": n}


@router.get("/reviews")
def recent_reviews(status: str = "", session: Session = Depends(get_db),
                   a: db.User = Depends(_admin)):
    q = session.query(db.Review).order_by(db.Review.id.desc()).limit(100)
    rows = []
    for r in q.all():
        u = session.get(db.User, r.user_id)
        c = session.get(db.Course, r.course_id)
        rows.append({"id": r.id, "course": c.title if c else "", "course_id": r.course_id,
                     "name": u.name if u else "", "rating": r.rating,
                     "comment": r.comment, "reply": r.reply or "",
                     "date": r.created.strftime("%Y-%m-%d")})
    return {"reviews": rows}


@router.delete("/reviews/{rid}")
def delete_review(rid: int, session: Session = Depends(get_db),
                  a: db.User = Depends(_admin)):
    r = session.get(db.Review, rid)
    if not r:
        raise HTTPException(404, "Review not found.")
    c = session.get(db.Course, r.course_id)
    uid = r.user_id
    if c and c.reviews > 0:
        total = c.rating * c.reviews
        c.reviews -= 1
        c.rating = round(max(1.0, min(5.0, (total - r.rating) / c.reviews))
                         if c.reviews else 4.5, 2)
    session.delete(r)
    session.commit()
    db.notify(session, uid, "A review you posted was removed by the moderation team.",
              "/dashboard", "system")
    return {"message": "Review removed and the course average recalculated."}


@router.post("/reviews/{rid}/hide")
def hide_note(rid: int, session: Session = Depends(get_db),
              a: db.User = Depends(_admin)):
    r = session.get(db.Review, rid)
    if not r:
        raise HTTPException(404, "Review not found.")
    return {"message": "Flagged for follow-up.", "review_id": rid}


@router.get("/categories")
def list_categories(session: Session = Depends(get_db), a: db.User = Depends(_admin)):
    return {"categories": [{"name": x.name, "icon": x.icon}
                          for x in session.query(db.Category).all()]}


class CatIn(BaseModel):
    name: str
    icon: str = "📚"


@router.post("/categories")
def add_category(body: CatIn, session: Session = Depends(get_db),
                 a: db.User = Depends(_admin)):
    name = body.name.strip()
    if not name:
        raise HTTPException(400, "Category name is required.")
    if session.get(db.Category, name):
        raise HTTPException(400, "Category already exists.")
    session.add(db.Category(name=name, icon=body.icon or "\\ud83d\\udcda"))
    session.commit()
    return {"message": "Category added.", "name": name}


@router.delete("/categories/{name}")
def del_category(name: str, session: Session = Depends(get_db),
                 a: db.User = Depends(_admin)):
    cat = session.get(db.Category, name)
    if not cat:
        raise HTTPException(404, "Category not found.")
    used = session.query(db.Course).filter_by(category=name).count()
    if used:
        raise HTTPException(400, "Category is used by %d courses." % used)
    session.delete(cat)
    session.commit()
    return {"message": "Category removed."}


@router.post("/txns/{tid}/refund")
def refund(tid: int, session: Session = Depends(get_db), a: db.User = Depends(_admin)):
    t = session.get(db.Txn, tid)
    if not t:
        raise HTTPException(404, "Transaction not found.")
    if t.status == "refunded":
        raise HTTPException(400, "Already refunded.")
    if t.status != "success":
        raise HTTPException(400, "Only successful payments can be refunded.")
    t.status = "refunded"
    session.commit()
    c = session.get(db.Course, t.course_id)
    where = "/learn/%d" % c.id if c and session.query(db.Enrollment).filter_by(
        learner_id=t.learner_id, course_id=c.id).first() else "/dashboard"
    db.notify(session, t.learner_id,
              "Payment %s of \\u09f3%s was refunded." % (t.ref, t.amount), where, "payment")
    if c:
        db.notify(session, c.mentor_id,
                  "Payment %s on '%s' was refunded." % (t.ref, c.title),
                  "/dashboard", "payment")
    return {"message": "Refund recorded.", "amount": t.amount}


@router.get("/enrollments")
def enrollments(course_id: int = 0, session: Session = Depends(get_db),
                a: db.User = Depends(_admin)):
    q = session.query(db.Enrollment)
    if course_id:
        q = q.filter_by(course_id=course_id)
    rows = []
    for e in q.order_by(db.Enrollment.id.desc()).limit(200).all():
        u = session.get(db.User, e.learner_id)
        c = session.get(db.Course, e.course_id)
        rows.append({"id": e.id, "learner": u.name if u else "", "learner_id": e.learner_id,
                     "course": c.title if c else "", "course_id": e.course_id,
                     "progress": e.progress, "completed": bool(e.completed),
                     "enrolled": e.enrolled.strftime("%Y-%m-%d")})
    return {"enrollments": rows}


@router.delete("/enrollments/{eid}")
def drop_enrollment(eid: int, session: Session = Depends(get_db),
                    a: db.User = Depends(_admin)):
    e = session.get(db.Enrollment, eid)
    if not e:
        raise HTTPException(404, "Enrollment not found.")
    uid, cid = e.learner_id, e.course_id
    session.delete(e)
    session.commit()
    db.notify(session, uid, "Your enrollment was adjusted by the support team.",
              "/dashboard", "system")
    return {"message": "Enrollment removed.", "course_id": cid}


@router.get("/export/{what}")
def export_csv(what: str, session: Session = Depends(get_db),
               a: db.User = Depends(_admin)):
    buf = _io.StringIO()
    w = csv.writer(buf)
    if what == "users":
        w.writerow(["id", "name", "email", "phone", "role", "status", "created"])
        for x in session.query(db.User).all():
            w.writerow([x.id, x.name, x.email, x.phone, x.role, x.status,
                        x.created.strftime("%Y-%m-%d")])
    elif what == "courses":
        w.writerow(["id", "title", "mentor", "category", "language", "price",
                    "status", "lessons", "students", "rating", "reviews"])
        for c in session.query(db.Course).all():
            m = session.get(db.User, c.mentor_id)
            w.writerow([c.id, c.title, m.name if m else "", c.category, c.language,
                        c.price, c.status, len(c.lessons),
                        _students_of(session, c.id), c.rating, c.reviews])
    elif what == "transactions":
        w.writerow(["ref", "date", "learner", "course", "method", "amount", "status"])
        for t in session.query(db.Txn).all():
            u = session.get(db.User, t.learner_id)
            c = session.get(db.Course, t.course_id)
            w.writerow([t.ref, t.created.strftime("%Y-%m-%d %H:%M"),
                        u.name if u else "", c.title if c else "", t.method,
                        t.amount, t.status])
    elif what == "enrollments":
        w.writerow(["id", "learner", "course", "progress", "completed", "enrolled"])
        for e in session.query(db.Enrollment).all():
            u = session.get(db.User, e.learner_id)
            c = session.get(db.Course, e.course_id)
            w.writerow([e.id, u.name if u else "", c.title if c else "",
                        e.progress, int(bool(e.completed)),
                        e.enrolled.strftime("%Y-%m-%d")])
    else:
        raise HTTPException(400, "Export must be users, courses, transactions or enrollments.")
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=skillhub-%s.csv" % what})
'''
src = src.rstrip() + ADD
ast.parse(src)
io.open(P, "w", encoding="utf-8", newline="\n").write(src + "\n")
print("admin.py ->", len(src))