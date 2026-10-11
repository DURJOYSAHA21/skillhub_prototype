"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Nav from "@/components/Nav";
import { api, getToken, API } from "@/lib/api";

function ytEmbed(url) {
  const m = (url || "").match(/(?:v=|youtu\.be\/|embed\/)([\w-]{6,})/);
  return m ? "https://www.youtube.com/embed/" + m[1] : url;
}

export default function LearnPage() {
  const { id } = useParams();
  const [d, setD] = useState(null), [err, setErr] = useState(""), [msg, setMsg] = useState("");
  const [quiz, setQuiz] = useState(null), [ans, setAns] = useState({}), [res, setRes] = useState(null);
  const [file, setFile] = useState(null), [comment, setComment] = useState("");
  const [open, setOpen] = useState(null);
  useEffect(() => {
    if (!getToken()) { window.location = "/login"; return; }
    load();
  }, [id]);
  async function load() {
    try { setD(await api("/courses/" + id + "/learn")); } catch (x) { setErr(x.message); }
  }
  async function done(lid) {
    setErr("");
    try { const r = await api("/lessons/" + lid + "/complete", { method: "POST" });
      setMsg(r.message + " Progress: " + r.progress + "%"); load(); }
    catch (x) { setErr(x.message); }
  }
  async function openQuiz(qid) {
    setErr(""); setRes(null);
    try { setQuiz(await api("/quizzes/" + qid)); setAns({}); } catch (x) { setErr(x.message); }
  }
  async function submitQuiz() {
    setErr("");
    try {
      const r = await api("/quizzes/" + quiz.id + "/submit", { method: "POST", body: { answers: ans } });
      setRes(r); setMsg("Score: " + r.score_percent + "% - " + (r.passed ? "PASSED" : "not passed")); load();
    } catch (x) { setErr(x.message); }
  }
  async function submitAssign(aid, draft) {
    setErr("");
    const fd = new FormData();
    fd.append("comment", comment); fd.append("draft", String(draft));
    if (file) fd.append("file", file);
    try { setMsg((await api("/assignments/" + aid + "/submit", { method: "POST", body: fd })).message); }
    catch (x) { setErr(x.message); }
  }
  async function openPdf(path) {
    const r = await fetch(API + path, { headers: { Authorization: "Bearer " + getToken() } });
    if (!r.ok) { setErr((await r.json().catch(() => ({}))).detail || "Not available yet."); return; }
    const b = await r.blob();
    window.open(URL.createObjectURL(b));
  }
  if (!d) return <div><Nav /><div className="wrap">{err || "Loading..."}</div></div>;
  return (
    <div><Nav /><div className="wrap">
      <a href="/browse" className="muted">&lt;- Browse</a>
      <div className="panel">
        <h2 style={{ margin: "0 0 8px" }}>{d.title}</h2>
        <div className="bar"><i style={{ width: d.progress + "%" }} /></div>
        <p className="muted">{d.progress}% complete {d.completed && "- COMPLETED"}</p>
        {msg && <p className="ok">{msg}</p>}
        {err && <p className="err">{err}</p>}
        {d.completed && <button className="btn green" onClick={() => openPdf("/courses/" + id + "/certificate")}>🎓 Download Certificate (PDF)</button>}
      </div>
      <div className="grid g2">
        <div className="card">
          <h3>Lessons</h3>
          {d.lessons.map((l) => (
            <div key={l.id} className={"lic" + (l.done ? " done" : "")} style={{ flexWrap: "wrap" }}>
              <span className={"chip " + (l.done ? "chip-completed" : "chip-open")}>{l.position}</span>
              <span style={{ flex: 1, cursor: "pointer" }} onClick={() => setOpen(open === l.id ? null : l.id)}>
                {l.title}
                {(l.content || l.video_url) &&
                  <span className="pill" style={{ marginLeft: 6 }}>{open === l.id ? "hide" : "view lesson"}</span>}
                {l.file && <> <a className="muted" href={API + "/files/" + l.file}
                  onClick={(e) => e.stopPropagation()}>(file)</a></>}
              </span>
              {!l.done && <button className="btn sm teal" onClick={() => done(l.id)}>Mark complete</button>}
              {l.done && <span className="chip chip-completed">Completed</span>}
              {open === l.id && (
                <div style={{ width: "100%", background: "#faf8ff", borderRadius: 14, padding: 14, marginTop: 8 }}>
                  {l.video_url &&
                    <div style={{ position: "relative", paddingTop: "52%", borderRadius: 12, overflow: "hidden", background: "#111", marginBottom: 10 }}>
                      <iframe src={ytEmbed(l.video_url)} title={l.title} allowFullScreen
                        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", border: 0 }} />
                    </div>}
                  <p style={{ whiteSpace: "pre-wrap", margin: 0, fontSize: 14 }}>
                    {l.content || l.description || "No written notes for this lesson - follow the material and the video."}
                  </p>
                  {l.file && <p style={{ margin: "8px 0 0" }}>
                    <a href={API + "/files/" + l.file}>Download lesson file</a></p>}
                </div>)}
            </div>
          ))}
        </div>
        <div className="card">
          <h3>Quiz</h3>
          {!quiz && d.quizzes.map((qz) => (
            <p key={qz.id}><button className="chip" onClick={() => openQuiz(qz.id)}>Start: {qz.title} ({qz.time_limit_min} min, pass {qz.passing_score}%)</button></p>
          ))}
          {quiz && (
            <div>
              <h4>{quiz.title}</h4>
              {quiz.questions.map((q, i) => (
                <div key={q.id} style={{ marginBottom: 12 }}>
                  <p><b>Q{i + 1}.</b> {q.text}</p>
                  {q.options.map((o, j) => (
                    <label key={j} style={{ display: "inline-flex", gap: 6, margin: "2px 12px 2px 0", color: "var(--ink)" }}>
                      <input type="radio" style={{ width: "auto" }} name={"q" + q.id} checked={ans[String(q.id)] === j}
                        onChange={() => setAns({ ...ans, [String(q.id)]: j })} /> {o}
                    </label>
                  ))}
                  {res && <p className={res.results.find((x) => x.question_id === q.id)?.got ? "ok" : "err"}>
                    {res.results.find((x) => x.question_id === q.id)?.got ? "Correct" : "Answer was " + (res.results.find((x) => x.question_id === q.id)?.correct + 1)}</p>}
                </div>
              ))}
              {!res && <button className="btn" onClick={submitQuiz}>Submit Answers</button>}
              {res && <p className={res.passed ? "ok" : "err"}>Result: {res.score_percent}% ({res.attempts_used}/{quiz.max_attempts} attempts)</p>}
            </div>
          )}
        </div>
      </div>
      <div className="card" style={{ marginTop: 14 }}>
        <h3>Assignments</h3>
        {d.assignments.map((a) => (
          <div key={a.id} className="panel" style={{ background: "#f6f3fd" }}>
            <b>{a.title}</b> {a.due && <span className="muted"> - due {a.due}</span>}
            <p className="muted">{a.instructions}</p>
            <div className="grid g2">
              <div><label>Your comment</label><input value={comment} onChange={(e) => setComment(e.target.value)} /></div>
              <div><label>Attach file</label><input type="file" onChange={(e) => setFile(e.target.files[0])} /></div>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <button className="btn sm ghost" onClick={() => submitAssign(a.id, true)}>Save Draft</button>
              <button className="btn sm" onClick={() => submitAssign(a.id, false)}>Submit</button>
            </div>
          </div>
        ))}
        {!d.assignments.length && <p className="muted">No assignments for this course.</p>}
      </div>
    </div></div>
  );
}
