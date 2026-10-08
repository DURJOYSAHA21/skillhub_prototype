"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { api, getUser, getToken, API } from "@/lib/api";

const LANGS = { en: "English", bn: "Bangla", hi: "Hindi", ur: "Urdu", ar: "Arabic", es: "Spanish", fr: "French" };
const EMO = { Tech: "💻", Office: "📊", Design: "🎨", Media: "🎬", Business: "💼", "Soft Skills": "🧠", Language: "🗣️", Music: "🎵", Engineering: "⚙️", Lifestyle: "🌿" };
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
  useEffect(() => {
    const cur = getUser();
    setU(cur);
    fetch(API + "/api/health").then((r) => r.json()).then(setHealth).catch(() => {});
    if (cur && getToken()) {
      api("/courses?max_price=0&min_rating=0").then((d) => {
        if (d.courses && d.courses.length) setFeatured(d.courses.slice(0, 3));
      }).catch(() => {});
    }
  }, []);
  function goSearch(e) { e.preventDefault(); window.location = "/browse?q=" + encodeURIComponent(q); }
  return (
    <div><Nav /><div className="wrap">
      <div className="hero" style={{ marginTop: 8 }}>
        <div style={{ maxWidth: 660, position: "relative", zIndex: 1 }}>
          <div style={{ fontSize: 34, fontWeight: 900, lineHeight: 1.2 }}>
            SkillHub <span style={{ color: "#ffd76a" }}>:</span> One Platform to{" "}
            <span style={{ color: "#ffd76a", textDecoration: "underline wavy rgba(255,215,106,.5) 2px" }}>Learn Every Skill</span>
          </div>
          <p style={{ color: "#c9cdd8", marginTop: 14, fontSize: 15, lineHeight: 1.6 }}>
            Courses, mentors, payments, quizzes, certificates — in your own language.
            Learn any skill, in any of 14 languages, from mentors worldwide.</p>
          <form className="searchpill" onSubmit={goSearch} style={{ marginTop: 24, maxWidth: 520 }}>
            <span>🔍</span>
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="What Do You Want To Learn?" />
            <button className="btn sm" style={{ flex: "0 0 auto" }}>Search</button>
          </form>
          <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
            {u ? <a href="/browse"><button className="btn teal">Browse Courses</button></a>
                : <a href="/login"><button className="btn">Login</button></a>}
            {!u && <a href="/signup"><button className="btn ghost">Create Account</button></a>}
            <a href="/match"><button className="btn dark">Find a Mentor</button></a>
          </div>
        </div>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "30px 0 2px" }}>
        <h3 style={{ margin: 0 }}>Featured Courses</h3>
        <a href={u ? "/browse" : "/login"}><span className="btn ghost sm">See more →</span></a>
      </div>
      <div className="grid g3">
        {featured.map((c) => (
          <div key={c.id} className="card" style={{ padding: 0, overflow: "hidden" }}>
            <div style={{ height: 92, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 46, background: "linear-gradient(135deg,#efe9ff,#d6c8f0)" }}>
              {EMO[c.category] || "🎓"}
            </div>
            <div style={{ padding: "14px 18px 18px" }}>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Course Name: </span><b>{c.title}</b></p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Instructor: </span>{c.mentor}</p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Language: </span>{LANGS[c.language] || c.language}</p>
              <p style={{ margin: "3px 0", fontSize: 13 }}><span className="muted">Price: </span><b style={{ color: c.price ? "var(--orange)" : "var(--teal)" }}>{c.price ? "BDT " + c.price : "Free"}</b></p>
              <a href={u ? "/course/" + c.id : "/login"} style={{ display: "block", textAlign: "center", marginTop: 14 }}>
                <span className={"btn block sm " + (c.price ? "pink" : "teal")}>{c.price ? "Buy Now" : "Enroll Now (Free)"}</span>
              </a>
            </div>
          </div>
        ))}
      </div>
      <div className="grid g3" style={{ marginTop: 26 }}>
        <div className="card"><h3>🌍 Multi-language</h3><p className="muted">Full UI in English & Bangla, courses delivered in 14 languages. Your preference is saved to your account.</p></div>
        <div className="card"><h3>🎯 Smart Mentor Match</h3><p className="muted">A ranked mentor engine: skill depth → language fit → teaching quality, with plain-English reasons for every result.</p></div>
        <div className="card"><h3>💳 Complete Learning Loop</h3><p className="muted">Enroll (free or simulated bank payment), learn lessons, pass quizzes, submit assignments, download your certificate.</p></div>
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
      <div className="foot">Skillhub — university SE project rebuilt as a working full-stack product</div>
    </div></div>
  );
}