import io, ast
p = r"d:\skillhub\backend\app\routers\mentor.py"
src = io.open(p, encoding="utf-8-sig").read()
old = 'from fastapi import APIRouter, Depends, HTTPException, Request'
assert src.count(old) == 1
src = src.replace(old, 'import json\n' + old, 1)
ast.parse(src)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("ok")