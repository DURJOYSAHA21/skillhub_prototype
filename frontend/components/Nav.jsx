"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUser, logout, api, getToken } from "../lib/api";
import { useLang } from "../components/LangContext";
import { LANG_META } from "../lib/i18n";

export default function Nav() {
  const [u, setU] = useState(null);
  const [notifs, setNotifs] = useState([]);
  const [unread, setUnread] = useState(0);
  const [show, setShow] = useState(false);
  const [showLang, setShowLang] = useState(false);
  const router = useRouter();
  const { lang, setLang, tr } = useLang();
  useEffect(() => { setU(getUser()); }, []);
  // Flip between guest and authenticated headers on login/logout without reload.
  useEffect(() => {
    function onAuth() { setU(getUser()); }
    window.addEventListener("sh-auth", onAuth);
    return () => window.removeEventListener("sh-auth", onAuth);
  }, []);
  useEffect(() => {
    if (!u) return;
    let stop = false;
    async function poll() {
      try { const d = await api("/notifications"); if (stop) return;
        setNotifs(d.notifications); setUnread(d.unread); } catch (e) {}
    }
    poll();
    const iv = setInterval(poll, 30000);
    return () => { stop = true; clearInterval(iv); };
  }, [u]);
  const langPop = (
    <div className="panel notifpop" style={{ position: "absolute", right: 0, top: 38, margin: 0,
      zIndex: 50, padding: 8, minWidth: 170, maxHeight: 320, overflow: "auto" }}>
      {Object.keys(LANG_META).map((code) => (
        <div key={code} onClick={() => { setLang(code); setShowLang(false); }}
          style={{ padding: "8px 10px", borderRadius: 8, cursor: "pointer",
            fontWeight: code === lang ? 800 : 500,
            background: code === lang ? "#f1ecff" : "transparent", fontSize: 14 }}>
          {LANG_META[code].native} <span className="muted" style={{ fontSize: 12 }}>· {LANG_META[code].name}</span>
        </div>
      ))}
    </div>
  );
  const langBtn = (
    <button className="chip" onClick={() => setShowLang(!showLang)} title="Language"
      style={{ position: "relative" }}>🌐 {LANG_META[lang] ? LANG_META[lang].native : lang}</button>
  );
  if (!u) {
    // Guest header - let the world navigate, switch language and sign in.
    return (
      <div className="nav">
        <a href="/" className="logo">Skillhub</a>
        <a href="/browse">{tr("browse")}</a>
        <span className="sp" />
        <div style={{ position: "relative" }}>{langBtn}{showLang && langPop}</div>
        <a href="/login"><button className="btn sm ghost">{tr("login")}</button></a>
        <a href="/signup"><button className="btn sm">{tr("signup")}</button></a>
      </div>
    );
  }
  const links = [["/browse", tr("browse")], ["/match", tr("match")],
                 ["/dashboard", tr("dashboard")], ["/chat", tr("chat")],
                 ["/profile", tr("profile")]];
  async function openNotif(n) {
    try { await api("/notifications/" + n.id + "/read", { method: "PUT" }); } catch (e) {}
    setShow(false);
    if (n.link) router.push(n.link);
  }
  async function markAll() {
    try {
      await api("/notifications/read-all", { method: "PUT" });
      setUnread(0); setNotifs((ns) => ns.map((n) => ({ ...n, read: true })));
    } catch (e) {}
  }
  return (
    <div className="nav">
      <a href="/" className="logo">Skillhub</a>
      {links.map(([h, lbl]) => <a key={h} href={h}>{lbl}</a>)}
      <span className="sp" />
      <div style={{ position: "relative" }}>{langBtn}{showLang && langPop}</div>
      <div style={{ position: "relative" }}>
        <button className="chip" onClick={() => setShow(!show)} title={tr("notifications")} style={{ position: "relative" }}>
          🔔
          {unread > 0 && <span style={{ position: "absolute", top: -7, right: -7, background: "var(--red)",
            color: "#fff", borderRadius: 999, fontSize: 10, fontWeight: 800, minWidth: 18, height: 18,
            lineHeight: "18px", padding: "0 4px" }}>{unread}</span>}
        </button>
        {show && (
          <div className="panel notifpop" style={{ position: "absolute", right: 0, top: 42,
            maxHeight: 380, overflow: "auto", margin: 0, zIndex: 50, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <b style={{ fontSize: 14 }}>{tr("notifications")}</b>
              <button className="btn sm ghost" onClick={markAll}>{tr("markAllRead")}</button>
            </div>
            {!notifs.length && <p className="muted" style={{ fontSize: 13 }}>{tr("noNotif")}</p>}
            {notifs.map((n) => (
              <div key={n.id} onClick={() => openNotif(n)}
                style={{ padding: "10px 8px", borderRadius: 10, cursor: "pointer",
                  borderBottom: "1px solid var(--line)", background: n.read ? "transparent" : "#f1ecff",
                  fontSize: 13 }}>
                <div style={{ fontWeight: n.read ? 500 : 700 }}>{n.message}</div>
                <div className="muted" style={{ fontSize: 11 }}>{n.date}</div>
              </div>))}
          </div>
        )}
      </div>
      <span className="pill">{u.name} - {u.role}</span>
      <button className="btn sm ghost" onClick={() => { logout(); router.push("/"); }}>
        {tr("logout")}</button>
    </div>
  );
}