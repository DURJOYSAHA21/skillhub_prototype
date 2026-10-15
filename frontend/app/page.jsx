"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { useLang } from "@/components/LangContext";
import { LANG_META } from "@/lib/i18n";
import { api, getUser, getToken, API } from "@/lib/api";

const LANGS = { en: "English", bn: "Bangla", hi: "Hindi", ur: "Urdu", ar: "Arabic", es: "Spanish", fr: "French", zh: "Chinese", id: "Indonesian", tl: "Tagalog", pt: "Portuguese", tr: "Turkish", ne: "Nepali", fa: "Farsi" };
const EMO = { Tech: "💻", Office: "📊", Design: "🎨", Media: "🎬", Business: "💼", "Soft Skills": "🧠", Language: "🗣️", Music: "🎵", Engineering: "⚙️", Lifestyle: "🌿", Aviation: "✈️" };
const SEED_FEATURED = [
  { id: 1, title: "Excel for Business: Zero to Dashboards", mentor: "Rifat Hasan", category: "Office", language: "bn", price: 0 },
  { id: 5, title: "Python Basics with Projects", mentor: "Ammar Khan", category: "Tech", language: "en", price: 0 },
  { id: 6, title: "UI/UX Design with Figma", mentor: "Sofia Alvarez", category: "Design", language: "es", price: 3000 },
];

export default function Home() {
  const [u, setU] = useState(null);
  const [featured, setFeatured] = useState(SEED_FEATURED);
  const [q, setQ] = useState("");
  const [health, setHealth] = useState(null);
  const [cats, setCats] = useState([]);
  const { lang, setLang, tr } = useLang();
  useEffect(() => {
    const cur = getUser();
    setU(cur);
    fetch(API + "/api/health").then((r) => r.json()).then(setHealth).catch(() => {});
    api("/meta").then((m) => setCats(m.categories || [])).catch(() => {});
    if (cur && getToken()) {
      api("/courses?max_price=0&min_rating=0").then((d) => {
        if (d.courses && d.courses.length) setFeatured(d.courses.slice(0, 3));
      }).catch(() => {});
    }
  }, []);
  function goSearch(e) { e.preventDefault(); window.location = "/browse?q=" + encodeURIComponent(q); }
  return (
    <div><Nav /><div className="wrap">
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end", marginTop: 8 }}>
        {Object.keys(LANG_META).map((code) => (
          <button key={code} onClick={() => setLang(code)}
            className={"chip" + (code === lang ? " on" : "")}
            style={{ cursor: "pointer" }}>{LANG_META[code].native}</button>
        ))}
      </div>
      <div className="hero" style={{ marginTop: 8 }}>
        <div style={{ maxWidth: 660, position: "relative", zIndex: 1 }}>
          <div style={{ fontSize: 34, fontWeight: 900, lineHeight: 1.2 }}>
            SkillHub <span style={{ color: "#ffd76a" }}>:</span> {tr("hero1")}{" "}
            <span style={{ color: "#ffd76a", textDecoration: "underline wavy rgba(255,215,106,.5) 2px" }}>{tr("hero2")}</span>
          </div>
          <p style={{ color: "#c9cdd8", marginTop: 14, fontSize: 15, lineHeight: 1.6 }}>
            {tr("heroSub")}</p>
          <form className="searchpill" onSubmit={goSearch} style={{ marginTop: 24, maxWidth: 520 }}>
            <span>🔍</span>
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={tr("searchPlaceholder")} />
            <button className="btn sm" style={{ flex: "0 0 auto" }}>{tr("search")}</button>
          </form>
          <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
            {u ? <a href="/browse"><button className="btn teal">{tr("browseCourses")}</button></a>
                : <a href="/login"><button className="btn">{tr("login")}</button></a>}
            {!u && <a href="/signup"><button className="btn ghost">{tr("createAccount")}</button></a>}
            <a href="/match"><button className="btn dark">{tr("findMentor")}</button></a>
          </div>
        </div>
      </div>
      {cats.length > 0 && (
        <div style={{ marginTop: 26 }}>
          <h3 style={{ margin: "0 0 12px" }}>{tr("browseCategories")}</h3>
          <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(116px, 1fr))", gap: 12 }}>
            {cats.map((c) => (
              <a key={c.name} href={"/browse?category=" + encodeURIComponent(c.name)} className="card"
                style={{ padding: "16px 8px", textAlign: "center", margin: 0, textDecoration: "none", color: "inherit" }}>
                <div style={{ fontSize: 34 }}>{c.icon || EMO[c.name] || "🎓"}</div>
                <div style={{ fontWeight: 700, fontSize: 13, marginTop: 6 }}>{c.name}</div>
                {typeof c.count === "number" && <div className="muted" style={{ fontSize: 11 }}>{c.count} {tr("coursesWord")}</div>}
              </a>
            ))}
          </div>
        </div>
      )}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "30px 0 2px" }}>
        <h3 style={{ margin: 0 }}>{tr("featured")}</h3>
        <a href={u ? "/browse" : "/browse"}><span className="btn ghost sm">{tr("seeMore")} →</span></a>
      </div>
      <div className="grid g3">
        {featured.map((c) => (
          <div key={c.id} className="card" style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ height: 92, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 46, background: "linear-gradient(135deg,#efe9ff,#d6c8f0)" }}>
              {EMO[c.category] || "🎓"}
            </div>
            <div style={{ padding: "14px 18px 18px" }}>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">{tr("courseName")}: </span><b>{c.title}</b></p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">{tr("instructor")}: </span>{c.mentor}</p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">{tr("language")}: </span>{LANGS[c.language] || c.language}</p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">{tr("price")}: </span><b style={{ color: c.price ? "var(--orange)" : "var(--teal)" }}>{c.price ? "BDT " + c.price : tr("free")}</b></p>
              <a href={"/course/" + c.id} style={{ display: "block", textAlign: "center", marginTop: 14 }}>
                <span className={"btn block sm " + (c.price ? "pink" : "teal")}>{c.price ? tr("buy") : tr("enrollFree")}</span>
              </a>
            </div>
          </div>
        ))}
      </div>
      <div className="grid g3" style={{ marginTop: 26 }}>
        <div className="card"><h3>🌍 {tr("featMultiTitle")}</h3><p className="muted">{tr("featMultiBody")}</p></div>
        <div className="card"><h3>🎯 {tr("featMatchTitle")}</h3><p className="muted">{tr("featMatchBody")}</p></div>
        <div className="card"><h3>💳 {tr("featLoopTitle")}</h3><p className="muted">{tr("featLoopBody")}</p></div>
      </div>
      <div className="panel">
        <h3 style={{ marginTop: 0 }}>Demo accounts (seeded)</h3>
        <table><tbody>
          <tr><td>Admin</td><td>admin@skillhub.dev</td><td>Admin123</td></tr>
          <tr><td>Mentor</td><td>rifat@skillhub.dev</td><td>Mentor123</td></tr>
          <tr><td>Learner</td><td>learner@skillhub.dev</td><td>Learner123</td></tr>
        </tbody></table>
        <p className="muted">OTP emails are simulated: the code is shown right on screen in dev mode.</p>
        {health && <p className="ok" style={{ marginTop: 10 }}>API online · {health.users} users · {health.courses} courses</p>}
      </div>
      <div className="foot">Skillhub — a global, multi-language learning platform</div>
    </div></div>
  );
}