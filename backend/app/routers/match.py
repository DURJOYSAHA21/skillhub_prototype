"""Skillhub Match feature: global language-aware mentor ranking."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import db
from ..deps import get_db
from ..engine import resolve_skill, rank_mentors

router = APIRouter(tags=["match"])


@router.get("/meta")
def meta(session: Session = Depends(get_db)):
    skills = session.query(db.Skill).order_by(db.Skill.name).all()
    langs = session.query(db.Language).all()
    cats = session.query(db.Category).order_by(db.Category.name).all()
    names = sorted({c.category for c in session.query(db.Course)
                    .filter_by(status="published").all()} |
                   {c.name for c in cats})
    return {"skills": [{"id": s.id, "name": s.name, "category": s.category} for s in skills],
            "languages": [{"code": l.code, "name": l.name} for l in langs],
            "categories": [{"name": c.name, "icon": c.icon} for c in cats],
            "all_categories": names,
            "levels": ["Beginner", "Intermediate", "Advanced"]}


@router.get("/skills/resolve")
def resolve(q: str, session: Session = Depends(get_db)):
    skills, aliases, _, _ = db.load_engine_state(session)
    sid, method = resolve_skill(q, skills, aliases)
    if not sid:
        raise HTTPException(404, f"Could not resolve skill: {q}")
    return {"query": q, "skill_id": sid, "skill": skills[sid], "method": method}


@router.get("/match")
def match(skill: str, langs: str = "", limit: int = 10, min_rating: float = 0,
          session: Session = Depends(get_db)):
    skills, aliases, lang_names, mentors = db.load_engine_state(session)
    sid, method = resolve_skill(skill, skills, aliases)
    if not sid:
        raise HTTPException(404, f"Could not resolve skill: {skill}")
    wanted = [c.strip().lower() for c in langs.split(",") if c.strip()]
    bad = [c for c in wanted if c not in lang_names]
    if bad:
        raise HTTPException(400, f"Unknown language codes: {bad}")
    ranked = rank_mentors(mentors, sid, wanted, limit=limit, min_rating=min_rating)
    return {"query": skill, "resolved_skill": skills[sid], "resolution_method": method,
            "languages": wanted, "results": [
                {"mentor_id": r.mentor.id, "name": r.mentor.name,
                 "country": r.mentor.country, "headline": r.mentor.headline,
                 "match_percent": round(r.score * 100, 1),
                 "breakdown": {"skill": round(r.skill_s, 3), "language": round(r.lang_s, 3),
                                "quality": round(r.quality_s, 3)},
                 "matched_language": lang_names.get(r.matched_lang, r.matched_lang),
                 "teaches_in": [lang_names.get(l.code, l.code) for l in r.mentor.langs],
                 "rating": r.mentor.rating, "reviews": r.mentor.reviews,
                 "reasons": r.reasons} for r in ranked]}


@router.get("/mentors/{mid}")
def mentor(mid: int, session: Session = Depends(get_db)):
    u = session.get(db.User, mid)
    if not u or u.role != "mentor":
        raise HTTPException(404, "Mentor not found.")
    p = session.get(db.MentorProfile, mid)
    _, aliases, lang_names, _ = db.load_engine_state(session)
    skills = [{"skill": (session.get(db.Skill, s.skill_id) or db.Skill(name="")).name,
               "proficiency": s.proficiency, "years": s.years}
              for s in session.query(db.MentorSkill).filter_by(user_id=mid).all()]
    courses = [{"id": c.id, "title": c.title, "price": c.price, "language": c.language,
                 "level": c.level, "rating": c.rating, "reviews": c.reviews,
                 "students": session.query(db.Enrollment).filter_by(course_id=c.id).count()}
                for c in session.query(db.Course).filter_by(mentor_id=mid,
                                                            status="published").all()]
    students = sum(session.query(db.Enrollment).filter_by(course_id=c["id"]).count()
                   for c in courses)
    return {"id": u.id, "name": u.name, "picture": u.picture or "",
            "headline": p.headline if p else "", "about": (p.about if p else "") or "",
            "verified": bool(p and p.verified), "students": students,
            "country": p.country if p else "", "rating": p.rating if p else 0,
            "reviews": p.reviews if p else 0,
            "languages": [f"{lang_names.get(l.code, l.code)} ({l.fluency})"
                          for l in session.query(db.MentorLanguage).filter_by(user_id=mid).all()],
            "langs": [{"code": l.code, "fluency": l.fluency}
                      for l in session.query(db.MentorLanguage).filter_by(user_id=mid).all()],
            "skills": skills, "courses": courses}
