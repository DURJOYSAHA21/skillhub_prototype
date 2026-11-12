"""Regression tests for the security and correctness fixes (one test per bug)."""
import random
from datetime import datetime, timedelta
from sqlalchemy import event
from fastapi.testclient import TestClient
from app.main import app
from app import db

db.init_db()
C = TestClient(app)


# Postgres enforces foreign keys; make SQLite do the same so delete bugs show up here.
@event.listens_for(db.engine, "connect")
def _fk_on(dbapi_conn, _):
    if db.engine.dialect.name == "sqlite":
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


db.engine.dispose()


def login(email, password, ip=None):
    headers = {"X-Forwarded-For": ip} if ip else {}
    return C.post("/auth/login", json={"email": email, "password": password}, headers=headers)


def tok(email, password):
    r = login(email, password)
    assert r.status_code == 200 and "token" in r.json(), r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


def signup(role="learner", verify=True):
    email = "f%d@test.dev" % random.randint(10**6, 10**8)
    r = C.post("/auth/signup", json={"name": "Fix Test", "email": email,
                                     "phone": "018%d" % random.randint(10**7, 10**8 - 1),
                                     "password": "Secret123", "confirm_password": "Secret123",
                                     "role": role})
    assert r.status_code == 200, r.text
    if not verify:
        return email, None
    v = C.post("/auth/verify", json={"email": email, "otp": r.json()["dev_otp"]})
    assert v.status_code == 200, v.text
    return email, {"Authorization": "Bearer " + v.json()["token"]}


def uid_of(h):
    return C.get("/auth/me", headers=h).json()["id"]


def admin():
    return tok("admin@skillhub.dev", "Admin123")


def published_course(price=0, mh=None):
    if mh is None:
        _, mh = signup("mentor")
    cr = C.post("/courses", json={"title": "Fix Course %d" % random.randint(1000, 99999),
                                  "language": "en", "price": price}, headers=mh)
    assert cr.status_code == 200, cr.text
    cid = cr.json()["course"]["id"]
    assert C.put("/admin/courses/%d/status" % cid, json={"status": "published"},
                 headers=admin()).status_code == 200
    return cid, mh


# --- sign-up and login -------------------------------------------------------------

def test_signup_cannot_pick_admin_role():
    r = C.post("/auth/signup", json={"name": "X", "email": "adm%d@test.dev" % random.randint(1, 10**8),
                                     "phone": "019%d" % random.randint(10**7, 10**8 - 1),
                                     "password": "Secret123", "confirm_password": "Secret123",
                                     "role": "admin"})
    assert r.status_code == 400


def test_unverified_account_gets_no_token_until_otp():
    email, _ = signup(verify=False)
    r = login(email, "Secret123")
    assert r.status_code == 200 and r.json().get("verify_required") and "token" not in r.json()
    code = C.post("/auth/resend", json={"email": email}).json()["dev_otp"]
    v = C.post("/auth/verify", json={"email": email, "otp": code})
    assert v.status_code == 200 and v.json()["token"]
    assert "token" in login(email, "Secret123").json()
    assert C.post("/auth/resend", json={"email": email}).status_code == 400


def test_wrong_passwords_lock_only_the_caller_ip():
    email, _ = signup()
    for _ in range(5):
        login(email, "WrongPass1", ip="203.0.113.7")
    assert login(email, "Secret123", ip="203.0.113.7").status_code == 403
    assert "token" in login(email, "Secret123", ip="198.51.100.2").json()
    uid = [u for u in C.get("/admin/users", headers=admin()).json()["users"]
           if u["email"] == email][0]["id"]
    assert C.get("/admin/users/%d" % uid, headers=admin()).json()["locked"] is True
    C.put("/admin/users/%d/unlock" % uid, headers=admin())
    assert "token" in login(email, "Secret123", ip="203.0.113.7").json()


# --- uploads -------------------------------------------------------------------------

