import io, ast
P="app/routers/product.py"
src=io.open(P,encoding="utf-8-sig").read().replace("\r\n","\n")
old='''                    "mine": bool(u and u.id == getattr(session, "_me_id", None)),\n'''
assert src.count(old)==1, src[src.find("mine")-120:src.find("mine")+120]
src=src.replace(old,"")
ast.parse(src); io.open(P,"w",encoding="utf-8",newline="\n").write(src); print("product cleaned")