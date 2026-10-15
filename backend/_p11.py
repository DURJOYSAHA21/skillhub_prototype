import io, ast
def load(p): return io.open(p, encoding="utf-8-sig").read().replace("\r\n","\n")
def save(p, src):
    ast.parse(src); io.open(p,"w",encoding="utf-8",newline="\n").write(src)
def rep(src, old, new, tag):
    assert src.count(old)==1, "MARKER FAIL "+tag
    return src.replace(old,new)

# ---------- admin analytics ----------
P="app/routers/admin.py"; src=load(P)
src = rep(src, '''    top = session.query(db.Course).filter_by(status="published") \\
        .order_by(db.Course.rating.desc()).limit(5).all()
    return {''',
'''    top = session.query(db.Course).filter_by(status="published") \\
        .order_by(db.Course.rating.desc()).limit(5).all()
    months, cursor = [], datetime.utcnow().replace(day=1)
    for _ in range(6):
        nxt = (cursor.replace(month=cursor.month + 1, year=cursor.year + 1)
               if cursor.month < 12 else
               cursor.replace(month=1, year=cursor.year + 1))
        rows = [t for t in txns if cursor <= t.created < nxt]
        months.append({"month": cursor.strftime("%Y-%m"),
                       "revenue": round(sum(t.amount for t in rows
                                            if t.status == "success"), 2),
                       "payments": len(rows)})
        cursor = (cursor.replace(month=cursor.month - 1, year=cursor.year)
                  if cursor.month > 1 else
                  cursor.replace(month=12, year=cursor.year - 1))
    months.reverse()
    cats = {}
    for c in session.query(db.Course).filter_by(status="published").all():
        e = cats.setdefault(c.category, {"category": c.category, "courses": 0,
                                         "students": 0})
        e["courses"] += 1
        e["students"] += session.query(db.Enrollment).filter_by(course_id=c.id).count()
    mentor_rows = []
    for m in session.query(db.User).filter_by(role="mentor").all():
        cs = session.query(db.Course).filter_by(mentor_id=m.id).all()
        cids = [c.id for c in cs]
        stu = session.query(db.Enrollment).filter(
            db.Enrollment.course_id.in_(cids or [-1])).count()
        rev = round(sum(t.amount for t in txns
                        if t.course_id in cids and t.status == "success"), 2)
        p = session.get(db.MentorProfile, m.id)
        mentor_rows.append({"mentor_id": m.id, "name": m.name, "students": stu,
                            "courses": len(cs), "revenue": rev,
                            "rating": p.rating if p else 0,
                            "verified": bool(p and p.verified)})
    mentor_rows.sort(key=lambda x: (-x["revenue"], -x["students"]))
    ens = session.query(db.Enrollment).all()
    week = datetime.utcnow() - timedelta(days=7)
    return {
        "monthly": months,
        "categories": sorted(cats.values(), key=lambda x: -x["students"])[:10],
        "top_mentors": mentor_rows[:5],
        "completion_rate": round(100.0 * len([e for e in ens if e.completed]) /
                                 len(ens), 1) if ens else 0,
        "avg_progress": round(sum(e.progress for e in ens) / len(ens), 1) if ens else 0,
        "new_users_7d": session.query(db.User).filter(db.User.created >= week).count(),
        "refunded": round(sum(t.amount for t in txns if t.status == "refunded"), 2),
        "low_ratings": session.query(db.Review).filter(db.Review.rating <= 2).count(),''',
    "analytics")
src = src.replace("from fastapi import APIRouter, Depends, HTTPException, Response",
                  "from datetime import timedelta\nfrom fastapi import APIRouter, Depends, HTTPException, Response")
save(P, src); print("analytics ok")

# ---------- match meta + mentor page ----------
P="app/routers/match.py"; src=load(P)
src = rep(src, '''@router.get("/meta")
def meta(session: Session = Depends(get_db)):
    skills = session.query(db.Skill).order_by(db.Skill.name).all()
    langs = session.query(db.Language).all()
    return {"skills": [{"id": s.id, "name": s.name, "category": s.category} for s in skills],
            "languages": [{"code": l.code, "name": l.name} for l in langs]}''',
'''@router.get("/meta")
def meta(session: Session = Depends(get_db)):
    skills = session.query(db.Skill).order_by(db.Skill.name).all()
    langs = session.query(db.Language).all()
    cats = session.query(db.Category).order_by(db.Category.name).all()
    names = sorted({c.category for c in session.query(db.Course)
                    .filter_by(status="published").all()} |
                   {c.name for c in cats})
    return {"skills": [{"id": s.id, "name": s.name, "category": s.category} for s in skills],
            "languages": [{"code": l.code, "name": l.name} for l in langs],
            "categories": [{"name": c.name, "icon": c.icon} for c in cats],
            "all_categories": names,
            "levels": ["Beginner", "Intermediate", "Advanced"]}''', "meta")
src = rep(src, '''    courses = [{"id": c.id, "title": c.title, "price": c.price, "language": c.language}
               for c in session.query(db.Course).filter_by(mentor_id=mid,
                                                           status="published").all()]
    return {"id": u.id, "name": u.name, "headline": p.headline if p else "",
            "country": p.country if p else "", "rating": p.rating if p else 0,
            "reviews": p.reviews if p else 0,''',
'''    courses = [{"id": c.id, "title": c.title, "price": c.price, "language": c.language,
                 "level": c.level, "rating": c.rating, "reviews": c.reviews,
                 "students": session.query(db.Enrollment).filter_by(course_id=c.id).count()}
                for c in session.query(db.Course).filter_by(mentor_id=mid,
                                                            status="published").all()]
    students = sum(session.query(db.Enrollment).filter_by(course_id=c["id"]).count()
                   for c in courses)
    return {"id": u.id, "name": u.name, "picture": u.picture or "",
            "headline": p.headline if p else "", "about": (p.about if p else "") or "",
            "verified": bool(p and p.verified), "students": students,
            "country": p.country if p else "", "rating": p.rating if p else 0,
            "reviews": p.reviews if p else 0,''', "mentor-page")
save(P, src); print("match ok")