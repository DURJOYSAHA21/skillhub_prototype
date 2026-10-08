"""Skillhub persistence: SQLAlchemy models + engine bridge + seeding."""
import os
from datetime import datetime, timedelta
from sqlalchemy import (create_engine, Column, Integer, String, Float,
                        ForeignKey, DateTime, Text, Boolean)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from .engine import Mentor, SkillRow, LangRow
from .security import hash_password

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get("SKILLHUB_DB") or os.path.join(ROOT, "skillhub.db")
UPLOAD_DIR = os.environ.get("SKILLHUB_UPLOADS") or os.path.join(ROOT, "uploads")
engine = create_engine("sqlite:///" + DB_PATH, echo=False)
Session = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)          # admin | mentor | learner
    lang = Column(String, default="en")            # preferred UI language
    dob = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    status = Column(String, default="active")      # active | blocked
    fail_count = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created = Column(DateTime, default=datetime.utcnow)


class Otp(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    code = Column(String, nullable=False)
    purpose = Column(String, nullable=False)       # signup | reset | payment
    owner_id = Column(Integer, nullable=True)      # for payment OTP binding
    expires = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)


class Language(Base):
    __tablename__ = "languages"
    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)


class SkillAlias(Base):
    __tablename__ = "skill_aliases"
    alias = Column(String, primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)

class MentorProfile(Base):
    __tablename__ = "mentor_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    headline = Column(String, default="")
    country = Column(String, default="Bangladesh")
    rating = Column(Float, default=4.5)
    reviews = Column(Integer, default=0)
    avg_reply_hours = Column(Float, default=6.0)
    completion = Column(Float, default=75.0)


class MentorSkill(Base):
    __tablename__ = "mentor_skills"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    proficiency = Column(Integer, default=3)
    years = Column(Float, default=2.0)


