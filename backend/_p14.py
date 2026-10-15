import io, ast

def rw(path, fn):
    src = io.open(path, encoding="utf-8-sig").read()
    out = fn(src)
    ast.parse(out)
    io.open(path, "w", encoding="utf-8", newline="\n").write(out)
    print("patched", path)

def fix_bot(src):
    i = src.index("    # --- course discovery")
    j = src.index("    # --- platform numbers")
    k = src.index("    # --- greeting / fallback")
    assert i < j < k
    return src[:i] + src[j:k] + src[i:j] + src[k:]

rw(r"d:\skillhub\backend\app\routers\bot.py", fix_bot)

def fix_smoke(src):
    old = 'r = c.put("/admin/users/4/status", headers=admin, data=json.dumps({"status": "blocked"}))'
    assert src.count(old) == 1
    new = ('LID = [x["id"] for x in c.get("/admin/users", headers=admin).json()["users"]\n'
           '         if x["email"] == "ayesha@skillhub.dev"][0]\n'
           'r = c.put("/admin/users/%d/status" % LID, headers=admin, data=json.dumps({"status": "blocked"}))')
    src = src.replace(old, new)
    src = src.replace('c.put("/admin/users/4/status", headers=admin, data=json.dumps({"status": "active"}))',
                      'c.put("/admin/users/%d/status" % LID, headers=admin, data=json.dumps({"status": "active"}))')
    src = src.replace('c.put("/admin/users/4/role", headers=admin, data=json.dumps({"role": "mentor"}))',
                      'c.put("/admin/users/%d/role" % LID, headers=admin, data=json.dumps({"role": "mentor"}))')
    src = src.replace('c.put("/admin/users/4/role", headers=admin,\n                       data=json.dumps({"role": "learner"}))',
                      'c.put("/admin/users/%d/role" % LID, headers=admin,\n                       data=json.dumps({"role": "learner"}))')
    assert "/admin/users/4/" not in src, "leftover hardcoded id"
    return src

rw(r"d:\skillhub\backend\_smoke.py", fix_smoke)