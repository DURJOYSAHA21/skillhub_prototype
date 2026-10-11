"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Nav from "@/components/Nav";
import { api, getToken } from "@/lib/api";

export default function MentorPage() {
  const { id } = useParams();
  const [m, setM] = useState(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api("/mentors/" + id).then(setM).catch((x) => setErr(x.message));
  }, [id]);
  if (!m) return (<div><Nav /><div className="wrap">
    <p className="muted">{err || "Loading mentor profile..."}</p>
    {!err && <div className="panel"><h2>Please wait</h2><p className="muted">Fetching the instructor profile.</p></div>}
  </div></div>);
  const stars = Math.round(m.rating || 0);
  return (
    <div><Nav /><div className="wrap">
      <a href="/browse" className="muted">&lt;- Back to browse</a>
      <div className="panel">
        <span className="pill">Verified instructor</span>
        <h2 style={{ margin: "10px 0 4px" }}>{m.name}</h2>
        <p className="muted" style={{ margin: 0 }}>{m.headline || "SkillHub mentor"}</p>
        <p style={{ marginTop: 10 }}>
          {"★".repeat(stars)}{"☆".repeat(5 - stars)} <b>{m.rating}</b>
          <span className="muted"> ({m.reviews} reviews)</span>
          {m.country && <> - {m.country}</>}
        </p>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
          <a href={"/chat?to=" + m.id}><button className="btn teal">Message {m.name.split(" ")[0]}</button></a>
          <a href="/browse"><button className="btn ghost">Browse the catalog</button></a>
          {!getToken() && <a href="/login" className="muted" style={{ alignSelf: "center" }}>Login to message</a>}
        </div>
      </div>
      <div className="grid g2">
        <div className="card">
          <h3>Courses by {m.name} ({m.courses.length})</h3>
          {m.courses.map((c) => (
            <a key={c.id} href={"/course/" + c.id} className="lic" style={{ textDecoration: "none" }}>
              <span className="chip chip-open">{c.language}</span>
              <span style={{ flex: 1 }}>{c.title}</span>
              <span className="pill">{c.price ? "BDT " + c.price : "FREE"}</span>
            </a>
          ))}
          {!m.courses.length && <p className="muted">No published courses yet - this mentor is still teaching one-on-one.</p>}
        </div>
        <div>
          <div className="card" style={{ marginBottom: 18 }}>
            <h3>Skills</h3>
            {m.skills.map((sk, i) => (
              <div key={i} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <b>{sk.skill}</b><span className="muted">{sk.years} yrs</span>
                </div>
                <div className="bar"><i style={{ width: Math.min(100, sk.proficiency * 10) + "%" }} /></div>
              </div>
            ))}
            {!m.skills.length && <p className="muted">No skills listed yet.</p>}
          </div>
          <div className="card">
            <h3>Languages</h3>
            {m.languages.length ? m.languages.map((l, i) => <span key={i} className="chip" style={{ marginRight: 6 }}>{l}</span>)
              : <p className="muted">No languages listed yet.</p>}
          </div>
        </div>
      </div>
    </div></div>
  );
}