class MentorLanguage(Base):
    __tablename__ = "mentor_languages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String, nullable=False)
    fluency = Column(String, default="fluent")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    category = Column(String, default="Tech")
    language = Column(String, nullable=False)      # course delivery language
    price = Column(Float, default=0.0)             # 0 = free
    type = Column(String, default="free")          # free | paid
    duration_hours = Column(Float, default=4.0)
    status = Column(String, default="pending")     # pending|published|rejected
    rating = Column(Float, default=4.5)
    reviews = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.utcnow)
    lessons = relationship("Lesson", cascade="all, delete-orphan",
                           order_by="Lesson.position")
    quizzes = relationship("Quiz", cascade="all, delete-orphan")
    assignments = relationship("Assignment", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    position = Column(Integer, default=1)
    file = Column(String, nullable=True)           # stored upload path/name

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    time_limit_min = Column(Integer, default=20)
    passing_score = Column(Float, default=60.0)    # percent
    max_attempts = Column(Integer, default=3)
    published = Column(Boolean, default=False)
    questions = relationship("Question", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    text = Column(Text, nullable=False)
    options = Column(String, nullable=False)       # JSON list of 4
    correct = Column(Integer, nullable=False)      # index 0..3
    marks = Column(Float, default=5.0)


class Submission(Base):
    __tablename__ = "quiz_submissions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answers = Column(String, default="{}")         # JSON {qid: idx}
    score = Column(Float, default=0.0)             # percent
    passed = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)
    submitted = Column(DateTime, default=datetime.utcnow)


class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    instructions = Column(Text, default="")
    due = Column(DateTime, nullable=True)
    marks = Column(Float, default=100.0)


class AssignSubmit(Base):
    __tablename__ = "assignment_submissions"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file = Column(String, default="")
    comment = Column(Text, default="")
    draft = Column(Boolean, default=True)
    submitted = Column(DateTime, default=datetime.utcnow)

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    progress = Column(Float, default=0.0)          # percent, lessons+quiz
    done_lessons = Column(String, default="[]")    # JSON list of lesson ids
    passed_quizzes = Column(String, default="[]")  # JSON list of quiz ids
    last_lesson = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    enrolled = Column(DateTime, default=datetime.utcnow)


class ChatMsg(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, default="")
    file = Column(String, default="")
    ts = Column(DateTime, default=datetime.utcnow)


class Txn(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    learner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(String, default="")            # bank name
    card_last4 = Column(String, default="")
    status = Column(String, default="pending")     # success|pending|failed
    ref = Column(String, default="")               # SH-YYYYmmdd-XXXX
    created = Column(DateTime, default=datetime.utcnow)


class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    account = Column(String, default="")
    status = Column(String, default="active")      # active|inactive


def issue_otp(session, email, purpose, minutes=5, owner_id=None):
    from .security import gen_otp
    code = gen_otp()
    session.query(Otp).filter_by(email=email, purpose=purpose,
                                 used=False).update({"used": True})
    session.add(Otp(email=email, code=code, purpose=purpose, owner_id=owner_id,
                    expires=datetime.utcnow() + timedelta(minutes=minutes)))
    session.commit()
    return code


def check_otp(session, email, purpose, code, owner_id=None) -> bool:
    q = session.query(Otp).filter_by(email=email, purpose=purpose, code=code,
                                     used=False)
    if owner_id is not None:
        q = q.filter_by(owner_id=owner_id)
    o = q.first()
    ok = bool(o and o.expires > datetime.utcnow())
    if ok:
        o.used = True
        session.commit()
    return ok

LANGS = [("en", "English"), ("bn", "Bangla"), ("hi", "Hindi"), ("ur", "Urdu"),
         ("ar", "Arabic"), ("es", "Spanish"), ("fr", "French"), ("de", "German"),
         ("pt", "Portuguese"), ("tl", "Tagalog"), ("id", "Indonesian"),
         ("tr", "Turkish"), ("ne", "Nepali"), ("fa", "Farsi")]
SK = [
    (1, "Web Development", "Tech", ["web dev", "frontend", "full stack", "javascript"]),
    (2, "Python Programming", "Tech", ["python", "django", "scripting"]),
    (3, "Data Science", "Tech", ["data analysis", "machine learning", "ml"]),
    (4, "Microsoft Excel", "Office", ["excel", "spreadsheet", "vlookup"]),
    (5, "Graphic Design", "Design", ["photoshop", "logo design"]),
    (6, "UI/UX Design", "Design", ["figma", "ux", "user experience"]),
    (7, "Video Editing", "Media", ["premiere pro", "capcut"]),
    (8, "Digital Marketing", "Business", ["seo", "social media marketing"]),
    (9, "Content Writing", "Business", ["copywriting", "blog writing"]),
    (10, "English Speaking", "Language", ["spoken english", "fluency"]),
    (11, "Photography", "Media", ["camera basics"]),
    (12, "Guitar", "Music", ["acoustic guitar", "music"]),
    (13, "Accounting", "Business", ["bookkeeping", "tally"]),
    (14, "AutoCAD", "Engineering", ["cad", "drafting"]),
    (15, "Public Speaking", "Soft Skills", ["presentation skills"]),
    (16, "Mobile App Development", "Tech", ["flutter", "android development"]),
    (17, "Cyber Security", "Tech", ["ethical hacking", "infosec"]),
    (18, "3D Modeling", "Design", ["blender"]),
    (19, "Cooking", "Lifestyle", ["baking"]),
    (20, "Personal Finance", "Business", ["budgeting", "investing basics"]),
]
MENTORS = [  # name, email, country, headline, [(skill, prof, yrs)], [(code, flu)], rating, reviews
    ("Rifat Hasan", "rifat@skillhub.dev", "Bangladesh",
     "Excel automation consultant for garment factories", [(4, 5, 9)],
     [("bn", "native"), ("en", "fluent")], 4.9, 312),
    ("Nusrat Jahan", "nusrat@skillhub.dev", "Bangladesh",
     "Data analyst teaching statistics in Bangla", [(3, 4, 6), (4, 4, 5)],
     [("bn", "native"), ("en", "fluent")], 4.8, 190),
    ("Ammar Khan", "ammar@skillhub.dev", "Pakistan",
     "Full-stack dev, project-based coding in Urdu/Hindi", [(1, 5, 7), (2, 4, 5)],
     [("ur", "native"), ("hi", "fluent"), ("en", "fluent")], 4.7, 240),
    ("Sofia Alvarez", "sofia@skillhub.dev", "Spain",
     "Ex-bank product designer, portfolio-driven UI/UX", [(6, 4, 6)],
     [("es", "native"), ("en", "fluent")], 4.6, 120),
    ("Tanvir Alam", "tanvir@skillhub.dev", "Bangladesh",
     "YouTuber editor teaching Premiere + Capcut fast", [(7, 4, 4)],
     [("bn", "native"), ("en", "conversational")], 4.4, 88),
    ("Omar Elsayed", "omar@skillhub.dev", "Egypt",
     "Cyber security analyst, Arabic medium", [(17, 5, 8)],
     [("ar", "native"), ("en", "fluent")], 4.5, 96),
]
COURSES = [  # mentor idx, title, category, lang, price, lessons, has_quiz
    (0, "Excel for Business: Zero to Dashboards", "Office", "bn", 0, 5, True),
    (0, "Advanced Excel Formulas & Automation", "Office", "bn", 1500, 6, True),
    (1, "Statistics for Data Science (in Bangla)", "Tech", "bn", 2000, 6, True),
    (2, "Full-Stack Web Development Roadmap", "Tech", "ur", 2500, 8, False),
    (2, "Python Basics with Projects", "Tech", "en", 0, 5, True),
    (3, "UI/UX Design with Figma", "Design", "es", 3000, 6, False),
    (4, "Video Editing Bootcamp for Creators", "Media", "bn", 1200, 5, False),
    (5, "Ethical Hacking Foundations", "Tech", "ar", 4000, 7, True),
]

import json

LESSON_TITLES = ["Intro and setup", "Core concepts", "Guided practice",
                 "Real project part 1", "Real project part 2", "Review and quiz prep"]
QUIZ_QS = [
    ("Which function looks up a value row by row?", ["VLOOKUP", "COUNT", "SUM", "LEN"], 0),
    ("What does a dashboard mainly help with?", ["Hiding data", "Visual insight",
     "Deleting rows", "Formatting fonts"], 1),
    ("Which shortcut opens Format Cells?", ["F1", "F2", "Ctrl+1", "Alt+F4"], 2),
    ("A pivot table is used for?", ["Drawing", "Summarizing data", "Printing", "Chat"], 1),
    ("Absolute reference sign is?", ["#", "$", "&", "@"], 1),
]


def _seed(session):
    for c, n in LANGS:
        session.add(Language(code=c, name=n))
    for sid, nm, cat, als in SK:
        session.add(Skill(id=sid, name=nm, category=cat))
        for a in als:
            session.add(SkillAlias(alias=a, skill_id=sid))
    session.add(User(name="Platform Admin", email="admin@skillhub.dev",
                     phone="01700000001", password_hash=hash_password("Admin123"),
                     role="admin"))
    mentors = []
    for i, (nm, em, country, hl, sks, lgs, rt, rv) in enumerate(MENTORS):
        u = User(name=nm, email=em, phone="017%08d" % (100 + i),
                 password_hash=hash_password("Mentor123"), role="mentor")
        session.add(u)
        session.flush()
        session.add(MentorProfile(user_id=u.id, headline=hl, country=country,
                                  rating=rt, reviews=rv, avg_reply_hours=2.0 + i,
                                  completion=78.0 + i))
        for sid, p, y in sks:
            session.add(MentorSkill(user_id=u.id, skill_id=sid, proficiency=p, years=y))
        for c, f in lgs:
            session.add(MentorLanguage(user_id=u.id, code=c, fluency=f))
        mentors.append(u)
    learners = []
    for j, (nm, em) in enumerate([("Karim Student", "learner@skillhub.dev"),
                                  ("Ayesha Rahman", "ayesha@skillhub.dev"),
                                  ("John Doe", "john@skillhub.dev")]):
        u = User(name=nm, email=em, phone="018%08d" % (200 + j),
                 password_hash=hash_password("Learner123"), role="learner",
                 lang="bn" if j < 2 else "en")
        session.add(u)
        session.flush()
        learners.append(u)
    courses = []
    for mi, title, cat, lang, price, nles, quiz in COURSES:
        c = Course(mentor_id=mentors[mi].id, title=title, category=cat,
                   language=lang, price=price, type="paid" if price else "free",
                   status="published", duration_hours=nles * 1.5,
                   description=f"Hands-on {title} course taught in {lang.upper()}.",
                   rating=round(4.3 + (mi % 5) * 0.1, 2), reviews=20 + mi * 7)
        session.add(c)
        session.flush()
        for pos in range(1, nles + 1):
            session.add(Lesson(course_id=c.id,
                               title=f"Lesson {pos}: {LESSON_TITLES[pos % 6]}",
                               position=pos))
        if quiz:
            qz = Quiz(course_id=c.id, title="Final Quiz", time_limit_min=15,
                      passing_score=60.0, published=True)
            session.add(qz)
            session.flush()
            for text, opts, corr in QUIZ_QS:
                session.add(Question(quiz_id=qz.id, text=text,
                                     options=json.dumps(opts), correct=corr, marks=5))
        session.add(Assignment(course_id=c.id, title="Practical Task",
                               instructions="Apply what you learned and submit a short report."))
        courses.append(c)
    for nm, acc in [("UCB", "3001234"), ("BRAC Bank", "5009876"),
                    ("City Bank", "7004321"), ("bKash", "01700111222")]:
        session.add(PaymentMethod(name=nm, account=acc, status="active"))
    session.flush()
    lids = [l.id for l in courses[0].lessons][:2]
    session.add(Enrollment(learner_id=learners[0].id, course_id=courses[0].id,
                           progress=33.3, done_lessons=json.dumps(lids),
                           last_lesson=lids[-1]))
    session.add(Txn(learner_id=learners[0].id, course_id=courses[1].id,
                    amount=1500.0, method="UCB", card_last4="4920",
                    status="success", ref="SH-DEMO-0001"))
    session.add_all([
        ChatMsg(sender_id=learners[0].id, receiver_id=mentors[0].id,
                text="Sir, when is the next live class?"),
        ChatMsg(sender_id=mentors[0].id, receiver_id=learners[0].id,
                text="Saturday 8 PM Bangladesh time. Bring your dataset."),
    ])
    session.commit()

def init_db():
    Base.metadata.create_all(engine)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    s = Session()
    try:
        if s.query(User).count() == 0:
            _seed(s)
    finally:
        s.close()


def load_engine_state(session):
    """Bridge DB -> pure matching-engine objects (SkillHub Match feature)."""
    skills = {x.id: x.name for x in session.query(Skill).all()}
    aliases = {a.alias: a.skill_id for a in session.query(SkillAlias).all()}
    lang_names = {l.code: l.name for l in session.query(Language).all()}
    mentors = []
    for u in session.query(User).filter_by(role="mentor").all():
        p = session.get(MentorProfile, u.id)
        if not p or u.status != "active":
            continue
        mentors.append(Mentor(
            id=u.id, name=u.name, country=p.country, headline=p.headline,
            rating=p.rating, reviews=p.reviews,
            avg_reply_hours=p.avg_reply_hours, completion=p.completion,
            skills=[SkillRow(s.skill_id, s.proficiency, s.years)
                    for s in session.query(MentorSkill).filter_by(user_id=u.id)],
            langs=[LangRow(l.code, l.fluency)
                   for l in session.query(MentorLanguage).filter_by(user_id=u.id)],
        ))
    return skills, aliases, lang_names, mentors


def get_user(session, token_payload):
    return session.get(User, int(token_payload["sub"])) if token_payload else None
