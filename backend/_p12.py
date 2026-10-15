import io, ast
P="app/db.py"
src=io.open(P,encoding="utf-8-sig").read().replace("\r\n","\n")
def rep(old,new,tag):
    global src
    assert src.count(old)==1, "MARKER FAIL "+tag
    src=src.replace(old,new)

rep('''MENTORS = [''', '''CATEGORIES = [("Tech", "\\U0001F4BB"), ("Office", "\\U0001F4CA"), ("Design", "\\U0001F3A8"),
              ("Media", "\\U0001F3AC"), ("Business", "\\U0001F4BC"), ("Language", "\\U0001F5E4"),
              ("Music", "\\U0001F3B8"), ("Engineering", "\\u2699"), ("Soft Skills", "\\U0001F91D"),
              ("Lifestyle", "\\U0001F373")]

MENTORS = [''', "cats-list")

rep('''def _seed(session):
    for c, n in LANGS:
        session.add(Language(code=c, name=n))''',
'''def _seed(session):
    for c, n in LANGS:
        session.add(Language(code=c, name=n))
    for nm, ic in CATEGORIES:
        session.add(Category(name=nm, icon=ic))''', "seed-cats")

rep('''        session.add(MentorProfile(user_id=u.id, headline=hl, country=country,
                                  rating=rt, reviews=rv, avg_reply_hours=2.0 + i,
                                  completion=78.0 + i))''',
'''        session.add(MentorProfile(user_id=u.id, headline=hl, country=country,
                                  about="%s. I teach step by step with real "
                                        "projects and answer questions in chat "
                                        "within a day." % hl,
                                  verified=(i < 3),
                                  rating=rt, reviews=rv, avg_reply_hours=2.0 + i,
                                  completion=78.0 + i))''', "seed-verified")

rep('''        u = User(name=nm, email=em, phone="018%08d" % (200 + j),
                 password_hash=hash_password("Learner123"), role="learner",
                 lang="bn" if j < 2 else "en")''',
'''        u = User(name=nm, email=em, phone="018%08d" % (200 + j),
                 password_hash=hash_password("Learner123"), role="learner",
                 goals=json.dumps([["Microsoft Excel", "Data Science"],
                                   ["UI/UX Design"], ["Python Programming"]][j]),
                 lang="bn" if j < 2 else "en")''', "seed-goals")

rep('''    session.add(Wishlist(user_id=learners[0].id, course_id=courses[1].id))''',
'''    demo = Course(mentor_id=mentors[3].id, title="Design Systems in Figma (Pro)",
                  description="Awaiting review: components, tokens and handoff.",
                  category="Design", language="en", price=2200, type="paid",
                  level="Intermediate", duration_hours=9, status="pending",
                  tags="figma, ui, design system")
    session.add(demo)
    session.flush()
    for pos, lt in enumerate(LESSON_TITLES[:3], start=1):
        session.add(Lesson(course_id=demo.id, title="Lesson %d: %s" % (pos, lt),
                           position=pos, content=LESSON_NOTES.format(t=lt,
                           title=demo.title)))
    session.add(Review(course_id=courses[0].id, user_id=learners[1].id, rating=5,
                       comment="The dashboards module alone paid for itself.",
                       reply="Thank you Karim! Try the automation lesson next."))
    a0 = courses[0].assignments[0]
    session.add(AssignSubmit(assignment_id=a0.id, learner_id=learners[0].id,
                             comment="Submitted my sales dashboard workbook.",
                             draft=False, grade=88.0,
                             feedback="Great pivot work - tighten the chart labels."))
    session.add(LessonNote(lesson_id=courses[0].lessons[0].id,
                           user_id=learners[0].id,
                           text="Remember: absolute refs use $ before row and column."))
    session.add(Wishlist(user_id=learners[0].id, course_id=courses[1].id))''', "seed-extras")

ast.parse(src)
io.open(P,"w",encoding="utf-8",newline="\n").write(src)
print("seed patched", len(src))