"""SkillHub Match - mentor matching engine (pure python, no DB deps).

Scores mentors against a learner query (skill + preferred languages,
ordered by preference) with weighted multi-criteria scoring and an
explainable breakdown per result.
"""
from dataclasses import dataclass, field

FLUENCY = {"native": 1.0, "fluent": 0.85, "conversational": 0.55}
W_SKILL, W_LANG, W_QUALITY = 0.45, 0.30, 0.25


@dataclass
class SkillRow:
    skill_id: int
    proficiency: int  # 1..5 teaching depth
    years: float


@dataclass
class LangRow:
    code: str
    fluency: str  # key of FLUENCY


@dataclass
class Mentor:
    id: int
    name: str
    country: str
    headline: str
    rating: float
    reviews: int
    avg_reply_hours: float
    completion: float  # % of enrolled learners who finish
    skills: list = field(default_factory=list)   # SkillRow[]
    langs: list = field(default_factory=list)    # LangRow[]

def normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def resolve_skill(query: str, skills: dict, aliases: dict):
    """Map free text to a skill id. skills: {id: name}, aliases: {alias: id}.
    Returns (skill_id, method) or (None, None)."""
    q = normalize(query)
    if not q:
        return None, None
    for sid, name in skills.items():
        if normalize(name) == q:
            return sid, "exact"
    if q in aliases:
        return aliases[q], "alias"
    for sid, name in skills.items():  # phrase containment: "learn excel now" -> Excel
        n = normalize(name)
        if len(n) > 2 and (n in q or q in n):
            return sid, "containment"
    for alias, sid in aliases.items():
        if len(alias) > 2 and alias in q:
            return sid, "alias-contains"
    return None, None


def skill_score(row: SkillRow) -> float:
    return 0.75 * (row.proficiency / 5.0) + 0.25 * (min(row.years, 10.0) / 10.0)


def lang_fluency_map(langs) -> dict:
    best = {}
    for lr in langs:
        f = FLUENCY.get(lr.fluency, 0.0)
        if f > best.get(lr.code, 0.0):
            best[lr.code] = f
    return best


def lang_score(langs, wanted: list):
    """wanted: learner languages ordered by preference. Returns (score, best_code)."""
    if not wanted:
        return 0.5, None  # neutral when learner states no preference
    best = lang_fluency_map(langs)
    total, wsum = 0.0, 0.0
    top_pair = (0.0, None)
    for rank, code in enumerate(wanted):
        w = max(0.4, 1.0 - 0.15 * rank)  # first choice weighs most
        m = best.get(code, 0.0)
        if m * w > top_pair[0]:
            top_pair = (m * w, code)
        total += w * m
        wsum += w
    return (total / wsum if wsum else 0.0), top_pair[1]

def quality_score(m: Mentor) -> float:
    reply = max(0.0, 1.0 - min(m.avg_reply_hours, 24.0) / 24.0)
    return 0.5 * (m.rating / 5.0) + 0.25 * reply + 0.25 * (m.completion / 100.0)


@dataclass
class MatchResult:
    mentor: Mentor
    score: float
    skill_s: float
    lang_s: float
    quality_s: float
    matched_lang: str
    reasons: list = field(default_factory=list)


def rank_mentors(mentors, skill_id, wanted_langs, limit=10, min_rating=0.0):
    """Core ranking: keep mentors who teach the skill AND at least one wanted
    language, score them, return sorted top-N with explainable reasons."""
    out = []
    for m in mentors:
        if m.rating < min_rating:
            continue
        rows = [s for s in m.skills if s.skill_id == skill_id]
        if not rows:
            continue
        ss = max(skill_score(r) for r in rows)
        ls, lang = lang_score(m.langs, wanted_langs)
        if wanted_langs and ls <= 0.0:
            continue  # language is the hard gate - the product promise
        qs = quality_score(m)
        total = W_SKILL * ss + W_LANG * ls + W_QUALITY * qs
        out.append(MatchResult(m, round(total, 4), round(ss, 3),
                               round(ls, 3), round(qs, 3), lang,
                               _reasons(m, rows, ss, ls, lang, wanted_langs)))
    out.sort(key=lambda r: (-r.score, -r.mentor.rating, -r.mentor.reviews))
    return out[:limit]


def _reasons(m, rows, ss, ls, lang, wanted):
    best_row = max(rows, key=lambda r: skill_score(r))

    r = [f"Depth L{best_row.proficiency}/5 with {best_row.years:g} yrs teaching"]
    if lang:
        flu = lang_fluency_map(m.langs).get(lang, 0)
        label = "native" if flu >= 1.0 else ("fluent" if flu >= 0.8 else "conversational")
        r.append(f"Teaches in {lang.upper()} ({label})")
    r.append(f"Rated {m.rating:.1f} by {m.reviews} learners")
    r.append(f"~{m.avg_reply_hours:g}h avg reply, {m.completion:.0f}% course completion")
    return r
