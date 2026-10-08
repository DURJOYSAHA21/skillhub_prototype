"""End-to-end API tests mapped to SRS acceptance criteria."""
import random
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app
from app import db

db.init_db()
C = TestClient(app)


def tok(email, password):
    r = C.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


def newsignup(role="learner"):
    email = f"t{random.randint(10**5, 10**7)}@test.dev"
    phone = "017" + str(random.randint(10**7, 10**8 - 1))
    body = {"name": "Test User", "email": email, "phone": phone,
            "password": "Secret123", "confirm_password": "Secret123",
            "role": role}
    r = C.post("/auth/signup", json=body)
    assert r.status_code == 200, r.text
    otp = r.json()["dev_otp"]
    v = C.post("/auth/verify", json={"email": email, "otp": otp})
    assert v.status_code == 200, v.text
    return email, {"Authorization": "Bearer " + v.json()["token"]}


def test_login_bad_password_and_lockout():
    email = f"lock{random.randint(10**5, 10**7)}@test.dev"
    C.post("/auth/signup", json={"name": "Lock Test", "email": email,
            "phone": "017" + str(random.randint(10**7, 10**8 - 1)), "password": "Secret123",
            "confirm_password": "Secret123", "role": "learner"})
    for _ in range(5):
        C.post("/auth/login", json={"email": email, "password": "WrongPass1"})
    r = C.post("/auth/login", json={"email": email, "password": "Secret123"})
    assert r.status_code == 403 and "Too many failed" in r.text


def test_signup_validation_rules():
    base = {"name": "V", "email": f"v{random.randint(10**5,10**7)}@t.dev",
            "phone": "01700000000", "password": "Secret123",
            "confirm_password": "Secret123", "role": "learner"}
    assert C.post("/auth/signup", json={**base, "password": "short1A",
                    "confirm_password": "short1A"}).status_code == 400
    assert C.post("/auth/signup", json={**base, "phone": "12345"}).status_code == 400
    assert C.post("/auth/signup", json={**base, "confirm_password": "Other123"}
                  ).status_code == 400


def test_free_enroll_and_duplicate():
    _, h = newsignup()
    r = C.post("/enroll/free", json={"course_id": 1}, headers=h)
    assert r.status_code == 200, r.text
    r2 = C.post("/enroll/free", json={"course_id": 1}, headers=h)
    assert r2.status_code == 400 and "Already" in r2.text
    assert any(c["course_id"] == 1 for c in C.get("/my/courses", headers=h).json()["courses"])


def test_paid_flow_receipt_pdf():
    _, h = newsignup()
    bad = C.post("/pay/start", json={"course_id": 2, "method": "UCB",
                "card_number": "12", "pin": "1234"}, headers=h)
    assert bad.status_code == 400
    st = C.post("/pay/start", json={"course_id": 2, "method": "UCB",
               "card_number": "4111111111111234", "pin": "1234"}, headers=h)
    assert st.status_code == 200
    conf = C.post("/pay/confirm", json={"course_id": 2, "otp": st.json()["dev_otp"],
                   "method": "UCB", "card_number": "4111111111111234"}, headers=h)
    assert conf.status_code == 200, conf.text
    txn_id = conf.json()["txn_id"]
    tx = C.get("/txns/me", headers=h).json()["transactions"]
    assert tx and tx[0]["status"] == "success"
    pdf = C.get(f"/txns/{txn_id}/receipt", headers=h)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"


def test_quiz_pass_and_progress():
    _, h = newsignup()
    C.post("/enroll/free", json={"course_id": 1}, headers=h)
    learn = C.get("/courses/1/learn", headers=h).json()
    qid = learn["quizzes"][0]["id"]
    quiz = C.get(f"/quizzes/{qid}", headers=h).json()
    keys = [0, 1, 2, 1, 1]
    answers = {str(q["id"]): keys[i] for i, q in enumerate(quiz["questions"])}
    sub = C.post(f"/quizzes/{qid}/submit", json={"answers": answers}, headers=h)
    assert sub.status_code == 200
    assert sub.json()["passed"] and sub.json()["score_percent"] == 100.0
    cert_no = C.get("/courses/1/certificate", headers=h)
    assert cert_no.status_code == 400  # lessons not finished yet


def test_mentor_create_course_admin_approve():
    email, _ = newsignup("mentor")
    h = tok(email, "Secret123")
    cr = C.post("/courses", json={"title": "Test Course ABC", "language": "en",
                                  "price": 500}, headers=h)
    assert cr.status_code == 200 and cr.json()["course"]["status"] == "pending"
    cid = cr.json()["course"]["id"]
    ah = tok("admin@skillhub.dev", "Admin123")
    assert cid in [x["id"] for x in C.get("/admin/courses/pending", headers=ah).json()["courses"]]
    assert C.put(f"/admin/courses/{cid}/status", json={"status": "published"},
                 headers=ah).status_code == 200
    assert any(x["id"] == cid for x in C.get("/courses").json()["courses"])


def test_chat_roundtrip():
    _, h1 = newsignup()
    lid = C.get("/auth/me", headers=h1).json()["id"]
    mh = tok("rifat@skillhub.dev", "Mentor123")
    send = C.post("/chat/2", data={"text": "Hello mentor"}, headers=h1)
    assert send.status_code == 200
    C.post(f"/chat/{lid}", data={"text": "Hi! Class at 8"}, headers=mh)
    conv = C.get("/chat/2", headers=h1).json()["messages"]
    assert len(conv) >= 2 and conv[-1]["text"] == "Hi! Class at 8"
    assert any(t["user_id"] == 2 for t in C.get("/chat/threads", headers=h1).json()["threads"])


def test_profile_language_toggle():
    email, h = newsignup()
    r = C.put("/auth/profile", json={"lang": "bn"}, headers=h)
    assert r.status_code == 200
    assert C.get("/auth/me", headers=h).json()["lang"] == "bn"


def test_admin_analytics_and_block():
    ah = tok("admin@skillhub.dev", "Admin123")
    an = C.get("/admin/analytics", headers=ah).json()
    assert an["revenue"] >= 1500 and an["users"]["learner"] >= 3
    email, _ = newsignup()
    uid = C.get(f"/admin/users", headers=ah).json()
    tid = [x["id"] for x in uid["users"] if x["email"] == email][0]
    C.put(f"/admin/users/{tid}/status", json={"status": "blocked"}, headers=ah)
    blocked = C.post("/auth/login", json={"email": email, "password": "Secret123"})
    assert blocked.status_code == 403 and "blocked" in blocked.text.lower()


def test_match_engine_endpoint():
    m = C.get("/match?skill=vlookup&langs=bn,en").json()
    assert m["resolved_skill"] == "Microsoft Excel"
    assert m["results"][0]["name"] == "Rifat Hasan"
