"use client";
import { useEffect, useState } from "react";
import Nav from "../../components/Nav";
import { api, getToken } from "../../lib/api";

export default function MatchPage() {
  const [meta, setMeta] = useState(null), [skill, setSkill] = useState("");
  const [picked, setPicked] = useState([]), [data, setData] = useState(null);
  const [err, setErr] = useState(""), [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!getToken()) { window.location = "/login"; return; }
    api("/meta").then(setMeta).catch((x) => setErr(x.message));
  }, []);
  function toggle(code) {
    setPicked(picked.includes(code) ? picked.filter((c) => c !== code) : [...picked, code]);
  }
  async function search(e) {
    e.preventDefault(); setErr(""); setLoading(true);
    try { setData(await api("/match?skill=" + encodeURIComponent(skill) + "&langs=" + picked.join(","))); }
    catch (x) { setErr(x.message); setData(null); }
    setLoading(false);
  }
  const ln = (c) => (meta ? meta.languages.find((l) => l.code === c)?.name || c : c);
  return (
    <div><Nav /><div className="wrap">
      <h2>Find a Mentor <span className="muted">- ranked by skill depth, language fit & teaching quality</span></h2>
      <form className="panel" onSubmit={search}>
        <label>Skill (try "vlookup", "ethical hacking", "spoken english")</label>
        <input value={skill} onChange={(e) => setSkill(e.target.value)} placeholder="What do you want to learn?" />
        <label>Languages you speak (click in order of preference)</label>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {meta && meta.languages.map((l) => (
            <button type="button" key={l.code} className={"chip" + (picked.includes(l.code) ? " on" : "")}
              onClick={() => toggle(l.code)}>
              {l.name}{picked.includes(l.code) && " #" + (picked.indexOf(l.code) + 1)}
            </button>
          ))}
        </div>
        <button className="btn" style={{ marginTop: 12 }} disabled={loading}>{loading ? "Matching..." : "Match Mentors"}</button>
        {err && <p className="err">{err}</p>}
      </form>
      {data && (
        <div>
          <p className="ok">"{data.query}" resolved to <b>{data.resolved_skill}</b> (via {data.resolution_method})
            {data.languages.length > 0 && <> · languages: {data.languages.map(ln).join(" > ")}</>}</p>
          {data.results.map((r, i) => (
            <div key={r.mentor_id} className="card" style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <b>#{i + 1} {r.name}</b><span style={{ color: "var(--acc)", fontWeight: 800 }}>{r.match_percent}%</span>
              </div>
              <p className="muted">{r.headline} · {r.country} · ★ {r.rating} ({r.reviews})</p>
              <div className="bar" style={{ marginBottom: 4 }}><i style={{ width: r.breakdown.skill * 100 + "%" }} /></div>
              <div className="bar" style={{ marginBottom: 4 }}><i style={{ width: r.breakdown.language * 100 + "%", background: "linear-gradient(90deg,#38bdf8,#818cf8)" }} /></div>
              <div className="bar"><i style={{ width: r.matched_language === "-" ? 0 : r.breakdown.quality * 100 + "%" }} /></div>
              <p className="muted">skill {r.breakdown.skill} · language {r.breakdown.language} · quality {r.breakdown.quality}
                {r.matched_language !== "-" && <> · teaches you in <b>{r.matched_language}</b></>}</p>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {r.reasons.map((x, j) => <span key={j} className="pill">{x}</span>)}
              </div>
              <a href={`/chat?to=${r.mentor_id}`}><button className="btn sm ghost" style={{ marginTop: 8 }}>Message {r.name.split(" ")[0]}</button></a>
            </div>
          ))}
          {!data.results.length && <div className="panel"><p>No mentor speaks your language for this skill yet — try adding English.</p></div>}
        </div>
      )}
    </div></div>
  );
}
