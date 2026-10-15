import io
P = "app/routers/mentor.py"
src = io.open(P, encoding="utf-8").read().replace("\r\n", "\n")
old = '''    ungraded = (session.query.db if False else
                session.query(db.AssignSubmit).join(db.Assignment)
                .filter(db.Assignment.course_id.in_(ids or [-1]),
                        db.AssignSubmit.draft == False,  # noqa: E712
                        db.AssignSubmit.grade == None).count())  # noqa: E711'''
new = '''    ungraded = (session.query(db.AssignSubmit).join(db.Assignment)
                .filter(db.Assignment.course_id.in_(ids or [-1]),
                        db.AssignSubmit.draft.is_(False),
                        db.AssignSubmit.grade.is_(None)).count())'''
assert src.count(old) == 1
src = src.replace(old, new)
old2 = '''"""Mentor workspace: course studio, lessons, roster, grading, replies, profile."""
import json
from datetime import datetime
from fastapi import (APIRouter, Depends, File, Form, HTTPException, Request,
                     UploadFile)
from pydantic import BaseModel'''
new2 = '''"""Mentor workspace: course studio, lessons, roster, grading, replies, profile."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel'''
assert src.count(old2) == 1
src = src.replace(old2, new2)
io.open(P, "w", encoding="utf-8", newline="\n").write(src)
import ast; ast.parse(src); print("mentor.py cleaned", len(src))