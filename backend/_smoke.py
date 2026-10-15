import json, sys
import httpx
B = "http://127.0.0.1:8030"
fails = []
def ck(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  -> " + str(extra)[:220]))
    if not cond:
        fails.append(name)

def login(email, pw):
    r = c.post("/auth/login", json={"email": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"],
            "Content-Type": "application/json"}

c = httpx.Client(base_url=B, timeout=20)
mentor = login("rifat@skillhub.dev", "Mentor123")
admin = login("admin@skillhub.dev", "Admin123")
learner = login("learner@skillhub.dev", "Learner123")

# 1. mentor creates a course exactly like the browser does (JSON body)
r = c.post("/courses", headers=mentor, data=json.dumps({
    "title": "Smoke Course Auto", "description": "created by smoke script",
    "category": "Tech", "language": "en", "price": 0, "duration_hours": 3,
    "level": "Beginner", "tags": "smoke"}))
ck("mentor create course 200", r.status_code == 200, r.text)
cid = r.json().get("id") if r.status_code == 200 else 0
ck("create returns id + status pending", bool(cid) and r.json().get("status") == "pending", r.text)

# 2. admin notified + pending queue
n = c.get("/notifications", headers=admin).json()
ck("admin bell has course-review notification",
   any("awaiting review" in x["message"] for x in n["notifications"]), n)
p = c.get("/admin/courses/pending", headers=admin).json()
ck("pending queue lists new course", any(x["id"] == cid for x in p["courses"]), p)

# 3. admin approves with a note -> mentor notified with the note
r = c.put("/admin/courses/%d/status" % cid, headers=admin,
          data=json.dumps({"status": "published", "note": "Nice structure, approved."}))
ck("admin approve 200", r.status_code == 200, r.text)
mn = c.get("/notifications", headers=mentor).json()
ck("mentor notified with reviewer note",
   any("Nice structure" in x["message"] for x in mn["notifications"]), mn)

# 4. mentor workspace APIs
o = c.get("/mentor/overview", headers=mentor).json()
ck("mentor overview keys", all(k in o for k in ("courses", "students", "revenue", "ungraded", "reviews_unanswered")), o)
ck("mentor overview counts something", o["courses"] >= 2, o)
st = c.get("/courses/1/students", headers=mentor)
ck("mentor roster 200", st.status_code == 200, st.text)
qr = c.get("/quizzes/1/results", headers=mentor)
ck("mentor quiz results 200", qr.status_code == 200, qr.text)
bad = c.get("/courses/3/students", headers=mentor)  # not his course
ck("foreign course roster blocked", bad.status_code == 404, bad.status_code)

# lesson edit + reorder on the new course
r = c.post("/courses/%d/lessons" % cid, headers=dict(mentor, **{}), data=json.dumps({}),
           files=None, content=None) if False else None
lform = {"title": "Smoke Lesson", "description": "d", "content": "notes here", "video_url": ""}
r = c.post("/courses/%d/lessons" % cid, headers={"Authorization": mentor["Authorization"],
           "Content-Type": "application/x-www-form-urlencoded"}, data=lform)
ck("lesson add (form) 200", r.status_code == 200, r.text)
lid = r.json().get("lesson_id") if r.status_code == 200 else 0
r = c.put("/lessons/%s" % lid, headers={"Authorization": mentor["Authorization"],
            "Content-Type": "application/x-www-form-urlencoded"},
            data={"title": "Smoke Lesson Renamed", "content": "updated notes"})
ck("lesson edit 200", r.status_code == 200, r.text)
r = c.post("/courses/%d/lessons" % cid, headers={"Authorization": mentor["Authorization"],
            "Content-Type": "application/x-www-form-urlencoded"},
            data={"title": "Second lesson"})
lid2 = r.json().get("lesson_id")
r = c.put("/lessons/%s/move" % lid2, headers=mentor, params={"direction": "up"})
ck("lesson reorder 200", r.status_code == 200, r.text)

# grading: learner submits, mentor grades
r = c.post("/assignments/1/submit", headers={"Authorization": learner["Authorization"],
            "Content-Type": "application/x-www-form-urlencoded"},
            data={"comment": "my work", "draft": "False"})
ck("learner assignment submit 200", r.status_code == 200, r.text)
subs = c.get("/assignments/1/submissions", headers=mentor).json()
ck("mentor sees submissions list", "submissions" in subs, subs)
# review reply
rv = c.get("/courses/1/reviews").json()["reviews"]
rid = rv[0]["id"]
r = c.post("/reviews/%d/reply" % rid, headers=mentor, data=json.dumps({"reply": "Thanks!"}))
ck("review reply (owner) works or 404-if-not-owner", r.status_code in (200, 404), r.text)
# mentor profile save
r = c.put("/mentor/profile", headers=mentor, data=json.dumps({
    "headline": "Excel automation consultant", "about": "I teach by building.",
    "country": "Bangladesh", "skills": [{"name": "Microsoft Excel", "proficiency": 5, "years": 9}],
    "langs": [{"code": "bn", "fluency": "native"}, {"code": "en", "fluency": "fluent"}]}))
ck("mentor profile save 200", r.status_code == 200, r.text)

# 5. learner APIs
o = c.get("/learner/overview", headers=learner).json()
ck("learner overview keys", all(k in o for k in ("courses", "hours_learned", "certificates", "wishlist")), o)
ck("learner results 200", c.get("/my/results", headers=learner).status_code == 200)
ck("learner certificates 200", c.get("/my/certificates", headers=learner).status_code == 200)
r = c.put("/lessons/1/note", headers=learner, data=json.dumps({"text": "my study note"}))
ck("lesson note save 200", r.status_code == 200, r.text)
lk = c.get("/courses/1/learn", headers=learner).json()
ck("learn payload carries note + rich fields",
   lk["lessons"][0].get("note") == "my study note" and "attempts_left" in str(lk["quizzes"]),
   lk["lessons"][0])
r = c.put("/my/goals", headers=learner, data=json.dumps({"goals": ["Data Science", "Excel"]}))
ck("goals save 200", r.status_code == 200 and r.json()["goals"], r.text)
ck("my/notes 200", c.get("/my/notes", headers=learner).status_code == 200)
r = c.delete("/wishlist/2", headers=learner)
ck("wishlist DELETE works", r.status_code == 200 and r.json()["saved"] is False, r.text)

# 6. admin APIs
ac = c.get("/admin/courses?q=Smoke", headers=admin).json()
ck("admin course search 200", any(x["title"] == "Smoke Course Auto" for x in ac["courses"]), ac)
ck("admin course rows carry students+revenue", all(k in ac["courses"][0] for k in ("students", "revenue")), ac)
r = c.post("/admin/broadcast", headers=admin, data=json.dumps({"message": "Maintenance window Sunday 2am.", "role": "learner"}))
ck("admin broadcast 200", r.status_code == 200 and r.json()["sent"] >= 1, r.text)
ln = c.get("/notifications", headers=learner).json()
ck("learner received announcement", any("Maintenance window" in x["message"] for x in ln["notifications"]), ln)
r = c.post("/admin/categories", headers=admin, data=json.dumps({"name": "QA Cat " + str(int(__import__("time").time())), "icon": "\u2708"}))
ck("category add 200", r.status_code == 200, r.text)
cats = c.get("/meta").json()
ck("meta exposes categories+levels", "categories" in cats and "levels" in cats, list(cats))
tx = c.get("/txns/admin", headers=admin).json()["transactions"]
ok_tx = [t for t in tx if t["status"] == "success"]
r = c.post("/admin/txns/%d/refund" % ok_tx[0]["id"], headers=admin)
ck("refund 200", r.status_code == 200, r.text)
ck("refund twice rejected", c.post("/admin/txns/%d/refund" % ok_tx[0]["id"], headers=admin).status_code == 400)
an = c.get("/admin/analytics", headers=admin).json()
ck("analytics has monthly+top_mentors+completion_rate",
   all(k in an for k in ("monthly", "top_mentors", "completion_rate", "categories")), list(an))
ck("export users csv", c.get("/admin/export/users", headers=admin).text.startswith("id,name"))
ck("export courses csv", c.get("/admin/export/courses", headers=admin).text.startswith("id,title"))
ck("admin enrollments list", c.get("/admin/enrollments", headers=admin).status_code == 200)
ck("admin reviews list", c.get("/admin/reviews", headers=admin).status_code == 200)
mp = c.get("/mentors/2", headers=admin).json()
ck("public mentor page has verified/about/students", all(k in mp for k in ("verified", "about", "students")), list(mp))
r = c.put("/admin/mentors/2/verify", headers=admin, data=json.dumps({"verified": True}))
ck("mentor verify 200", r.status_code == 200 and r.json()["verified"], r.text)
LID = [x["id"] for x in c.get("/admin/users", headers=admin).json()["users"]
         if x["email"] == "ayesha@skillhub.dev"][0]
r = c.put("/admin/users/%d/status" % LID, headers=admin, data=json.dumps({"status": "blocked"}))
ck("block user 200", r.status_code == 200, r.text)
ck("blocked user cannot log in", c.post("/auth/login",
   json={"email": "ayesha@skillhub.dev", "password": "Learner123"}).status_code == 403)
ck("unblock user 200", c.put("/admin/users/%d/status" % LID, headers=admin,
   data=json.dumps({"status": "active"})).status_code == 200)
ck("role change 200", c.put("/admin/users/%d/role" % LID, headers=admin,
   data=json.dumps({"role": "mentor"})).status_code == 200)
c.put("/admin/users/%d/role" % LID, headers=admin, data=json.dumps({"role": "learner"}))
ck("csv guard for bad export", c.get("/admin/export/nope", headers=admin).status_code == 400)

# 7. chatbot
sk = c.get("/bot/starters").json()
ck("bot starters for guest", sk["role"] == "guest" and len(sk["chips"]) >= 3, sk)
sl = c.get("/bot/starters", headers=learner).json()
ck("bot starters personalised", sl["role"] == "learner", sl)
qs = [("find excel courses", "match"), ("how do I pay for a course", "OTP"),
      ("what is my progress", "course"), ("when do I get a certificate", "certificate"),
      ("match me with a mentor for python", "match"), ("my course was rejected", "review"),
      ("I forgot my password", "forgot" ), ("talk to a human", "chat"),
      ("how many learners do you have", "learners")]
for q, expect in qs:
    r = c.post("/bot/ask", headers=learner, data=json.dumps({"message": q}))
    d = r.json() if r.status_code == 200 else {}
    ck("bot answers: " + q, r.status_code == 200 and expect.lower() in json.dumps(d).lower(), d)
r = c.post("/bot/ask", headers=admin, data=json.dumps({"message": "what is pending review"}))
ck("bot admin pending", "review" in json.dumps(r.json()).lower(), r.json())

print()
print("TOTAL FAILURES:", len(fails))
sys.exit(1 if fails else 0)