def test_uploaded_html_is_never_served_as_a_page():
    _, h = signup()
    bad = C.post("/auth/picture", headers=h,
                 files={"file": ("x.html", b"<script>alert(1)</script>", "text/html")})
    assert bad.status_code == 400
    peer = uid_of(signup()[1])
    sent = C.post("/chat/%d" % peer, headers=h, data={"text": ""},
                  files={"file": ("page.html", b"<script>alert(1)</script>", "text/html")})
    assert sent.status_code == 200, sent.text
    name = C.get("/chat/%d" % peer, headers=h).json()["messages"][-1]["file"]
    f = C.get("/files/" + name)
    assert f.headers["content-type"] == "application/octet-stream"
    assert "attachment" in f.headers["content-disposition"]
    assert f.headers["x-content-type-options"] == "nosniff"
    pic = C.post("/auth/picture", headers=h, files={"file": ("me.png", b"\x89PNG\r\n", "image/png")})
    assert pic.status_code == 200
    assert C.get("/files/" + pic.json()["picture"]).headers["content-type"] == "image/png"


# --- payments ------------------------------------------------------------------------

def test_payment_code_only_unlocks_its_own_course():
    cheap, mh = published_course(price=100)
    dear, _ = published_course(price=900, mh=mh)
    pending = C.post("/courses", json={"title": "Not approved", "language": "en", "price": 50},
                     headers=mh).json()["course"]["id"]
    _, lh = signup()
    card = {"method": "UCB", "card_number": "123456789012", "pin": "1234"}
    otp = C.post("/pay/start", json={"course_id": cheap, **card}, headers=lh).json()["dev_otp"]
    assert C.post("/pay/confirm", json={"course_id": dear, "otp": otp}, headers=lh).status_code == 400
    assert C.post("/pay/confirm", json={"course_id": pending, "otp": otp}, headers=lh).status_code == 404
    otp = C.post("/pay/start", json={"course_id": cheap, **card}, headers=lh).json()["dev_otp"]
    assert C.post("/pay/confirm", json={"course_id": cheap, "otp": otp}, headers=lh).status_code == 200
    assert C.post("/pay/confirm", json={"course_id": cheap, "otp": otp}, headers=lh).status_code == 400
    ok = [t for t in C.get("/txns/me", headers=lh).json()["transactions"] if t["status"] == "success"]
    assert len(ok) == 1 and ok[0]["course_id"] == cheap


def test_admin_transactions_bad_date_is_a_400():
    assert C.get("/txns/admin?date_from=yesterday", headers=admin()).status_code == 400


# --- quizzes -------------------------------------------------------------------------

def quiz_setup(max_attempts=3, minutes=10):
    cid, mh = published_course()
    _, lh = signup()
    assert C.post("/enroll/free", json={"course_id": cid}, headers=lh).status_code == 200
    body = {"title": "Q", "time_limit_min": minutes, "passing_score": 50, "max_attempts": max_attempts,
            "questions": [{"text": "1+1?", "options": ["2", "3", "4", "5"], "correct": 0},
                          {"text": "Sky?", "options": ["red", "blue", "hot", "old"], "correct": 1}]}
    qid = C.post("/courses/%d/quizzes" % cid, json=body, headers=mh).json()["quiz_id"]
    return cid, qid, lh, mh


def take(qid, lh, answers):
    assert C.get("/quizzes/%d" % qid, headers=lh).status_code == 200
    return C.post("/quizzes/%d/submit" % qid, json={"answers": answers}, headers=lh).json()


def test_quiz_hides_answers_until_passed_and_keeps_best_result():
    cid, qid, lh, _ = quiz_setup()
    qs = C.get("/quizzes/%d" % qid, headers=lh).json()["questions"]
    wrong = take(qid, lh, {})
    assert wrong["answers_revealed"] is False and all("correct" not in x for x in wrong["results"])
    right = {str(qs[0]["id"]): 0, str(qs[1]["id"]): 1}
    good = take(qid, lh, right)
    assert good["passed"] and good["answers_revealed"]
    worse = take(qid, lh, {})
    assert worse["passed"] is False and worse["ever_passed"] is True
    row = [q for q in C.get("/courses/%d/learn" % cid, headers=lh).json()["quizzes"] if q["id"] == qid][0]
    assert row["passed"] is True and row["best_score"] == 100.0


