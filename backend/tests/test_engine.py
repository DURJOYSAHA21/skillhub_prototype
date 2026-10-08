"""Unit tests for the pure matching engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pytest  # noqa: E402
from app.engine import (Mentor, SkillRow, LangRow, resolve_skill, skill_score,
                        lang_score, quality_score, rank_mentors)

SKILLS = {4: "Microsoft Excel", 1: "Web Development"}
ALIASES = {"excel": 4, "spreadsheet": 4, "web dev": 1}


def mk(mid=1, rating=4.5, reviews=100, reply=4.0, comp=80.0, skills=None, langs=None):
    return Mentor(id=mid, name=f"M{mid}", country="Bangladesh", headline="h",
                  rating=rating, reviews=reviews, avg_reply_hours=reply,
                  completion=comp,
                  skills=skills or [SkillRow(4, 5, 9)],
                  langs=langs or [LangRow("bn", "native")])


def test_resolve_exact_and_alias():
    assert resolve_skill("Microsoft Excel", SKILLS, ALIASES) == (4, "exact")
    assert resolve_skill("Excel", SKILLS, ALIASES) == (4, "alias")
    assert resolve_skill("  spreadsheet ", SKILLS, ALIASES) == (4, "alias")


def test_resolve_phrase_and_miss():
    assert resolve_skill("learn excel fast", SKILLS, ALIASES)[0] == 4
    assert resolve_skill("knitting", SKILLS, ALIASES) == (None, None)


def test_skill_score_bounds():
    assert skill_score(SkillRow(4, 5, 10)) == 1.0
    assert skill_score(SkillRow(4, 1, 0)) == pytest.approx(0.15)
    assert 0 <= skill_score(SkillRow(4, 3, 4)) <= 1


def test_lang_gate_and_preference():
    langs = [LangRow("en", "fluent")]
    s, code = lang_score(langs, ["bn", "en"])
    assert code == "en" and 0 < s < 1
    s2, _ = lang_score(langs, ["bn"])
    assert s2 == 0.0  # hard gate: unwanted language only
    s3, _ = lang_score(langs, [])
    assert s3 == 0.5  # neutral


def test_quality_monotonic():
    assert quality_score(mk(rating=5, reply=1, comp=95)) > quality_score(mk(rating=3, reply=20, comp=60))


def test_ranking_filters_and_orders():
    good_bn = mk(1, rating=4.9, langs=[LangRow("bn", "native")])
    meh_bn = mk(2, rating=3.9, reply=18, comp=60, langs=[LangRow("bn", "conversational")])
    en_only = mk(3, langs=[LangRow("en", "fluent")])
    no_skill = mk(4, skills=[SkillRow(1, 5, 9)])
    res = rank_mentors([en_only, meh_bn, good_bn, no_skill], 4, ["bn"])
    assert [r.mentor.id for r in res] == [1, 2]  # en-only + no-skill excluded
    assert res[0].score > res[1].score
    assert res[0].reasons  # explainable


def test_min_rating_filter():
    res = rank_mentors([mk(1, rating=3.0), mk(2, rating=4.8)], 4, ["bn"], min_rating=4.0)
    assert [r.mentor.id for r in res] == [2]
