import io, ast
P = "app/db.py"
src = io.open(P, encoding="utf-8").read().replace("\r\n", "\n")

def rep(old, new):
    global src
    assert src.count(old) == 1, ("BAD MARKER: " + old[:60])
    src = src.replace(old, new)

# --- User: goals + notification prefs
rep('''    status = Column(String, default="active")      # active | blocked''',
    '''    goals = Column(String, default="[]")           # JSON skill names to learn
    notify_email = Column(Boolean, default=True)
    status = Column(String, default="active")      # active | blocked''')

# --- Course: richer catalogue + admin review note + featured
rep('''    status = Column(String, default="pending")     # pending|published|rejected
    rating = Column(Float, default=4.5)
    reviews = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.utcnow)''',
    '''    level = Column(String, default="Beginner")     # Beginner|Intermediate|Advanced
    tags = Column(String, default="")              # comma separated keywords
    thumbnail = Column(String, nullable=True)      # stored upload name
    status = Column(String, default="pending")     # pending|published|rejected|unpublished
    review_note = Column(Text, default="")         # admin feedback on approve/reject
    featured = Column(Boolean, default=False)
    rating = Column(Float, default=4.5)
    reviews = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow)''')

# --- Review: mentor reply
rep('''    comment = Column(Text, default="")
    created = Column(DateTime, default=datetime.utcnow)''',
    '''    comment = Column(Text, default="")
    reply = Column(Text, default="")               # mentor response
    created = Column(DateTime, default=datetime.utcnow)''')

# --- Assignment submission: mentor grade
rep('''    comment = Column(Text, default="")
    draft = Column(Boolean, default=True)
    submitted = Column(DateTime, default=datetime.utcnow)''',
    '''    comment = Column(Text, default="")
    draft = Column(Boolean, default=True)
    grade = Column(Float, nullable=True)           # marks awarded
    feedback = Column(Text, default="")
    submitted = Column(DateTime, default=datetime.utcnow)''')

# --- MentorProfile: verification + bio
rep('''    headline = Column(String, default="")
    country = Column(String, default="Bangladesh")''',
    '''    headline = Column(String, default="")
    about = Column(Text, default="")
    verified = Column(Boolean, default=False)
    country = Column(String, default="Bangladesh")''')

# --- Notification kind
rep('''    message = Column(String, default="")
    link = Column(String, default="")''',
    '''    message = Column(String, default="")
    kind = Column(String, default="info")          # info|course|payment|chat|grade|system
    link = Column(String, default="")''')

rep('''def notify(session, user_id, message, link=""):
    """Persist an in-app notification for a user (never raises)."""
    if not user_id:
        return
    session.add(Notification(user_id=user_id, message=message, link=link))
    session.commit()''',
    '''def notify(session, user_id, message, link="", kind="info"):
    """Persist an in-app notification for one user (never raises)."""
    if not user_id:
        return
    session.add(Notification(user_id=user_id, message=message, link=link, kind=kind))
    session.commit()


def notify_role(session, role, message, link="", kind="system", exclude=None):
    """Broadcast a notification to every active user of a role."""
    q = session.query(User).filter_by(status="active")
    if role:
        q = q.filter_by(role=role)
    ids = [x.id for x in q.all() if x.id != exclude]
    for i in ids:
        session.add(Notification(user_id=i, message=message, link=link, kind=kind))
    session.commit()
    return len(ids)''')

# --- new tables: lesson notes + categories
rep('''class Otp(Base):''',
    '''class LessonNote(Base):
    __tablename__ = "lesson_notes"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, default="")
    updated = Column(DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = "categories"
    name = Column(String, primary_key=True)
    icon = Column(String, default="📚")


class Otp(Base):''')

ast.parse(src)
io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("db.py patched ok", len(src))