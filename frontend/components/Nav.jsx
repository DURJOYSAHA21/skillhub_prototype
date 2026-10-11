"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUser, logout, api, setLocalUser } from "../lib/api";
import { t } from "../lib/i18n";

export default function Nav() {
  const [u, setU] = useState(null);
  const [notifs, setNotifs] = useState([]);
  const [unread, setUnread] = useState(0);
  const [show, setShow] = useState(false);
  const router = useRouter();
  useEffect(() => { setU(getUser()); }, []);
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
  if (!u) return null;
  const lang = u.lang || "en";
  const links = [["/browse", t(lang, "browse")], ["/match", t(lang, "match")],
                 ["/dashboard", t(lang, "dashboard")], ["/chat", t(lang, "chat")],
                 ["/profile", t(lang, "profile")]];
  async function toggleLang() {
    const next = lang === "en" ? "bn" : "en";
    try { await api("/auth/profile", { method: "PUT", body: { lang: next } }); } catch (e) {}
    setLocalUser({ ...u, lang: next });
    setU({ ...u, lang: next });
  }
  async function openNotif(n) {
    try { await api("/notifications/" + n.id + "/read", { method: "PUT" }); } catch (e) {}
    setShow(false);
    if (n.link) router.push(n.link);
  }
  async function markAll() {
    try {
      await api("/notifications/read-all", { method: "PUT" });
      setUnread(0); setNotifs(ns => ns.map(n => ({ ...n, read: true })));
    } catch (e) {}
  }
  return (
    <div className="nav">
      <span className="logo">Skillhub</span>
      {links.map(([h, lbl]) => <a key={h} href={h}>{lbl}</a>)}
      <span className="sp" />
      <div style={{ position: "relative" }}>
        <button className="chip" onClick={() => setShow(!show)} title="Notifications" style={{ position: "relative" }}>
          🔔
          {unread > 0 && <span style={{ position: "absolute", top: -7, right: -7, background: "var(--red)",
            color: "#fff", borderRadius: 999, fontSize: 10, fontWeight: 800, minWidth: 18, height: 18,
            lineHeight: "18px", padding: "0 4px" }}>{unread}</span>}
        </button>
        {show && (
          <div className="panel notifpop" style={{ position: "absolute", right: 0, top: 42,
            maxHeight: 380, overflow: "auto", margin: 0, zIndex: 50, padding: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <b style={{ fontSize: 14 }}>Notifications</b>
              <button className="btn sm ghost" onClick={markAll}>Mark all read</button>
            </div>
            {!notifs.length && <p className="muted" style={{ fontSize: 13 }}>Nothing yet - enrollments, payments and approvals will appear here.</p>}
            {notifs.map(n => (
              <div key={n.id} onClick={() => openNotif(n)}
                style={{ padding: "10px 8px", borderRadius: 10, cursor: "pointer",
                  borderBottom: "1px solid var(--line)", background: n.read ? "transparent" : "#f1ecff",
                  fontSize: 13 }}>
                <div style={{ fontWeight: n.read ? 500 : 700 }}>{n.message}</div>
                <div className="muted" style={{ fontSize: 11 }}>{n.date}</div>
              </div>))}
          </div>)}
      </div>
      <span className="pill">{u.name} - {u.role}</span>
      <button className="chip" onClick={toggleLang}>{lang === "en" ? "ব" + "াংলা" : "English"}</button>
      <button className="btn sm ghost" onClick={() => { logout(); router.push("/"); }}>
        {t(lang, "logout")}</button>
    </div>
  );
}