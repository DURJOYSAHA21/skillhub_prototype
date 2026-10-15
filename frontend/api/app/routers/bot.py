"""SkillHub helper bot: grounded, on-platform assistant (no external API).

It answers from the live database (courses, mentors, your own progress) and
routes anything it cannot resolve to a human. Optional auth: pass a bearer
token and it can talk about *your* enrolments, progress and payments.
"""
import re
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db
from ..engine import resolve_skill, rank_mentors
from ..security import decode_token

router = APIRouter(tags=["bot"])

TAKA = "\u09f3"


def _user(authorization: str, session: Session):
    if authorization and authorization.startswith("Bearer "):
        payload = decode_token(authorization[7:])
        if payload:
            return session.get(db.User, int(payload["sub"]))
    return None


class AskIn(BaseModel):
    message: str
    session_id: str = ""


def _link(label, href):
    return {"label": label, "href": href}


def _find_courses(session, text, limit=3):
    words = re.findall(r"[A-Za-z][A-Za-z+#.]{2,24}", text.lower())
    stop = {"course", "courses", "a", "an", "the", "me", "for", "with", "show",
            "find", "any", "want", "need", "please", "best", "good", "top",
            "teach", "teaching", "learn", "class", "classes", "do", "you"}
    keys = [w.strip() for w in words if w.strip() not in stop]
    q = session.query(db.Course).filter(db.Course.status == "published")
    hits, seen = [], set()
    for k in keys:
        for c in q.filter(db.Course.title.ilike("%" + k + "%")).all():
            if c.id not in seen:
                seen.add(c.id)
                hits.append(c)
    if not hits:
        for k in keys:
            for c in q.filter(db.Course.description.ilike("%" + k + "%")).all():
                if c.id not in seen:
                    seen.add(c.id)
                    hits.append(c)
    return hits[:limit], keys


def _free_paid(session):
    pub = session.query(db.Course).filter_by(status="published").all()
    free = len([c for c in pub if c.price <= 0])
    return free, len(pub) - free


@router.get("/bot/starters")
def starters(authorization: str = Header(default=""),
             session: Session = Depends(get_db)):
    u = _user(authorization, session)
    role = u.role if u else "guest"
    base = ["Find a free course", "How do I pay?", "Talk to a human"]
    return {
        "role": role,
        "greeting": ("Hi%s! I am SkillHub Assist. Ask me about courses, "
                     "enrolment, payments, your progress, quizzes or "
                     "certificates." % ((" " + u.name) if u else "")),
        "chips": {
            "guest": ["Find a free course", "How do I become a mentor?",
                      "Match me with a mentor", "Talk to a human"],
            "learner": ["My progress", "Find a free course", "When do I get a "
                        "certificate?", "My payment problem", "Talk to a human"],
            "mentor": ["Course approval status", "How do I add a lesson?",
                       "Grading submissions", "Talk to a human"],
            "admin": ["What is pending review?", "Platform numbers",
                      "Refund a payment", "Announce something"],
        }[role],
    }


