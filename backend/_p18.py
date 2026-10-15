import io, ast
p = r"d:\skillhub\backend\app\routers\match.py"
src = io.open(p, encoding="utf-8-sig").read()
old = '''            "languages": [f"{lang_names.get(l.code, l.code)} ({l.fluency})"
                          for l in session.query(db.MentorLanguage).filter_by(user_id=mid).all()],'''
assert src.count(old) == 1
new = '''            "languages": [f"{lang_names.get(l.code, l.code)} ({l.fluency})"
                          for l in session.query(db.MentorLanguage).filter_by(user_id=mid).all()],
            "langs": [{"code": l.code, "fluency": l.fluency}
                      for l in session.query(db.MentorLanguage).filter_by(user_id=mid).all()],'''
src = src.replace(old, new)
ast.parse(src)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("ok")