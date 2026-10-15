import io, ast
def load(p):
    return io.open(p, encoding="utf-8-sig").read().replace("\r\n", "\n")
def save(p, src):
    ast.parse(src)
    io.open(p, "w", encoding="utf-8", newline="\n").write(src)
def rep(src, old, new, tag=""):
    assert src.count(old) == 1, "MARKER FAIL " + tag + ": " + old[:60]
    return src.replace(old, new)

# ---------------- db.py: chat read flag ----------------
P = "app/db.py"; src = load(P)
src = rep(src, '''    file = Column(String, default="")
    ts = Column(DateTime, default=datetime.utcnow)''',
    '''    file = Column(String, default="")
    read = Column(Boolean, default=False)
    ts = Column(DateTime, default=datetime.utcnow)''', "db-chat")
save(P, src); print("db chat ok")

# ---------------- auth.py ----------------
P = "app/routers/auth.py"; src = load(P)
src = rep(src, '''def _public(u: db.User):
    return {"id": u.id, "name": u.name, "email": u.email, "phone": u.phone,
            "role": u.role, "lang": u.lang, "status": u.status}''',
'''def _public(u: db.User):
    p = None
    if u.role == "mentor":
        p = _session_for_profile
    return {"id": u.id, "name": u.name, "email": u.email, "phone": u.phone,
            "role": u.role, "lang": u.lang, "status": u.status,
            "dob": u.dob or "", "gender": u.gender or "",
            "picture": u.picture or "", "goals": json.loads(u.goals or "[]")}''', "auth-public")
src = rep(src, '''"""Auth & profile endpoints (SRS items 1-6)."""
import re''', '''"""Auth & profile endpoints (SRS items 1-6)."""
import json
import re''', "auth-import")
src = src.replace("_session_for_profile", "None")
src = rep(src, '''    code, sent = _issue(session, u.email, "signup", u.id)
    out = {"message": ("Account created. An OTP has been emailed to you."
                       if sent else "Account created. Verify OTP to activate.")}''',
'''    if body.role == "mentor":
        session.add(db.MentorProfile(user_id=u.id, headline="", verified=False))
    db.notify_role(session, "admin",
                   "New %s registered: %s (%s)" % (body.role, u.name, u.email),
                   "/dashboard", "system", exclude=u.id)
    session.commit()
    code, sent = _issue(session, u.email, "signup", u.id)
    out = {"message": ("Account created. An OTP has been emailed to you."
                       if sent else "Account created. Verify OTP to activate.")}''', "auth-signup")
src = rep(src, '''    u.status = "active"
    session.commit()
    return {"message": "Email verified successfully.", "token": create_token(u.id, u.role),''',
'''    u.status = "active"
    session.commit()
    if u.role == "mentor":
        db.notify_role(session, "admin",
                       "Mentor profile ready for review: %s" % u.name,
                       "/dashboard", "system", exclude=u.id)
    return {"message": "Email verified successfully.", "token": create_token(u.id, u.role),''', "auth-verify")
src = rep(src, '''    if body.lang and body.lang not in ("en", "bn"):
        raise HTTPException(400, "Unsupported language.")''',
'''    if body.lang and not session.get(db.Language, body.lang):
        raise HTTPException(400, "Unsupported language.")''', "auth-lang")
src = rep(src, '''class ProfileIn(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    dob: str = ""
    gender: str = ""
    lang: str = ""''',
'''class ProfileIn(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    dob: str = ""
    gender: str = ""
    lang: str = ""
    goals: str = ""            # comma separated skill names
    notify_email: bool = True''', "auth-profile-in")
src = rep(src, '''    u.lang = body.lang or u.lang          # req #13: preference persisted per user
    session.commit()
    return {"message": "Profile info updated successfully.", "user": _public(u)}''',
'''    u.lang = body.lang or u.lang          # req #13: preference persisted per user
    u.notify_email = bool(body.notify_email)
    if body.goals:
        names = [g.strip() for g in body.goals.split(",") if g.strip()][:12]
        u.goals = json.dumps(names)
    session.commit()
    return {"message": "Profile info updated successfully.", "user": _public(u)}


@router.post("/picture")
async def upload_picture(request: Request, session: Session = Depends(get_db),
                         u: db.User = Depends(current_user)):
    form = await request.form()
    up = form.get("file") if hasattr(form, "get") else None
    if up is None or not hasattr(up, "filename") or not up.filename:
        raise HTTPException(400, "Choose an image file first.")
    from .courses import _save_upload
    u.picture = _save_upload(up)
    session.commit()
    return {"message": "Photo updated.", "picture": u.picture}''', "auth-profile-out")
src = rep(src, '''from fastapi import APIRouter, Depends, HTTPException''',
          '''from fastapi import APIRouter, Depends, HTTPException, Request''', "auth-req")
save(P, src); print("auth ok")

# ---------------- chat.py ----------------
P = "app/routers/chat.py"; src = load(P)
src = rep(src, '''        if p:
            out.append({"user_id": p.id, "name": p.name, "role": p.role,
                        "last": (last.text or "[attachment]") if last else "",
                        "last_ts": last.ts.strftime("%Y-%m-%d %H:%M") if last else ""})''',
'''        if p:
            unread = session.query(db.ChatMsg).filter_by(receiver_id=u.id,
                                                         sender_id=pid,
                                                         read=False).count()
            out.append({"user_id": p.id, "name": p.name, "role": p.role,
                        "last": (last.text or "[attachment]") if last else "",
                        "last_ts": last.ts.strftime("%Y-%m-%d %H:%M") if last else "",
                        "unread": unread})''', "chat-threads")
