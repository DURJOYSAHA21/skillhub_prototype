"""Product-layer tests: quiz builder, reviews, wishlist, notifications, lesson content."""
import random
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
    email = "p%d@test.dev" % random.randint(10**5, 10**7)
    phone = "017%d" % random.randint(10**7, 10**8 - 1)
    r = C.post("/auth/signup", json={"name": "Product User", "email": email,
                                     "phone": phone, "password": "Secret123",
                                     "confirm_password": "Secret123", "role": role})
    assert r.status_code == 200, r.text
    v = C.post("/auth/verify", json={"email": email, "otp": r.json()["dev_otp"]})
    assert v.status_code == 200, v.text
    return email, {"Authorization": "Bearer " + v.json()["token"]}


def fresh_course():
    """Published free course owned by a new mentor, with one enrolled learner."""
    _, mh = newsignup("mentor")
    cr = C.post("/courses", json={"title": "Product Course %d" % random.randint(100, 9999),
                                  "language": "en", "price": 0, "category": "Tech",
                                  "duration_hours": 3}, headers=mh)
    assert cr.status_code == 200, cr.text
    cid = cr.json()["course"]["id"]
    ah = tok("admin@skillhub.dev", "Admin123")
    assert C.put("/admin/courses/%d/status" % cid, json={"status": "published"},
                 headers=ah).status_code == 200
    _, lh = newsignup("learner")
    assert C.post("/enroll/free", json={"course_id": cid}, headers=lh).status_code == 200
    return cid, mh, lh, ah


def test_lesson_content_and_video_roundtrip():
    cid, mh, lh, _ = fresh_course()
    up = C.post("/courses/%d/lessons" % cid, headers=mh,
                data={"title": "Lesson One", "description": "short",
                      "content": "Step by step notes for the lesson.",
                      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert up.status_code == 200, up.text
    assert C.post("/courses/%d/lessons" % cid, headers=mh,
                  data={"description": "no title"}).status_code == 400
    learn = C.get("/courses/%d/learn" % cid, headers=lh).json()
    les = learn["lessons"][0]
    assert les["content"].startswith("Step by step")
    assert "dQw4w9WgXcQ" in les["video_url"]
    mine = [c for c in C.get("/courses?mine=mentor", headers=mh).json()["courses"]
            if c["id"] == cid][0]
    assert mine["lessons"][0]["notes"] is True


def test_quiz_builder_and_validation():
    cid, mh, lh, _ = fresh_course()
    body = {"title": "Check basics", "time_limit_min": 10, "passing_score": 50,
            "max_attempts": 2,
            "questions": [{"text": "1+1?", "options": ["2", "3", "4", "5"], "correct": 0},
                          {"text": "Sky?", "options": ["blue", "wet", "hot", "old"], "correct": 0}]}
    r = C.post("/courses/%d/quizzes" % cid, json=body, headers=mh)
    assert r.status_code == 200, r.text
    assert r.json()["questions"] == 2
    assert C.post("/courses/%d/quizzes" % cid, headers=mh,
                  json={**body, "questions": [{"text": "bad", "options": ["a", "b"], "correct": 0}]}
                  ).status_code == 400
    assert C.post("/courses/%d/quizzes" % cid, headers=mh,
                  json={**body, "questions": [{"text": "bad", "options": ["a", "b", "c", "d"], "correct": 9}]}
                  ).status_code == 400
    other_m = newsignup("mentor")[1]
    assert C.post("/courses/%d/quizzes" % cid, json=body, headers=other_m).status_code == 404
    quizzes = C.get("/courses/%d/learn" % cid, headers=lh).json()["quizzes"]
    assert any(q["id"] == r.json()["quiz_id"] for q in quizzes)
    assert C.put("/quizzes/%d/publish" % r.json()["quiz_id"], headers=mh).status_code == 200


def test_review_upsert_recalculates_rating():
    cid, mh, lh, _ = fresh_course()
    before = C.get("/courses/%d/reviews" % cid).json()["reviews"]
    r1 = C.post("/courses/%d/reviews" % cid, json={"rating": 5, "comment": "Loved it"}, headers=lh)
    assert r1.status_code == 200, r1.text
    assert len(C.get("/courses/%d/reviews" % cid).json()["reviews"]) == len(before) + 1
    r2 = C.post("/courses/%d/reviews" % cid, json={"rating": 3, "comment": "Edited opinion"}, headers=lh)
    assert r2.status_code == 200, r2.text
    rows = C.get("/courses/%d/reviews" % cid).json()["reviews"]
    assert len(rows) == len(before) + 1
    assert rows[0]["rating"] == 3 and rows[0]["comment"] == "Edited opinion"
    assert 1 <= r2.json()["rating"] <= 5
    assert C.post("/courses/%d/reviews" % cid, json={"rating": 9}, headers=lh).status_code == 400
    assert C.post("/courses/%d/reviews" % cid, json={"rating": 4}, headers=mh).status_code == 403
    stranger = newsignup("learner")[1]
    assert C.post("/courses/%d/reviews" % cid, json={"rating": 4}, headers=stranger).status_code == 403


def test_wishlist_toggle():
    cid, _, lh, _ = fresh_course()
    assert C.post("/wishlist/%d" % cid, headers=lh).json()["saved"] is True
    got = C.get("/wishlist", headers=lh).json()["courses"]
    assert [w for w in got if w["course_id"] == cid]
    assert C.post("/wishlist/%d" % cid, headers=lh).json()["saved"] is False
    assert not [w for w in C.get("/wishlist", headers=lh).json()["courses"] if w["course_id"] == cid]
    assert C.post("/wishlist/999999", headers=lh).status_code == 404


def _unread(h):
    return C.get("/notifications", headers=h).json()["unread"]


def test_notifications_emit_and_read():
    _, mh = newsignup("mentor")
    start = _unread(mh)
    cr = C.post("/courses", json={"title": "Notify Me %d" % random.randint(100, 9999),
                                  "language": "en", "price": 0}, headers=mh)
    cid = cr.json()["course"]["id"]
    ah = tok("admin@skillhub.dev", "Admin123")
    C.put("/admin/courses/%d/status" % cid, json={"status": "published"}, headers=ah)
    data = C.get("/notifications", headers=mh).json()
    assert data["unread"] == start + 1
    assert any("approved" in n["message"] and n["link"] == "/dashboard"
               for n in data["notifications"])
    _, lh = newsignup("learner")
    C.post("/enroll/free", json={"course_id": cid}, headers=lh)
    C.post("/courses/%d/reviews" % cid, json={"rating": 5, "comment": "great"}, headers=lh)
    assert any("review" in n["message"].lower() for n in C.get("/notifications", headers=mh).json()["notifications"])
    nid = C.get("/notifications", headers=mh).json()["notifications"][0]["id"]
    assert C.put("/notifications/%d/read" % nid, headers=mh).status_code == 200
    C.put("/notifications/read-all", headers=mh)
    assert _unread(mh) == 0


def test_public_mentor_profile():
    m = C.get("/mentors/2")
    assert m.status_code == 200, m.text
    d = m.json()
    assert d["name"] == "Rifat Hasan" and d["role" if "role" in d else "id"]
    assert isinstance(d["courses"], list) and isinstance(d["skills"], list)
    assert C.get("/mentors/1").status_code == 404