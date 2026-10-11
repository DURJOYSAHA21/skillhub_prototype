"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { api, getToken, getUser } from "@/lib/api";

const LANGS = [["en","English"],["bn","Bangla"],["hi","Hindi"],["ur","Urdu"],["ar","Arabic"],
  ["es","Spanish"],["fr","French"],["de","German"],["pt","Portuguese"],["tl","Tagalog"],
  ["id","Indonesian"],["tr","Turkish"],["ne","Nepali"],["fa","Farsi"]];
const LNAME = Object.fromEntries(LANGS);
const CATS = ["Tech","Office","Design","Media","Business","Language","Music","Engineering","Soft Skills","Lifestyle"];
const EMO = { Tech: "💻", Office: "📊", Design: "🎨", Media: "🎬", Business: "💼", "Soft Skills": "🧠", Language: "🗣️", Music: "🎵", Engineering: "⚙️", Lifestyle: "🌿" };

export default function BrowsePage() {
  const [q, setQ] = useState(""), [cat, setCat] = useState(""), [lang, setLang] = useState("");
  const [maxPrice, setMaxPrice] = useState(""), [minRating, setMinRating] = useState("");
  const [data, setData] = useState(null), [err, setErr] = useState("");
  const [ready, setReady] = useState(false), [loading, setLoading] = useState(true);
  const [wish, setWish] = useState({});
  useEffect(() => {
    if (!getToken()) { window.location = "/login"; return; }
    const urlq = new URLSearchParams(window.location.search).get("q") || "";
    setQ(urlq); setReady(true);
    runSearch(urlq, "", "", "", "");
    api("/wishlist").then(r => setWish(Object.fromEntries(r.courses.map(w => [w.course_id, true])))).catch(() => {});
  }, []);
  async function runSearch(qv, cv, lv, pv, rv) {
    setLoading(true); setErr("");
    const p = new URLSearchParams({ q: qv, category: cv, language: lv,
      max_price: pv || 0, min_rating: rv || 0 });
    try { setData(await api("/courses?" + p.toString())); } catch (x) { setErr(x.message); }
    setLoading(false);
  }
  function search(e) { if (e) e.preventDefault(); runSearch(q, cat, lang, maxPrice, minRating); }
  async function toggleWish(id) {
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
      <h2 style={{ marginTop: 4 }}>Available Courses {u && <span className="muted" style={{ fontWeight: 400 }}>as {u.role}</span>}</h2>
      <form className="panel" onSubmit={search} style={{ padding: 18 }}>
        <div className="grid g4" style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr" }}>
          <input placeholder="Search title or keyword…" value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={cat} onChange={(e) => setCat(e.target.value)}>
            <option value="">All categories</option>
            {CATS.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={lang} onChange={(e) => setLang(e.target.value)}>
            <option value="">Any language</option>
            {LANGS.map(([c, n]) => <option key={c} value={c}>{n}</option>)}
          </select>
          <input placeholder="Max price (BDT)" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)} />
        </div>
        <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
          <input style={{ maxWidth: 160 }} placeholder="Min rating" value={minRating} onChange={(e) => setMinRating(e.target.value)} />
          <button className="btn">Search</button>
          <span className="btn ghost" onClick={() => { setQ(""); setCat(""); setLang(""); setMaxPrice(""); setMinRating(""); runSearch("", "", "", "", ""); }} style={{ cursor: "pointer" }}>Reset</span>
        </div>
      </form>
      {err && <p className="err">{err}</p>}
      {loading && <p className="muted">Loading courses…</p>}
      {!loading && data && <p className="muted">{data.count} courses found</p>}
      {!loading && data && data.count === 0 &&
        <div className="panel" style={{ textAlign: "center", padding: 34 }}>
          <p style={{ fontSize: 32, margin: 0 }}>🔍</p>
          <p style={{ fontWeight: 800, margin: "10px 0 2px" }}>No courses match your filters</p>
          <p className="muted" style={{ margin: 0 }}>Try a different keyword, or press Reset to see everything.</p>
        </div>}
      <div className="grid g3">
        {!loading && list.map((c) => (
          <div key={c.id} className="card" style={{ padding: 0, overflow: "hidden", margin: 0 }}>
            <div style={{ height: 88, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 44, background: "linear-gradient(135deg,#efe9ff,#d6c8f0)", position: "relative" }}>
              <span>{EMO[c.category] || "🎓"}</span>
              <span className="pill" style={{ position: "absolute", top: 10, right: 12 }}>{c.category}</span>
              <button onClick={() => toggleWish(c.id)} title={wish[c.id] ? "Remove from saved" : "Save for later"}
                style={{ position: "absolute", top: 8, left: 10, border: "none", background: "rgba(255,255,255,.9)", borderRadius: "50%", width: 30, height: 30, cursor: "pointer", fontSize: 14, lineHeight: "30px", padding: 0 }}>
                {wish[c.id] ? "❤️" : "🤍"}</button>
            </div>
            <div style={{ padding: "14px 18px 18px" }}>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Course Name: </span><b>{c.title}</b></p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Instructor: </span>
                <a href={`/mentor/${c.mentor_id}`} style={{ fontWeight: 600 }}>{c.mentor}</a> · ★ {c.rating} ({c.reviews})</p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Language: </span>{LNAME[c.language] || c.language}</p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Price: </span><b style={{ color: c.price ? "var(--orange)" : "var(--teal)" }}>{c.price ? "BDT " + c.price : "Free"}</b></p>
              <p className="muted" style={{ margin: "6px 0 0", fontSize: 12 }}>{c.lessons.length} lessons · {c.duration_hours}h · {c.quizzes.length} quiz</p>
              <a href={`/course/${c.id}`} style={{ display: "block", textAlign: "center", marginTop: 12 }}>
                <span className={"btn block sm " + (c.price ? "pink" : "teal")}>{c.price ? "Buy Now" : "Enroll Now (Free)"}</span>
              </a>
            </div>
          </div>
        ))}
      </div>
    </div></div>
  );
}