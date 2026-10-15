"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

/* SkillHub helper bot - grounded in live platform data, no external API key. */
export default function Chatbot() {
  const [open, setOpen] = useState(false);
  const [log, setLog] = useState([]);
  const [chips, setChips] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const scroller = useRef(null);

  async function ask(q) {
    const msg = (q || text).trim();
    if (!msg || busy) return;
    setText("");
    setBusy(true);
    setLog((l) => [...l, { me: true, text: msg }]);
    try {
      const d = await api("/bot/ask", { method: "POST", body: { message: msg } });
      setLog((l) => [...l, { me: false, text: d.reply, actions: d.actions || [] }]);
      setChips(d.chips || []);
    } catch (e) {
      setLog((l) => [...l, { me: false, text: "Sorry - I could not reach the server (" + e.message + "). Try again in a moment." }]);
    } finally {
      setBusy(false);
    }
  }

  async function boot() {
    setLog([{ me: false, text: "Hi! I am SkillBot. Ask me about courses, mentors, payments, your progress or how to fix an account problem." }]);
    try { const d = await api("/bot/starters"); setChips(d.chips || []); } catch (e) {}
  }

  useEffect(() => { if (open && !log.length) boot(); }, [open]);
  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight;
  }, [log, busy]);

  return (
    <>
      <button onClick={() => setOpen(!open)}
        style={{ position: "fixed", right: 18, bottom: 18, zIndex: 60, width: 56, height: 56,
          borderRadius: "50%", border: "none", cursor: "pointer", background: "#6c63ff",
          color: "#fff", fontSize: 24, boxShadow: "0 10px 26px rgba(60,30,120,.45)" }}
        title="Ask SkillBot">
        {open ? "×" : "💬"}
      </button>
      {open && (
        <div style={{ position: "fixed", right: 18, bottom: 84, zIndex: 60, width: "min(360px, calc(100vw - 36px))",
          background: "#fff", borderRadius: 20, boxShadow: "0 22px 50px rgba(40,20,80,.35)",
          display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "12px 16px", background: "#6c63ff", color: "#fff", fontWeight: 800, fontSize: 14 }}>
            SkillBot <span style={{ fontWeight: 500, opacity: .85, fontSize: 12 }}>· answers from your real SkillHub data</span>
          </div>
          <div ref={scroller} style={{ padding: 12, maxHeight: "min(46vh, 340px)", overflowY: "auto",
            display: "flex", flexDirection: "column", gap: 8, background: "#f6f4fd" }}>
            {log.map((m, i) => (
              <div key={i}>
                <div className={"bub " + (m.me ? "me" : "you")}>{m.text}</div>
                {m.actions && m.actions.length > 0 && (
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 6,
                    justifyContent: m.me ? "flex-end" : "flex-start" }}>
                    {m.actions.map((a) => (
                      <a key={a.label + a.href} href={a.href} className="chip"
                        style={{ background: "#fff", fontWeight: 700 }}>{a.label}</a>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {busy && <div className="bub you">Thinking…</div>}
          </div>
          {chips.length > 0 && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap", padding: "8px 12px 0" }}>
              {chips.map((c) => <button key={c} className="chip" onClick={() => ask(c)}>{c}</button>)}
            </div>
          )}
          <form style={{ display: "flex", gap: 8, padding: 12 }}
            onSubmit={(e) => { e.preventDefault(); ask(); }}>
            <input value={text} onChange={(e) => setText(e.target.value)}
              placeholder="Type your question…" style={{ flex: 1 }} />
            <button className="btn sm" type="submit" disabled={busy}>Send</button>
          </form>
        </div>
      )}
    </>
  );
}