"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Nav from "@/components/Nav";
import { api, getToken, getUser } from "@/lib/api";

const LNAME = { en: "English", bn: "Bangla", hi: "Hindi", ur: "Urdu", ar: "Arabic", es: "Spanish", fr: "French", de: "German", pt: "Portuguese", tl: "Tagalog", id: "Indonesian", tr: "Turkish", ne: "Nepali", fa: "Farsi" };

export default function CoursePage() {
  const { id } = useParams();
  const [c, setC] = useState(null), [err, setErr] = useState(""), [msg, setMsg] = useState("");
  const [pay, setPay] = useState(0);
  const [pm, setPm] = useState({ method: "UCB", card_number: "", pin: "", otp: "" });
  const [devOtp, setDevOtp] = useState("");
  const [enrolled, setEnrolled] = useState(false);
  const u = getUser();
  useEffect(() => {
    if (!getToken()) { window.location = "/login"; return; }
    load();
    async function load() {
      try {
        const d = await api("/courses?q=");
        setC(d.courses.find((x) => String(x.id) === String(id)));
        if (u && u.role === "learner") {
          const my = await api("/my/courses");
          setEnrolled(my.courses.some((x) => String(x.course_id) === String(id)));
        }
      } catch (x) { setErr(x.message); }
    }
  }, [id]);
  async function freeEnroll() {
    setErr(""); setMsg("");
    try { setMsg((await api("/enroll/free", { method: "POST", body: { course_id: Number(id) } })).message); setEnrolled(true); }
    catch (x) { setErr(x.message); }
  }
  async function startPay(e) {
    e.preventDefault(); setErr("");
    try {
      const d = await api("/pay/start", { method: "POST",
        body: { course_id: Number(id), method: pm.method, card_number: pm.card_number, pin: pm.pin } });
      setDevOtp(d.dev_otp); setPay(2);
    } catch (x) { setErr(x.message); }
  }
  async function confirmPay(e) {
    e.preventDefault(); setErr("");
    try {
      const d = await api("/pay/confirm", { method: "POST",
        body: { course_id: Number(id), otp: pm.otp, method: pm.method, card_number: pm.card_number } });
      setMsg(d.message + " Receipt: " + d.receipt_no); setPay(0); setEnrolled(true);
    } catch (x) { setErr(x.message); setPay(1); }
  }
  if (!c) return <div><Nav /><div className="wrap">Loading...</div></div>;
  return (
    <div><Nav /><div className="wrap">
      <a href="/browse" className="muted">&lt;- Back to browse</a>
      <div className="panel">
        <span className="pill">{c.category}</span> <span className="pill">taught in {LNAME[c.language] || c.language}</span>
        <span className={"badge " + (c.status === "published" ? "b-pub" : "b-pend")}>{c.status}</span>
        <h2 style={{ margin: "10px 0 4px" }}>{c.title}</h2>
        <p className="muted">by <a href={`/chat?to=${c.mentor_id}`}>{c.mentor}</a> - rating {c.rating} ({c.reviews} reviews) - {c.duration_hours}h</p>
        <p>{c.description}</p>
        <b style={{ color: c.price ? "var(--orange)" : "var(--teal)", fontSize: 20 }}>{c.price ? "BDT " + c.price : "FREE"}</b>
        <div style={{ marginTop: 14, display: "flex", gap: 10 }}>
          {enrolled ? <a href={`/learn/${c.id}`}><button className="btn green">Continue Learning →</button></a> :
            u && u.role === "learner" ? <>
              {c.price === 0 ? <button className="btn teal" onClick={freeEnroll}>Enroll Now (Free)</button> :
                <button className="btn pink" onClick={() => setPay(1)}>Buy Now</button>}
            </> : <span className="muted">Login as a learner to enroll.</span>}
          <a href={`/chat?to=${c.mentor_id}`}><button className="btn ghost">Ask mentor</button></a>
        </div>
        {msg && <p className="ok">{msg}</p>}
        {err && <p className="err">{err}</p>}
      </div>
      <div className="grid g2">
        <div className="card"><h3>Lessons ({c.lessons.length})</h3>
          {c.lessons.map((l) => <div key={l.id} className="lic"><span className="chip chip-open">{l.position}</span> {l.title}</div>)}
        </div>
        <div className="card"><h3>Assessments</h3>
          {c.quizzes.map((qz) => <p key={qz.id} className="muted">📝 Quiz: {qz.title}</p>)}
          {c.assignments.map((a) => <p key={a.id} className="muted">📌 Assignment: {a.title}</p>)}
          {!c.quizzes.length && !c.assignments.length && <p className="muted">No assessments yet.</p>}
        </div>
      </div>
      {pay > 0 && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(24,12,44,.55)", backdropFilter: "blur(3px)", zIndex: 60, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}>
          <div className="panel" style={{ width: 460, maxWidth: "100%", margin: 0, position: "relative" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ margin: 0, color: "var(--red)" }}>Payment Details</h3>
              <button onClick={() => setPay(0)} style={{ background: "none", border: "none", fontSize: 20, color: "var(--mut)", cursor: "pointer", width: "auto" }}>✕</button>
            </div>
            <div className="step on" style={{ marginTop: 14 }}><span className="dot">1</span> Choose bank &amp; card</div>
            <div className={pay === 2 ? "step on" : "step"}><span className="dot">2</span> Enter OTP</div>
            {pay === 1 && (
              <form onSubmit={startPay}>
                <label>Select Bank</label>
                <select value={pm.method} onChange={(e) => setPm({ ...pm, method: e.target.value })}>
                  {["UCB", "BRAC Bank", "City Bank", "bKash"].map((m) => <option key={m}>{m}</option>)}
                </select>
                <label>Card Number (12-19 digits, any)</label>
                <input value={pm.card_number} onChange={(e) => setPm({ ...pm, card_number: e.target.value })} placeholder="4111111111111234" />
                <label>PIN (4-6 digits)</label>
                <input type="password" value={pm.pin} onChange={(e) => setPm({ ...pm, pin: e.target.value })} />
                <button className="btn block" style={{ marginTop: 14 }}>Request OTP</button>
              </form>
            )}
            {pay === 2 && (
              <form onSubmit={confirmPay}>
                <p className="ok">Bank (simulated) sent OTP. Dev OTP: <b>{devOtp}</b></p>
                <label>OTP</label>
                <input value={pm.otp} onChange={(e) => setPm({ ...pm, otp: e.target.value })} maxLength={6} />
                <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
                  <button className="btn green" style={{ flex: 1 }}>Confirm Payment · BDT {c.price}</button>
                  <button type="button" className="btn" style={{ flex: "0 0 auto" }} onClick={() => setPay(0)}>Cancel</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div></div>
  );
}