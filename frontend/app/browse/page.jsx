"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { api, getToken, getUser } from "@/lib/api";

const LANGS = [["en","English"],["bn","Bangla"],["hi","Hindi"],["ur","Urdu"],["ar","Arabic"],
  ["es","Spanish"],["fr","French"],["de","German"],["pt","Portuguese"],["tl","Tagalog"],
  ["id","Indonesian"],["tr","Turkish"],["ne","Nepali"],["fa","Farsi"]];
const LNAME = Object.fromEntries(LANGS);
const EMO = { Tech: "💻", Office: "📊", Design: "🎨", Media: "🎬", Business: "💼", "Soft Skills": "🧠", Language: "🗣️", Music: "🎵", Engineering: "⚙️", Lifestyle: "🌿" };

export default function BrowsePage() {
  const [q, setQ] = useState(""), [cat, setCat] = useState(""), [lang, setLang] = useState("");
  const [maxPrice, setMaxPrice] = useState(""), [minRating, setMinRating] = useState("");
  const [data, setData] = useState(null), [err, setErr] = useState("");
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!getToken()) { window.location = "/login"; return; }
    const urlq = new URLSearchParams(window.location.search).get("q") || "";
    setQ(urlq); setReady(true);
    runSearch(urlq, "", "", "", "");
  }, []);
  async function runSearch(qv, cv, lv, pv, rv) {
    setErr("");
    const p = new URLSearchParams({ q: qv, category: cv, language: lv,
      max_price: pv || 0, min_rating: rv || 0 });
    try { setData(await api("/courses?" + p.toString())); } catch (x) { setErr(x.message); }
  }
  function search(e) { if (e) e.preventDefault(); runSearch(q, cat, lang, maxPrice, minRating); }
  if (!ready) return null;
  const u = getUser();
  return (
    <div><Nav /><div className="wrap">
      <h2 style={{ marginTop: 4 }}>Available Courses {u && <span className="muted" style={{ fontWeight: 400 }}>as {u.role}</span>}</h2>
      <form className="panel" onSubmit={search} style={{ padding: 18 }}>
        <div className="grid g4" style={{ gridTemplateColumns: "2fr 1fr 1fr 1fr" }}>
          <input placeholder="Search title or keyword…" value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={cat} onChange={(e) => setCat(e.target.value)}>
            <option value="">All categories</option>
            {["Tech","Office","Design","Media","Business","Language","Music","Engineering","Soft Skills","Lifestyle"].map(c =>
              <option key={c} value={c}>{c}</option>)}
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
      {data && <p className="muted">{data.count} courses found</p>}
      <div className="grid g3">
        {data && data.courses.map((c) => (
          <div key={c.id} className="card" style={{ padding: 0, overflow: "hidden", margin: 0 }}>
            <div style={{ height: 88, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 44, background: "linear-gradient(135deg,#efe9ff,#d6c8f0)", gap: 10 }}>
              <span>{EMO[c.category] || "🎓"}</span>
              <span className="pill" style={{ position: "absolute", marginTop: -70, right: 14 }}>{c.category}</span>
            </div>
            <div style={{ padding: "14px 18px 18px" }}>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Course Name: </span><b>{c.title}</b></p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Instructor: </span>{c.mentor} · ★ {c.rating} ({c.reviews})</p>
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