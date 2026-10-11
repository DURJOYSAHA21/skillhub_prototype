"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Nav from "@/components/Nav";
import { api, getToken, getUser } from "@/lib/api";

const LNAME = { en: "English", bn: "Bangla", hi: "Hindi", ur: "Urdu", ar: "Arabic", es: "Spanish", fr: "French", de: "German", pt: "Portuguese", tl: "Tagalog", id: "Indonesian", tr: "Turkish", ne: "Nepali", fa: "Farsi" };
const STARS = [1, 2, 3, 4, 5];

export default function CoursePage() {
  const { id } = useParams();
  const [c, setC] = useState(null), [err, setErr] = useState(""), [msg, setMsg] = useState("");
  const [pay, setPay] = useState(0);
  const [pm, setPm] = useState({ method: "UCB", card_number: "", pin: "", otp: "" });
  const [devOtp, setDevOtp] = useState("");
  const [enrolled, setEnrolled] = useState(false);
  const [reviews, setReviews] = useState([]);
  const [myReview, setMyReview] = useState(null);
  const [rev, setRev] = useState({ rating: 5, comment: "" });
  const [wish, setWish] = useState(false);
  const u = getUser();
  useEffect(() => {
    if (!getToken()) { window.location = "/login"; return; }
    load();
    async function load() {
      try {
        const d = await api("/courses?q=");
        setC(d.courses.find((x) => String(x.id) === String(id)));
        const rv = await api("/courses/" + id + "/reviews");
        setReviews(rv.reviews);
        const wl = await api("/wishlist");
        setWish(wl.courses.some(w => String(w.course_id) === String(id)));
        if (u && u.role === "learner") {
          const my = await api("/my/courses");
          setEnrolled(my.courses.some((x) => String(x.course_id) === String(id)));
          const mine = rv.reviews.find(r => r.name === u.name);
          if (mine) setMyReview(mine);
        }
      } catch (x) { setErr(x.message); }
    }
  }, [id]);
  async function freeEnroll() {
    setErr(""); setMsg("");
    try { setMsg((await api("/enroll/free", { method: "POST", body: { course_id: Number(id) } })).message); setEnrolled(true); }
    catch (x) { if (x.message.includes("Already enrolled")) { setEnrolled(true); setMsg("You are already enrolled - happy learning!"); } else setErr(x.message); }
  }
  async function startPay(e) {
    e.preventDefault(); setErr("");
    try {
      const d = await api("/pay/start", { method: "POST",
        body: { course_id: Number(id), method: pm.method, card_number: pm.card_number, pin: pm.pin } });
      setDevOtp(d.dev_otp || ""); setPay(2);
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
  async function toggleWish() {
    try { const r = await api("/wishlist/" + id, { method: "POST" }); setWish(r.saved); } catch (e) {}
  }
  async function saveReview(e) {
    e.preventDefault(); setErr("");
    try {
      const d = await api("/courses/" + id + "/reviews", { method: "POST", body: rev });
      setMsg(d.message); setMyReview({ name: u.name, rating: rev.rating, comment: rev.comment, date: "today" });
      const rv = await api("/courses/" + id + "/reviews"); setReviews(rv.reviews);
      setC(x => x ? { ...x, rating: d.rating, reviews: d.reviews } : x);
    } catch (x) { setErr(x.message); }
  }
  if (!c) return <div><Nav /><div className="wrap">Loading...</div></div>;
  return (
    <div><Nav /><div className="wrap">
      <a href="/browse" className="muted">&lt;- Back to browse</a>
      <div className="panel">
        <span className="pill">{c.category}</span> <span className="pill">taught in {LNAME[c.language] || c.language}</span>
        <span className={"badge " + (c.status === "published" ? "b-pub" : "b-pend")}>{c.status}</span>
        <button onClick={toggleWish} title={wish ? "Remove from saved" : "Save for later"}
          style={{ float: "right", background: "none", border: "none", fontSize: 20, cursor: "pointer", width: "auto" }}>
          {wish ? "❤️" : "🤍"}</button>
        <h2 style={{ margin: "10px 0 4px" }}>{c.title}</h2>
        <p className="muted">by <a href={`/mentor/${c.mentor_id}`} style={{ fontWeight: 600 }}>{c.mentor}</a> - ★ {c.rating} ({c.reviews} reviews) - {c.duration_hours}h</p>
        <p>{c.description}</p>
        <b style={{ color: c.price ? "var(--orange)" : "var(--teal)", fontSize: 20 }}>{c.price ? "BDT " + c.price : "FREE"}</b>
        <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
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
          {c.lessons.map((l) => <div key={l.id} className="lic"><span className="chip chip-open">{l.position}</span> {l.title}
            {l.notes && <span className="pill" style={{ marginLeft: 8 }}>notes / video</span>}</div>)}
        </div>
        <div className="card"><h3>Assessments</h3>
          {c.quizzes.map((qz) => <p key={qz.id} className="muted">📝 Quiz: {qz.title}</p>)}
          {c.assignments.map((a) => <p key={a.id} className="muted">📌 Assignment: {a.title}</p>)}
          {!c.quizzes.length && !c.assignments.length && <p className="muted">No assessments yet.</p>}
        </div>
      </div>
      <div className="card">
        <h3>Ratings &amp; Reviews ({reviews.length})</h3>
        {reviews.length === 0 && <p className="muted">No written reviews yet - be the first!</p>}
        {reviews.map(r => (
          <div key={r.id} style={{ padding: "10px 0", borderBottom: "1px solid var(--line)" }}>
            <b>{"★".repeat(r.rating)}{"☆".repeat(5 - r.rating)}</b> <span className="muted" style={{ fontSize: 12 }}>{r.name} · {r.date}</span>
            <p style={{ margin: "4px 0 0" }}>{r.comment}</p>
          </div>))}
        {enrolled && !myReview && u && u.role === "learner" && (
          <form onSubmit={saveReview} style={{ marginTop: 14, background: "#faf8ff", borderRadius: 14, padding: 14 }}>
            <b>Write your review</b>
            <div style={{ display: "flex", gap: 6, margin: "8px 0" }}>
              {STARS.map(n => (
                <button key={n} type="button" onClick={() => setRev({ ...rev, rating: n })}
                  style={{ background: "none", border: "none", fontSize: 24, cursor: "pointer", width: "auto",
                    color: n <= rev.rating ? "var(--orange)" : "#c9c9d4" }}>★</button>))}
            </div>
            <textarea rows={2} placeholder="How was the course?" value={rev.comment}
              onChange={(e) => setRev({ ...rev, comment: e.target.value })} />
            <button className="btn sm" style={{ marginTop: 8 }}>Submit Review</button>
          </form>)}
        {myReview && <p className="ok" style={{ marginTop: 10 }}>Your review: {"★".repeat(myReview.rating)} - {myReview.comment || "no comment"}</p>}
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
              </form>)}
            {pay === 2 && (
              <form onSubmit={confirmPay}>
                {devOtp ? <p className="ok">Bank (simulated) sent OTP. Dev OTP: <b>{devOtp}</b></p>
                         : <p className="ok">The bank sent an OTP to your registered email.</p>}
                <label>OTP</label>
                <input value={pm.otp} onChange={(e) => setPm({ ...pm, otp: e.target.value })} maxLength={6} />
                <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
                  <button className="btn green" style={{ flex: 1 }}>Confirm Payment · BDT {c.price}</button>
                  <button type="button" className="btn gray" style={{ flex: "0 0 auto" }} onClick={() => setPay(0)}>Cancel</button>
                </div>
              </form>)}
          </div>
        </div>)}
    </div></div>
  );
}