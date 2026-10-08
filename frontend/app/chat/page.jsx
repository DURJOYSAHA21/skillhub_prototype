"use client";
import { useEffect, useRef, useState } from "react";
import Nav from "../../components/Nav";
import { api, getToken, getUser, API } from "../../lib/api";

export default function ChatPage() {
  const [threads, setThreads] = useState([]), [peer, setPeer] = useState(null);
  const [msgs, setMsgs] = useState([]), [text, setText] = useState("");
  const [err, setErr] = useState("");
  const me = getUser();
  const lastId = useRef(0), boxRef = useRef(null);
  useEffect(() => {
    if (!getToken()) { window.location = "/login"; return; }
    const to = new URLSearchParams(window.location.search).get("to");
    refreshThreads();
    if (to) select(Number(to));
  }, []);
  useEffect(() => {
    if (!peer) return;
    const iv = setInterval(poll, 2500);
    return () => clearInterval(iv);
  }, [peer]);
  async function refreshThreads() {
    try { setThreads((await api("/chat/threads")).threads); } catch (x) {}
  }
  async function select(pid) {
    setPeer(pid); lastId.current = 0; setMsgs([]);
    poll();
  }
  async function poll() {
    if (!peer) return;
    try {
      const d = await api(`/chat/${peer}?since_id=${lastId.current}`);
      if (d.messages.length) {
        lastId.current = d.messages[d.messages.length - 1].id;
        setMsgs((m) => [...m, ...d.messages]);
        setTimeout(() => boxRef.current?.scrollTo(0, boxRef.current.scrollHeight), 50);
      }
    } catch (x) { setErr(x.message); }
  }
  async function send(e) {
    e.preventDefault(); setErr("");
    if (!text.trim()) return;
    try {
      const fd = new FormData(); fd.append("text", text);
      await api("/chat/" + peer, { method: "POST", body: fd });
      setText(""); poll(); refreshThreads();
    } catch (x) { setErr(x.message); }
  }
  return (
    <div><Nav /><div className="wrap">
      <h2>Messages</h2>
      {err && <p className="err">{err}</p>}
      <div className="grid g2" style={{ gridTemplateColumns: "1fr 2fr" }}>
        <div className="card threads">
          <h4>Conversations</h4>
          {threads.map((t) => (
            <div key={t.user_id} className={"trow" + (peer === t.user_id ? " on" : "")} onClick={() => select(t.user_id)}>
              <b>{t.name}</b> <span className="pill">{t.role}</span>
              <p className="muted" style={{ margin: 2 }}>{t.last} · {t.last_ts}</p>
            </div>
          ))}
          {!threads.length && <p className="muted">No conversations yet. Use "Find a Mentor" or a course page to message someone.</p>}
        </div>
        <div className="card">
          {peer ? <>
            <div className="conv" ref={boxRef}>
              {msgs.map((m) => (
                <div key={m.id} className={"bub " + (m.from === me?.id ? "me" : "you")}>
                  {m.text}{m.file && <> 📎 <a href={API + "/files/" + m.file}>attachment</a></>}
                  <div className="muted" style={{ fontSize: 10 }}>{m.ts}</div>
                </div>
              ))}
              {!msgs.length && <p className="muted">Say hello 👋</p>}
            </div>
            <form onSubmit={send} style={{ display: "flex", gap: 8 }}>
              <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Type a message..." />
              <button className="btn">Send</button>
            </form>
          </> : <p className="muted">Select a conversation on the left.</p>}
        </div>
      </div>
    </div></div>
  );
}
