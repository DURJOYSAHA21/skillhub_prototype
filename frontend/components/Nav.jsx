"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getUser, logout, api, setLocalUser } from "../lib/api";
import { t } from "../lib/i18n";

export default function Nav() {
  const [u, setU] = useState(null);
  const router = useRouter();
  useEffect(() => { setU(getUser()); }, []);
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
  return (
    <div className="nav">
      <span className="logo">Skillhub</span>
      {links.map(([h, lbl]) => <a key={h} href={h}>{lbl}</a>)}
      <span className="sp" />
      <span className="pill">{u.name} - {u.role}</span>
      <button className="chip" onClick={toggleLang}>{lang === "en" ? "ব" + "াংলা" : "English"}</button>
      <button className="btn sm ghost" onClick={() => { logout(); router.push("/"); }}>
        {t(lang, "logout")}</button>
    </div>
  );
}