def test_quiz_time_limit_is_enforced_on_the_server():
    _, qid, lh, _ = quiz_setup(minutes=1)
    assert C.post("/quizzes/%d/submit" % qid, json={"answers": {}}, headers=lh).status_code == 400
    qs = C.get("/quizzes/%d" % qid, headers=lh).json()["questions"]
    s = db.Session()
    st = s.query(db.QuizStart).filter_by(quiz_id=qid).first()
    st.started = datetime.utcnow() - timedelta(minutes=5)
    s.commit()
    s.close()
    late = C.post("/quizzes/%d/submit" % qid, headers=lh,
                  json={"answers": {str(qs[0]["id"]): 0, str(qs[1]["id"]): 1}}).json()
    assert late["late"] is True and late["score_percent"] == 0


def test_mentor_can_delete_quiz_with_results():
    _, qid, lh, mh = quiz_setup()
    take(qid, lh, {})
    assert C.delete("/quizzes/%d" % qid, headers=mh).status_code == 200


# --- deleting things -----------------------------------------------------------------

def test_course_with_learners_is_taken_offline_not_deleted():
    cid, qid, lh, mh = quiz_setup()
    take(qid, lh, {})
    r = C.delete("/admin/courses/%d" % cid, headers=admin())
    assert r.status_code == 200 and r.json()["status"] == "unpublished"
    assert C.get("/courses/%d/learn" % cid, headers=lh).status_code == 200
    empty = C.post("/courses", json={"title": "Empty", "language": "en"}, headers=mh).json()["course"]["id"]
    C.post("/courses/%d/lessons" % empty, headers=mh, data={"title": "L1"})
    assert C.delete("/courses/%d" % empty, headers=mh).json()["message"] == "Course deleted successfully."


def test_user_with_activity_is_not_deleted_but_a_new_one_is():
    _, lh = signup()
    busy = uid_of(lh)
    C.post("/wishlist/1", headers=lh)
    C.post("/chat/2", headers=lh, data={"text": "hi"})
    r = C.delete("/admin/users/%d" % busy, headers=admin())
    assert r.status_code == 400 and "messages" in r.json()["detail"]
    _, nh = signup("mentor")
    assert C.delete("/admin/users/%d" % uid_of(nh), headers=admin()).status_code == 200


def test_admin_role_cannot_be_changed():
    users = C.get("/admin/users", headers=admin()).json()["users"]
    other = [u for u in users if u["role"] == "admin"][0]["id"]
    assert C.put("/admin/users/%d/role" % other, json={"role": "learner"},
                 headers=admin()).status_code == 400


def test_editing_a_live_course_sends_it_back_for_review():
    cid, mh = published_course()
    body = {"title": "Totally different title", "language": "en", "price": 500}
    r = C.put("/courses/%d" % cid, json=body, headers=mh)
    assert r.json()["status"] == "pending"
    assert cid not in [c["id"] for c in C.get("/courses").json()["courses"]]


# --- chat ----------------------------------------------------------------------------

def test_chat_one_notification_no_self_messages_unknown_peer():
    _, lh = signup()
    _, mh = signup("mentor")
    mid, lid = uid_of(mh), uid_of(lh)
    before = len(C.get("/notifications", headers=mh).json()["notifications"])
    assert C.post("/chat/%d" % mid, headers=lh, data={"text": "Hello"}).status_code == 200
    assert len(C.get("/notifications", headers=mh).json()["notifications"]) == before + 1
    assert C.post("/chat/%d" % lid, headers=lh, data={"text": "me"}).status_code == 400
    assert C.get("/chat/99999999", headers=lh).status_code == 404
