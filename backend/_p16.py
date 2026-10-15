import io, ast
p = r"d:\skillhub\backend\app\routers\assess.py"
src = io.open(p, encoding="utf-8-sig").read()
old = """    rows = [{"learner": (session.get(db.User, s.learner_id) or db.User(name="")).name,
             "file": s.file, "comment": s.comment, "draft": s.draft,
             "submitted": s.submitted.strftime("%Y-%m-%d %H:%M")}
            for s in session.query(db.AssignSubmit).filter_by(assignment_id=aid).all()]
    return {"assignment": a.title, "submissions": rows}"""
assert src.count(old) == 1
new = """    rows = [{"id": s.id, "learner_id": s.learner_id,
              "learner": (session.get(db.User, s.learner_id) or db.User(name="")).name,
              "file": s.file, "comment": s.comment, "draft": s.draft,
              "grade": s.grade, "feedback": s.feedback or "",
              "marks": a.marks,
              "submitted": s.submitted.strftime("%Y-%m-%d %H:%M")}
             for s in session.query(db.AssignSubmit).filter_by(assignment_id=aid).all()]
    return {"assignment": a.title, "marks": a.marks,
            "ungraded": len([r for r in rows if not r["draft"] and r["grade"] is None]),
            "submissions": rows}"""
src = src.replace(old, new)
ast.parse(src)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("ok")