src = rep(src, '''    peer = session.get(db.User, peer_id)
    return {"peer": {"id": peer.id, "name": peer.name, "role": peer.role} if peer else None,
            "messages": [{"id": m.id, "from": m.sender_id, "to": m.receiver_id,
                          "text": m.text, "file": m.file,
                          "ts": m.ts.strftime("%H:%M")} for m in rows]}''',
'''    peer = session.get(db.User, peer_id)
    for m in rows:
        if m.receiver_id == u.id and not m.read:
            m.read = True
    session.commit()
    return {"peer": {"id": peer.id, "name": peer.name, "role": peer.role} if peer else None,
            "messages": [{"id": m.id, "from": m.sender_id, "to": m.receiver_id,
                          "text": m.text, "file": m.file,
                          "ts": m.ts.strftime("%H:%M")} for m in rows]}''', "chat-conv")
src = rep(src, '''    m = db.ChatMsg(sender_id=u.id, receiver_id=peer_id, text=text.strip(),''',
'''    db.notify(session, peer_id, "%s sent you a message: %s" %
              (u.name, (text.strip() or "[attachment]")[:70]),
              "/chat?to=%d" % u.id, "chat")
    m = db.ChatMsg(sender_id=u.id, receiver_id=peer_id, text=text.strip(),''', "chat-send")
save(P, src); print("chat ok")

# ---------------- enroll.py ----------------
P = "app/routers/enroll.py"; src = load(P)
src = rep(src, '''    db.notify(session, c.mentor_id,
              "%s enrolled in '%s'" % (u.name, c.title), "/dashboard")''',
'''    db.notify(session, c.mentor_id,
              "%s enrolled in '%s'" % (u.name, c.title), "/dashboard", "course")
    db.notify(session, u.id, "You are enrolled in '%s'. Start learning anytime!"
              % c.title, "/learn/%d" % c.id, "course")''', "enroll-free")
src = rep(src, '''    if not re.fullmatch(r"\\d{12,19}", body.card_number):''',
'''    if session.query(db.Enrollment).filter_by(learner_id=u.id, course_id=c.id).first():
        raise HTTPException(400, "You already have access to this course.")
    if not re.fullmatch(r"\\d{12,19}", body.card_number):''', "enroll-dup")
src = rep(src, '''    db.notify(session, u.id,
              "Payment confirmed for '%s' (%s)" % (c.title, ref),
              "/learn/%d" % c.id)
    db.notify(session, c.mentor_id,
              "New sale: '%s' bought by %s" % (c.title, u.name), "/dashboard")''',
'''    db.notify(session, u.id,
              "Payment confirmed for '%s' (%s)" % (c.title, ref),
              "/learn/%d" % c.id, "payment")
    db.notify(session, c.mentor_id,
              "New sale: '%s' bought by %s" % (c.title, u.name), "/dashboard", "payment")''',
    "enroll-pay")
src = rep(src, '''             "amount": t.amount, "method": t.method, "card_last4": t.card_last4,
             "status": t.status} for t in rows]''',
'''             "amount": t.amount, "method": t.method, "card_last4": t.card_last4,
             "course_id": t.course_id, "learner_id": t.learner_id,
             "status": t.status} for t in rows]''', "enroll-txnrow")
save(P, src); print("enroll ok")

# ---------------- product.py ----------------
P = "app/routers/product.py"; src = load(P)
src = rep(src, '''        out.append({"id": r.id, "name": u.name if u else "", "rating": r.rating,
                    "comment": r.comment, "date": r.created.strftime("%Y-%m-%d")})''',
'''        out.append({"id": r.id, "name": u.name if u else "", "rating": r.rating,
                    "comment": r.comment, "reply": r.reply or "",
                    "mine": bool(u and u.id == getattr(session, "_me_id", None)),
                    "date": r.created.strftime("%Y-%m-%d")})''', "prod-reviews")
src = rep(src, '''    db.notify(session, c.mentor_id,
              "New %d-star review on '%s'" % (body.rating, c.title),
              "/course/%d" % cid)''',
'''    db.notify(session, c.mentor_id,
              "New %d-star review on '%s'" % (body.rating, c.title),
              "/course/%d" % cid, "course")
    if body.rating <= 2:
        db.notify_role(session, "admin",
                       "Low rating (%d/5) on '%s' - worth a look" % (body.rating, c.title),
                       "/dashboard", "system")''', "prod-notify")
src = rep(src, '''    return {"notifications": [{"id": n.id, "message": n.message, "link": n.link,
                               "read": bool(n.read),''',
'''    return {"notifications": [{"id": n.id, "message": n.message, "link": n.link,
                               "kind": n.kind or "info", "read": bool(n.read),''',
    "prod-notif")
src = rep(src, '''@router.post("/wishlist/{cid}")''',
'''@router.delete("/wishlist/{cid}")
def remove_wish(cid: int, session: Session = Depends(get_db),
                u: db.User = Depends(current_user)):
    w = session.query(db.Wishlist).filter_by(user_id=u.id, course_id=cid).first()
    if w:
        session.delete(w)
        session.commit()
    return {"saved": False, "message": "Removed from your saved list."}


@router.post("/wishlist/{cid}")''', "prod-delwish")
save(P, src); print("product ok")

# ---------------- main.py: register routers ----------------
P = "app/main.py"; src = load(P)
src = rep(src, '''from .routers import auth, courses, enroll, assess, chat, admin, match, product''',
'''from .routers import (auth, courses, enroll, assess, chat, admin, match, product,
                     mentor, learner, bot)''', "main-import")
src = rep(src, '''for r in (auth.router, courses.router, enroll.router, assess.router,
          chat.router, admin.router, match.router, product.router):''',
'''for r in (auth.router, courses.router, enroll.router, assess.router,
          chat.router, admin.router, match.router, product.router,
          mentor.router, learner.router, bot.router):''', "main-reg")
save(P, src); print("main ok")