import io, ast
p = r"d:\skillhub\backend\_smoke.py"
lines = io.open(p, encoding="utf-8-sig").read().split("\n")
start = next(i for i, l in enumerate(lines) if '"/admin/users/4/status"' in l)
end = next(i for i, l in enumerate(lines) if '"/admin/users/4/role"' in l and "ck(" not in l)
print("replacing lines", start + 1, "to", end + 1)
block = [
 'LID = [x["id"] for x in c.get("/admin/users", headers=admin).json()["users"]',
 '         if x["email"] == "ayesha@skillhub.dev"][0]',
 'r = c.put("/admin/users/%%d/status" %% LID, headers=admin, data=json.dumps({"status": "blocked"}))',
 'ck("block user 200", r.status_code == 200, r.text)',
 'ck("blocked user cannot log in", c.post("/auth/login",',
 '   json={"email": "ayesha@skillhub.dev", "password": "Learner123"}).status_code == 403)',
 'ck("unblock user 200", c.put("/admin/users/%%d/status" %% LID, headers=admin,',
 '   data=json.dumps({"status": "active"})).status_code == 200)',
 'ck("role change 200", c.put("/admin/users/%%d/role" %% LID, headers=admin,',
 '   data=json.dumps({"role": "mentor"})).status_code == 200)',
 'c.put("/admin/users/%%d/role" %% LID, headers=admin, data=json.dumps({"role": "learner"}))',
]
block = [b.replace("%%", "%") for b in block]
lines[start:end + 1] = block
src = "\n".join(lines)
assert "/admin/users/4/" not in src
ast.parse(src)
io.open(p, "w", encoding="utf-8", newline="\n").write(src)
print("ok")