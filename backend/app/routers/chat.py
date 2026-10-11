"""1:1 chat between learners and mentors (SRS item 12), polling-friendly."""
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db, current_user
from .assess import _save_upload

router = APIRouter(tags=["chat"])


@router.get("/chat/threads")
def threads(session: Session = Depends(get_db), u: db.User = Depends(current_user)):
    peer_ids = {m.sender_id if m.sender_id != u.id else m.receiver_id
                for m in session.query(db.ChatMsg).filter(
                    or_(db.ChatMsg.sender_id == u.id,
                        db.ChatMsg.receiver_id == u.id)).all()}
    out = []
    for pid in peer_ids:
        p = session.get(db.User, pid)
        last = session.query(db.ChatMsg).filter(
            or_(db.ChatMsg.sender_id == u.id, db.ChatMsg.receiver_id == u.id),
            or_(db.ChatMsg.sender_id == pid, db.ChatMsg.receiver_id == pid)
        ).order_by(db.ChatMsg.id.desc()).first()
        if p:
            out.append({"user_id": p.id, "name": p.name, "role": p.role,
                        "last": (last.text or "[attachment]") if last else "",
                        "last_ts": last.ts.strftime("%Y-%m-%d %H:%M") if last else ""})
    return {"threads": sorted(out, key=lambda x: x["last_ts"], reverse=True)}


@router.get("/chat/{peer_id}")
def conversation(peer_id: int, since_id: int = 0,
                 session: Session = Depends(get_db),
                 u: db.User = Depends(current_user)):
    rows = session.query(db.ChatMsg).filter(
        or_(db.ChatMsg.sender_id == u.id, db.ChatMsg.receiver_id == u.id),
        or_(db.ChatMsg.sender_id == peer_id, db.ChatMsg.receiver_id == peer_id),
        db.ChatMsg.id > since_id).order_by(db.ChatMsg.id).limit(200).all()
    peer = session.get(db.User, peer_id)
    return {"peer": {"id": peer.id, "name": peer.name, "role": peer.role} if peer else None,
            "messages": [{"id": m.id, "from": m.sender_id, "to": m.receiver_id,
                          "text": m.text, "file": m.file,
                          "ts": m.ts.strftime("%H:%M")} for m in rows]}


@router.post("/chat/{peer_id}")
async def send(peer_id: int, text: str = Form(""),
               file: UploadFile = File(default=None),
               session: Session = Depends(get_db),
               u: db.User = Depends(current_user)):
    peer = session.get(db.User, peer_id)
    if not peer:
        raise HTTPException(404, "User not found.")
    if not text.strip() and not file:
        raise HTTPException(400, "Message is empty.")
    m = db.ChatMsg(sender_id=u.id, receiver_id=peer_id, text=text.strip(),
                   file=_save_upload(file) if file else "")
    session.add(m)
    session.commit()
    if peer_id != u.id:
        db.notify(session, peer_id, "New message from %s" % u.name, "/chat")
    return {"message": "Sent.", "id": m.id}
