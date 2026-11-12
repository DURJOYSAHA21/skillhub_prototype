"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Nav from "../../components/Nav";
import { useLang } from "../../components/LangContext";
import { api, getToken, getUser, API } from "../../lib/api";

export default function ChatPage() {
  const { tr } = useLang();
  const [threads, setThreads] = useState([]);
  const [peer, setPeer] = useState(null);           // id of the open conversation
  const [peerInfo, setPeerInfo] = useState(null);   // { id, name, role }
  const [msgs, setMsgs] = useState([]);
  const [text, setText] = useState(""), [file, setFile] = useState(null);
  const [err, setErr] = useState(""), [sending, setSending] = useState(false);
  const [me, setMe] = useState(null);
  // The open conversation and the newest message id live in refs so that every
  // poll, including one still in flight from before a switch, sees the current value.
  const peerRef = useRef(null), lastId = useRef(0);
  const boxRef = useRef(null), fileRef = useRef(null);

  const refreshThreads = useCallback(async () => {
    try { setThreads((await api("/chat/threads")).threads); } catch (x) { /* next tick retries */ }
  }, []);

  const poll = useCallback(async () => {
    const pid = peerRef.current;
    if (!pid) return;
    try {
      const d = await api(`/chat/${pid}?since_id=${lastId.current}`);
      if (peerRef.current !== pid) return;          // switched conversation while waiting
      setPeerInfo(d.peer);
      if (d.messages.length) {
        lastId.current = Math.max(lastId.current, d.messages[d.messages.length - 1].id);
        setMsgs((old) => {
          const seen = new Set(old.map((m) => m.id));
          return [...old, ...d.messages.filter((m) => !seen.has(m.id))];
        });
      }
    } catch (x) { if (peerRef.current === pid) setErr(x.message); }
  }, []);

  const select = useCallback((pid, info) => {
    peerRef.current = pid;
    lastId.current = 0;
    setPeer(pid); setPeerInfo(info || null); setMsgs([]); setErr("");
    setThreads((ts) => ts.map((t) => (t.user_id === pid ? { ...t, unread: 0 } : t)));
    window.history.replaceState(null, "", "/chat?to=" + pid);
    poll();
  }, [poll]);

  useEffect(() => {
    if (!getToken()) { window.location = "/login"; return; }
    const u = getUser();
    setMe(u);
    refreshThreads();
    const to = Number(new URLSearchParams(window.location.search).get("to"));
    if (to && to !== u?.id) select(to);
    const msgTimer = setInterval(poll, 2500);
    const listTimer = setInterval(refreshThreads, 10000);
    return () => { clearInterval(msgTimer); clearInterval(listTimer); };
  }, [poll, refreshThreads, select]);

  useEffect(() => {
    boxRef.current?.scrollTo(0, boxRef.current.scrollHeight);
  }, [msgs.length]);

  async function send(e) {
    e.preventDefault(); setErr("");
    if ((!text.trim() && !file) || !peer || sending) return;
    setSending(true);
    try {
      const fd = new FormData();
      fd.append("text", text);
      if (file) fd.append("file", file);
      await api("/chat/" + peer, { method: "POST", body: fd });
      setText(""); setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      await poll();
      refreshThreads();
    } catch (x) { setErr(x.message); }
    finally { setSending(false); }
  }

  const known = threads.find((t) => t.user_id === peer);
  const head = peerInfo || (known && { name: known.name, role: known.role });
  return (
    <div><Nav /><div className="wrap">
      <h2>{tr("chatTitle")}</h2>
      {err && <p className="err">{err}</p>}
      <div className="grid g2" style={{ gridTemplateColumns: "1fr 2fr" }}>
        <div className="card threads">
          <h4>{tr("conversations")}</h4>
          {threads.map((t) => (
            <div key={t.user_id} className={"trow" + (peer === t.user_id ? " on" : "")}
              onClick={() => select(t.user_id, { id: t.user_id, name: t.name, role: t.role })}>
              <b>{t.name}</b> <span className="pill">{t.role}</span>
              {t.unread > 0 && peer !== t.user_id &&
                <span className="pill" style={{ background: "var(--indigo)", color: "#fff", marginInlineStart: 4 }}>{t.unread}</span>}
              <p className="muted" style={{ margin: 2 }}>{t.last} · {t.last_ts}</p>
            </div>
          ))}
          {!threads.length && <p className="muted">{tr("noConversations")}</p>}
        </div>
        <div className="card">
          {peer ? <>
            {head && <h4 style={{ marginTop: 0 }}>{head.name} <span className="pill">{head.role}</span></h4>}
            <div className="conv" ref={boxRef}>
              {msgs.map((m) => (
                <div key={m.id} className={"bub " + (m.from === me?.id ? "me" : "you")}>
                  {m.text}{m.file && <> 📎 <a href={API + "/files/" + m.file} target="_blank" rel="noopener noreferrer">{tr("attachment")}</a></>}
                  <div className="muted" style={{ fontSize: 10 }}>{m.ts}</div>
                </div>
              ))}
              {!msgs.length && <p className="muted">{tr("sayHello")}</p>}
            </div>
            <form onSubmit={send} style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input value={text} onChange={(e) => setText(e.target.value)} placeholder={tr("typeMessage")} />
              <input ref={fileRef} type="file" hidden onChange={(e) => setFile(e.target.files[0] || null)} />
              <button type="button" className="btn ghost" title={tr("attachFile")} aria-label={tr("attachFile")}
                onClick={() => fileRef.current?.click()}>📎</button>
              <button className="btn" disabled={sending}>{tr("sendMsg")}</button>
            </form>
            {file && <p className="muted" style={{ fontSize: 12, margin: "6px 0 0" }}>📎 {file.name}</p>}
          </> : <p className="muted">{tr("pickConversation")}</p>}
        </div>
      </div>
    </div></div>
  );
}
