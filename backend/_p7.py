import io, ast
def load(p): return io.open(p, encoding="utf-8-sig").read().replace("\r\n","\n")
def save(p, src):
    ast.parse(src); io.open(p,"w",encoding="utf-8",newline="\n").write(src)
def rep(src, old, new, tag):
    assert src.count(old)==1, "MARKER FAIL "+tag
    return src.replace(old,new)

# ------------------- courses.py -------------------
P="app/routers/courses.py"; src=load(P)
src = rep(src, '''def _course_dict(c: db.Course, mentor_name: str = "", owner: bool = False):
    return {"id": c.id, "title": c.title, "description": c.description,
            "category": c.category, "language": c.language, "price": c.price,
            "type": c.type, "duration_hours": c.duration_hours, "status": c.status,
            "rating": c.rating, "reviews": c.reviews, "mentor": mentor_name,
            "mentor_id": c.mentor_id,''',
'''def _course_dict(c: db.Course, mentor_name: str = "", owner: bool = False,
                 students: int = 0, mentor_id_of=None):
    return {"id": c.id, "title": c.title, "description": c.description,
            "category": c.category, "language": c.language, "price": c.price,
            "type": c.type, "level": c.level, "tags": c.tags or "",
            "thumbnail": c.thumbnail or "", "duration_hours": c.duration_hours,
            "status": c.status, "students": students,
            "featured": bool(c.featured),
            "note": (c.review_note or "") if owner else "",
            "rating": c.rating, "reviews": c.reviews, "mentor": mentor_name,
            "mentor_id": c.mentor_id,''', "cd-dict")
src = rep(src, '''class CourseIn(BaseModel):
    title: str
    description: str = ""
    category: str = "Tech"
    language: str = "en"
    price: float = 0
    duration_hours: float = 4''',
'''class CourseIn(BaseModel):
    title: str
    description: str = ""
    category: str = "Tech"
    language: str = "en"
    price: float = 0
    duration_hours: float = 4
    level: str = "Beginner"
    tags: str = ""''', "cd-in")
src = rep(src, '''    c = db.Course(mentor_id=u.id, title=body.title.strip(),
                  description=body.description, category=body.category,
                  language=body.language, price=max(0.0, body.price),
                  type="paid" if body.price > 0 else "free",
                  duration_hours=body.duration_hours, status="pending")
    session.add(c)
    session.commit()
    return {"message": "Course saved. Status: Pending until admin approval.",
            "course": _course_dict(c, u.name, owner=True)}''',
'''    c = db.Course(mentor_id=u.id, title=body.title.strip(),
                  description=body.description, category=body.category,
                  language=body.language, price=max(0.0, body.price),
                  type="paid" if body.price > 0 else "free",
                  level=body.level or "Beginner", tags=body.tags.strip(),
                  duration_hours=body.duration_hours, status="pending")
    session.add(c)
    session.flush()
    db.notify_role(session, "admin",
                   "New course awaiting review: '%s' by %s (\\u09f3%s, %s)"
                   % (c.title, u.name, c.price, c.category),
                   "/dashboard", "course")
    session.commit()
    return {"message": "Course submitted for admin approval. You will be notified "
                       "as soon as it is reviewed.",
            "id": c.id, "status": c.status,
            "course": _course_dict(c, u.name, owner=True)}''', "cd-create")
src = rep(src, '''    c.title, c.description, c.category = body.title.strip(), body.description, body.category
    c.language, c.duration_hours = body.language, body.duration_hours
    c.price = max(0.0, body.price)
    c.type = "paid" if c.price > 0 else "free"
    session.commit()
    return {"message": "Course info updated successfully."}''',
'''    c.title, c.description, c.category = body.title.strip(), body.description, body.category
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
    return {"message": "Cover image saved.", "thumbnail": c.thumbnail}''', "cd-edit")
src = rep(src, '''    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    session.delete(c)
    session.commit()
    return {"message": "Course deleted successfully."}''',
'''    if not c or (c.mentor_id != u.id and u.role != "admin"):
        raise HTTPException(404, "Course not found.")
    mid = c.mentor_id
    session.delete(c)
    session.commit()
    if u.role == "admin":
        db.notify(session, mid, "Your course '%s' was removed by the admin team."
                  % c.title, "/dashboard", "course")
    return {"message": "Course deleted successfully."}''', "cd-delete")
# richer catalogue query
src = rep(src, '''@router.get("/courses")
def list_courses(q: str = "", category: str = "", language: str = "",
                 max_price: float = 0, min_rating: float = 0,
                 mine: str = "", authorization: str = Header(default=""),
                 session: Session = Depends(get_db)):
    query = session.query(db.Course)
    me = _optional_user(authorization, session)
    if mine == "mentor" and me and me.role == "mentor":
        query = query.filter(db.Course.mentor_id == me.id)   # incl. pending
    else:
        query = query.filter(db.Course.status == "published")''',
'''@router.get("/courses")
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
        query = query.filter(db.Course.price >= min_price)''', "cd-list")
src = rep(src, '''    out = []
    for c in query.order_by(db.Course.rating.desc()).all():
        m = session.get(db.User, c.mentor_id)
        out.append(_course_dict(c, m.name if m else "",
                                owner=bool(me and me.id == c.mentor_id)))
    return {"count": len(out), "courses": out}''',
'''    if sort == "newest":
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
    return {"count": len(out), "courses": out}''', "cd-listout")
save(P, src); print("courses ok")