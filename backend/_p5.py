import io, ast
def load(p): return io.open(p, encoding="utf-8-sig").read().replace("\r\n","\n")
def save(p, src):
    ast.parse(src); io.open(p,"w",encoding="utf-8",newline="\n").write(src)
def rep(src, old, new, tag):
    assert src.count(old)==1, "MARKER FAIL "+tag
    return src.replace(old,new)

P="app/routers/auth.py"; src=load(P)
src = rep(src, '''def _public(u: db.User):
    p = None
    if u.role == "mentor":
        p = None
    return {''', '''def _public(u: db.User):
    return {''', "auth-cruft")
save(P, src); print("auth cleaned")

P="app/routers/product.py"; src=load(P)
src = rep(src, '''                    "reply": r.reply or "",
                    "mine": bool(u and u.id == getattr(session, "_me_id", None)),
''', '''                    "reply": r.reply or "",
''', "prod-mine")
save(P, src); print("product cleaned")