@router.post("/bot/ask")
def ask(body: AskIn, authorization: str = Header(default=""),
        session: Session = Depends(get_db)):
    text = (body.message or "").strip()
    low = text.lower()
    u = _user(authorization, session)
    if not text:
        return {"reply": "Type a question and I will do my best.", "actions": [],
                "chips": ["Find a free course", "Talk to a human"]}

    # --- account / auth help
    if any(k in low for k in ("password", "locked", "can not log in", "cannot log in",
                              "sign in", "login")):
        return {"reply": "Use /forgot and the OTP code to reset your password. "
                         "After 5 wrong tries the account locks for 30 minutes - "
                         "an admin can clear that lock from the dashboard.",
                "actions": [_link("Reset password", "/forgot")],
                "chips": ["Talk to a human"]}

    # --- becoming a mentor
    if "mentor" in low and any(k in low for k in ("become", "teach", "create account",
                                                  "sell course", "instructor")):
        return {"reply": "Sign up choosing the Mentor role, then in your dashboard "
                         "use 'Create a course'. It lands in the admin review queue "
                         "and you get a notification the moment it is approved.",
                "actions": [_link("Sign up as mentor", "/signup"),
                            _link("My dashboard", "/dashboard")],
                "chips": ["How do I add a lesson?"]}

    # --- lessons / content
    if "lesson" in low and any(k in low for k in ("add", "upload", "create", "video",
                                                  "how")):
        return {"reply": "In your mentor dashboard use 'Upload a lesson': pick the "
                         "course, add a title, notes, a YouTube link and optionally a "
                         "file. Learners read the notes and watch the video inside "
                         "SkillHub.",
                "actions": [_link("Open dashboard", "/dashboard")], "chips": []}

    # --- grading
    if "grad" in low:
        return {"reply": "Open the assignment in your dashboard's assessment "
                         "builder to see every submission, then save a mark out of "
                         "the assignment total plus written feedback. The learner is "
                         "notified instantly.",
                "actions": [_link("Open dashboard", "/dashboard")], "chips": []}

    # --- approval status (mentor) or pending review (admin)
    if "approv" in low or "pending" in low or "reject" in low:
        if u and u.role == "admin":
            rows = session.query(db.Course).filter_by(status="pending").all()
            if not rows:
                return {"reply": "Nothing is waiting for review right now.",
                        "actions": [_link("Admin dashboard", "/dashboard")], "chips": []}
            names = ", ".join("#%d %s" % (c.id, c.title) for c in rows[:4])
            return {"reply": "%d course(s) await your decision: %s. Approve or "
                             "reject with a note in Manage Courses."
                             % (len(rows), names),
                    "actions": [_link("Review queue", "/dashboard")],
                    "chips": ["Platform numbers"]}
        if u and u.role == "mentor":
            mine = session.query(db.Course).filter_by(mentor_id=u.id).all()
            pend = [c for c in mine if c.status == "pending"]
            rej = [c for c in mine if c.status == "rejected"]
            pub = [c for c in mine if c.status == "published"]
            return {"reply": "You have %d published, %d awaiting review and %d "
                             "rejected course(s). Rejected ones show the reviewer's "
                             "note - edit and resubmit any time."
                             % (len(pub), len(pend), len(rej)),
                    "actions": [_link("My courses", "/dashboard")], "chips": []}
        return {"reply": "Courses are reviewed by the SkillHub admin team before they "
                         "go live. Mentors get a notification either way.",
                "actions": [_link("Browse live courses", "/browse")], "chips": []}

    # --- payments / refunds
    if any(k in low for k in ("pay", "payment", "refund", "card", "otp", "bKash",
                              "receipt", "price", "cost", "charged")):
        if "refund" in low:
            return {"reply": "Refunds are handled by the admin team from "
                             "Transactions - they mark the payment refunded and both "
                             "you and the instructor are notified.",
                    "actions": [_link("My transactions", "/dashboard"),
                                _link("Talk to a human", "/chat")], "chips": []}
        if u and u.role == "admin":
            rows = session.query(db.Txn).filter_by(status="success").all()
            return {"reply": "You can refund any successful payment from the "
                             "Transactions tab (total collected: %s%s across %d "
                             "payments)." % (TAKA, round(sum(r.amount for r in rows), 2),
                                             len(rows)),
                    "actions": [_link("Transactions", "/dashboard")], "chips": []}
        return {"reply": "Paid courses use the simulated bank flow: choose a method, "
                         "enter card + PIN, confirm the OTP, and you are enrolled "
                         "instantly with a receipt PDF. Free courses enrol with one "
                         "click.",
                "actions": [_link("Browse courses", "/browse"),
                            _link("My transactions", "/dashboard")],
                "chips": ["Any free courses?"]}

    # --- progress / certificate / results (learner)
    if any(k in low for k in ("progress", "certificate", "how far", "score",
                              "grade", "result", "completed", "where am i")):
        if u and u.role == "learner":
            ens = session.query(db.Enrollment).filter_by(learner_id=u.id).all()
            if not ens:
                return {"reply": "You are not enrolled yet - pick a course and the "
                                 "free ones enrol with one click.",
                        "actions": [_link("Browse courses", "/browse")], "chips": []}
            done = [e for e in ens if e.completed]
            lines = []
            for e in ens[:5]:
                c = session.get(db.Course, e.course_id)
                if c:
                    lines.append("%s (%d%%)" % (c.title, e.progress))
            return {"reply": "You are in %d course(s), finished %d: %s. "
                             "Certificates unlock at 100%%."
                             % (len(ens), len(done), "; ".join(lines)),
                    "actions": [_link("Continue learning", "/dashboard"),
                                _link("My certificates", "/dashboard")],
                    "chips": ["When do I get a certificate?"]}
        return {"reply": "Your dashboard shows progress per course. Finishing every "
                         "lesson and passing each quiz marks the course complete and "
                         "unlocks the certificate PDF.",
                "actions": [_link("Dashboard", "/dashboard")], "chips": []}

    if "certificate" in low:
        return {"reply": "Complete every lesson and pass all published quizzes; the "
                         "'Download Certificate (PDF)' button then appears on the "
                         "learning page and your dashboard.",
                "actions": [_link("My learning", "/dashboard")], "chips": []}

    # --- mentor matching
    if any(k in low for k in ("mentor for", "who can teach", "find a mentor",
                              "match", "instructor for", "coach")):
        skills, aliases, lang_names, mentors = db.load_engine_state(session)
        sid, _ = resolve_skill(text, skills, aliases)
        ranked = rank_mentors(mentors, sid, [], limit=3) if sid else []
        if ranked:
            lines = ["%s - %d%% match (%s, rating %s)"
                     % (r.mentor.name, round(r.score * 100), r.mentor.country,
                        r.mentor.rating) for r in ranked]
            return {"reply": "Best mentors for that skill: " + "; ".join(lines),
                    "actions": [_link("Open SkillHub Match", "/match"),
                                _link("Message %s" % ranked[0].mentor.name,
                                      "/chat?to=%d" % ranked[0].mentor.id)],
                    "chips": ["Find a free course"]}
        return {"reply": "Tell me the skill (for example 'Excel' or 'UI/UX') and I "
                         "will rank the mentors who teach it in your language.",
                "actions": [_link("SkillHub Match", "/match")], "chips": []}

    # --- wishlist / notifications / chat
    if "wishlist" in low or "saved" in low:
        return {"reply": "Tap the heart on any course card to save it; your saved "
                         "list is on the learner dashboard.",
                "actions": [_link("Saved courses", "/dashboard"),
                            _link("Browse", "/browse")], "chips": []}
    if "notification" in low or "bell" in low:
        return {"reply": "The bell in the header shows approvals, payments, "
                         "messages, grades and replies. New items arrive within "
                         "30 seconds.", "actions": [_link("Dashboard", "/dashboard")],
                "chips": []}

    # --- human handoff
    if any(k in low for k in ("human", "support", "help me", "agent", "complaint",
                              "problem", "talk to")):
        who = None
        if u:
            if u.role == "learner":
                ens = session.query(db.Enrollment).filter_by(learner_id=u.id).all()
                for e in ens:
                    c = session.get(db.Course, e.course_id)
                    if c:
                        who = session.get(db.User, c.mentor_id)
                        break
        msg = ("Sure - message your instructor directly"
               if who else "Sure - our admin team reads every request. ")
        actions = []
        if who:
            actions.append(_link("Message %s" % who.name, "/chat?to=%d" % who.id))
        actions.append(_link("Open chat", "/chat"))
        return {"reply": msg + "Include your course name and what went wrong so we "
                               "can fix it fast.", "actions": actions, "chips": []}

    # --- platform numbers
    if any(k in low for k in ("numbers", "stats", "how many", "analytics")):
        free, paid = _free_paid(session)
        return {"reply": "SkillHub right now: %d learners, %d mentors, %d published "
                         "courses (%d free), %d enrolments."
                         % (session.query(db.User).filter_by(role="learner").count(),
                            session.query(db.User).filter_by(role="mentor").count(),
                            free + paid, free,
                            session.query(db.Enrollment).count()),
                "actions": [_link("Admin analytics", "/dashboard")]
                       if u and u.role == "admin" else [], "chips": []}

    # --- course discovery
    if any(k in low for k in ("course", "class", "learn", "skill", "tutorial",
                              "training", "find", "free")):
        hits, keys = _find_courses(session, text)
        free, paid = _free_paid(session)
        if hits:
            lines = []
            for c in hits:
                m = session.get(db.User, c.mentor_id)
                price = "free" if c.price <= 0 else "%s%s" % (TAKA, c.price)
                lines.append("%s by %s - %s, %s, %d lessons"
                             % (c.title, m.name if m else "SkillHub", price,
                                c.language, len(c.lessons)))
            acts = [_link("Open " + hits[0].title, "/course/%d" % hits[0].id),
                    _link("See all results", "/browse?q=" + (keys[0] if keys else ""))]
            return {"reply": "Found %d match(es): %s. The catalogue has %d free and "
                             "%d paid courses." % (len(hits), " / ".join(lines),
                                                   free, paid),
                    "actions": acts, "chips": ["Match me with a mentor"]}
        return {"reply": "I could not match that to a course name. The catalogue has "
                         "%d free and %d paid courses - browse them and filter by "
                         "category, language or price." % (free, paid),
                "actions": [_link("Browse courses", "/browse"),
                            _link("SkillHub Match", "/match")],
                "chips": ["Find a free course", "Talk to a human"]}

    # --- greeting / fallback
    if re.fullmatch(r"(hi|hello|hey|salam|assalamu alaikum|yo|good (morning|evening|afternoon))[\s!.]*",
                    low):
        return {"reply": "Hello%s! What do you want to learn or fix today?"
                % (" " + u.name if u else ""), "actions": [],
                "chips": ["Find a free course", "Match me with a mentor",
                          "Talk to a human"]}
    return {"reply": "I can help with: finding courses, choosing a mentor, "
                     "enrolment and payment, your progress and certificates, "
                     "quizzes/assignments, course approval, and account access. "
                     "Want me to pass you to a human?",
            "actions": [_link("Browse courses", "/browse"),
                        _link("SkillHub Match", "/match"),
                        _link("Talk to a human", "/chat")],
            "chips": ["Find a free course", "Match me with a mentor",
                      "Talk to a human"]}