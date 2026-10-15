import io, ast
P="app/routers/bot.py"
src=io.open(P,encoding="utf-8").read().replace("\r\n","\n")
def rep(old,new,tag):
    global src
    assert src.count(old)==1,"MARKER FAIL "+tag
    src=src.replace(old,new)
rep('''import json
import re
from fastapi import APIRouter, Depends, Header''','''import re
from fastapi import APIRouter, Depends, Header''',"import")
rep('''                lines.append("%s by %s - %s (\\\\u%04x%s) %s, %s lessons"
                             % (c.title, m.name if m else "SkillHub",
                                "free" if c.price <= 0 else "%s%s" % (TAKA, c.price),
                                0x9f3, "", c.language, len(c.lessons)))''',
'''                price = "free" if c.price <= 0 else "%s%s" % (TAKA, c.price)
                lines.append("%s by %s - %s, %s, %d lessons"
                             % (c.title, m.name if m else "SkillHub", price,
                                c.language, len(c.lessons)))''',"price-line")
rep('''            "chips": starters()["chips"][u.role if u else "guest"]}''',
'''            "chips": ["Find a free course", "Match me with a mentor",
                      "Talk to a human"]}''',"chips")
ast.parse(src); io.open(P,"w",encoding="utf-8",newline="\n").write(src)
print("bot cleaned", len(src))