"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { api, getToken, getUser } from "@/lib/api";
import { useLang } from "@/components/LangContext";

const LANGS = [["en","English"],["bn","Bangla"],["hi","Hindi"],["ur","Urdu"],["ar","Arabic"],
  ["es","Spanish"],["fr","French"],["de","German"],["pt","Portuguese"],["tl","Tagalog"],
  ["id","Indonesian"],["tr","Turkish"],["ne","Nepali"],["fa","Farsi"]];
const LNAME = Object.fromEntries(LANGS);
const FALLBACK_CATS = ["Tech","Office","Design","Media","Business","Language","Music","Engineering","Soft Skills","Lifestyle"];
const EMO = { Tech: "💻", Office: "📊", Design: "🎨", Media: "🎬", Business: "💼", "Soft Skills": "🧠", Language: "🗣️", Music: "🎵", Engineering: "⚙️", Lifestyle: "🌿", Aviation: "✈️" };
const SORTS = [["rating","Top rated"],["popular","Most popular"],["newest","Newest"],["price_low","Price: low to high"],["price_high","Price: high to low"]];

export default function BrowsePage() {
  const [q, setQ] = useState(""), [cat, setCat] = useState(""), [lang, setLang] = useState("");
  const [maxPrice, setMaxPrice] = useState(""), [minRating, setMinRating] = useState("");
  const [level, setLevel] = useState(""), [sort, setSort] = useState("rating");
  const [meta, setMeta] = useState(null);
  const [data, setData] = useState(null), [err, setErr] = useState("");
  const [ready, setReady] = useState(false), [loading, setLoading] = useState(true);
  const [wish, setWish] = useState({});
  const { tr } = useLang();
  const cats = (meta && meta.all_categories) || FALLBACK_CATS;
  const levels = (meta && meta.levels) || ["Beginner", "Intermediate", "Advanced"];
  useEffect(() => {
    // Catalog is public: guests can browse. Wishlist needs a session.
    const sp = new URLSearchParams(window.location.search);
    const urlq = sp.get("q") || "";
    const urlcat = sp.get("category") || "";
    setQ(urlq); setCat(urlcat); setReady(true);
    api("/meta").then(setMeta).catch(() => {});
    runSearch(urlq, urlcat, "", "", "", "", "rating");
    if (getToken()) api("/wishlist").then(r => setWish(Object.fromEntries(r.courses.map(w => [w.course_id, true])))).catch(() => {});
  }, []);
  async function runSearch(qv, cv, lv, pv, rv, lev, srt) {
    setLoading(true); setErr("");
    const p = new URLSearchParams({ q: qv, category: cv, language: lv,
      max_price: pv || 0, min_rating: rv || 0, level: lev || "", sort: srt || "rating" });
    try { setData(await api("/courses?" + p.toString())); } catch (x) { setErr(x.message); }
    setLoading(false);
  }
  function search(e) { if (e) e.preventDefault(); runSearch(q, cat, lang, maxPrice, minRating, level, sort); }
  async function toggleWish(id) {
    if (!getToken()) { window.location = "/login"; return; }
    try {
      const r = await api("/wishlist/" + id, { method: "POST" });
      setWish(w => { const n = { ...w }; if (r.saved) n[id] = true; else delete n[id]; return n; });
    } catch (e) {}
  }
  if (!ready) return null;
  const u = getUser();
  const list = data ? data.courses : [];
  return (
    <div><Nav /><div className="wrap">
      <h2 style={{ marginTop: 4 }}>{tr("availableCourses")} {u && <span className="muted" style={{ fontWeight: 400 }}>{tr("asRole")} {u.role==="mentor"?tr("role_mentor"):u.role==="admin"?tr("role_admin"):tr("role_learner")}</span>}</h2>
      <form className="panel" onSubmit={search} style={{ padding: 18 }}>
        <div className="grid g4" style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr" }}>
          <input placeholder={tr("searchTitle")} value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={cat} onChange={(e) => setCat(e.target.value)}>
            <option value="">{tr("allCategories")}</option>
            {cats.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={lang} onChange={(e) => setLang(e.target.value)}>
            <option value="">{tr("anyLanguage")}</option>
            {LANGS.map(([c, n]) => <option key={c} value={c}>{n}</option>)}
          </select>
          <input placeholder={tr("maxPricePh")} value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} />
        </div>
        <div className="grid g4" style={{ gridTemplateColumns: "1fr 1fr 1fr 1fr", marginTop: 10 }}>
          <select value={level} onChange={(e) => setLevel(e.target.value)}>
            <option value="">{tr("anyLevel")}</option>
            {levels.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
          <select value={sort} onChange={(e) => setSort(e.target.value)}>
            {SORTS.map(([v, n]) => <option key={v} value={v}>{n}</option>)}
          </select>
          <input placeholder={tr("minRatingPh")} value={minRating} onChange={(e) => setMinRating(e.target.value)} />
          <button className="btn">{tr("search")}</button>
        </div>
        <div style={{ marginTop: 10 }}>
          <span className="btn ghost sm" onClick={() => { setQ(""); setCat(""); setLang(""); setMaxPrice(""); setMinRating(""); setLevel(""); setSort("rating"); runSearch("", "", "", "", "", "", "rating"); window.history.replaceState({}, "", "/browse"); }} style={{ cursor: "pointer" }}>{tr("resetFilters")}</span>
        </div>
      </form>
      {err && <p className="err">{err}</p>}
      {loading && <p className="muted">{tr("loadingCourses")}</p>}
      {!loading && data && <p className="muted">{data.count} {tr("coursesFound")}</p>}
      {!loading && data && data.count === 0 &&
        <div className="panel" style={{ textAlign: "center", padding: 34 }}>
          <p style={{ fontSize: 32, margin: 0 }}>🔍</p>
          <p style={{ fontWeight: 800, margin: "10px 0 2px" }}>{tr("noCoursesTitle")}</p>
          <p className="muted" style={{ margin: 0 }}>{tr("noCoursesBody")}</p>
        </div>}
      <div className="grid g3">
        {!loading && list.map((c) => (
          <div key={c.id} className="card" style={{ padding: 0, overflow: "hidden", margin: 0 }}>
            <div style={{ height: 88, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 44, background: "linear-gradient(135deg,#efe9ff,#d6c8f0)", position: "relative" }}>
              <span>{EMO[c.category] || "🎓"}</span>
              <span className="pill" style={{ position: "absolute", top: 10, right: 12 }}>{c.category}</span>
              <button onClick={() => toggleWish(c.id)} title={wish[c.id] ? tr("removeSaved") : tr("saveForLater")}
                style={{ position: "absolute", top: 8, left: 10, border: "none", background: "rgba(255,255,255,.9)", borderRadius: "50%", width: 30, height: 30, cursor: "pointer", fontSize: 14, lineHeight: "30px", padding: 0 }}>
                {wish[c.id] ? "❤️" : "🤍"}</button>
            </div>
            <div style={{ padding: "14px 18px 18px" }}>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">{tr("courseName")}: </span><b>{c.title}</b></p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">{tr("instructor")}: </span>
                <a href={`/mentor/${c.mentor_id}`} style={{ fontWeight: 600 }}>{c.mentor}</a> · {c.reviews > 0 ? "★ " + c.rating + " (" + c.reviews + ")" : tr("newNotRated")}</p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">{tr("language")}: </span>{LNAME[c.language] || c.language} · {c.level || tr("anyLevel")}</p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">{tr("price")}: </span><b style={{ color: c.price ? "var(--orange)" : "var(--teal)" }}>{c.price ? "BDT " + c.price : tr("free")}</b></p>
              <p className="muted" style={{ margin: "6px 0 0", fontSize: 12 }}>{c.lessons.length} {tr("lessons")} · {c.duration_hours}{tr("hoursWord")} · {c.quizzes.length} {tr("quiz")}</p>
              <a href={`/course/${c.id}`} style={{ display: "block", textAlign: "center", marginTop: 12 }}>
                <span className={"btn block sm " + (c.price ? "pink" : "teal")}>{c.price ? tr("buy") : tr("enrollFree")}</span>
              </a>
            </div>
          </div>
        ))}
      </div>
    </div></div>
  );
}