"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, saveAuth } from "@/lib/api";
import { useLang } from "@/components/LangContext";
import { LANG_META } from "@/lib/i18n";

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [f, setF] = useState({ name: "", email: "", phone: "", password: "", confirm_password: "", role: "learner", lang: "en" });
  const [otp, setOtp] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [err, setErr] = useState("");
  const router = useRouter();
  const { lang: uiLang, setLang, tr } = useLang();
  useEffect(() => { document.body.classList.add("page-teal"); return () => document.body.classList.remove("page-teal"); }, []);
  async function go(e) {
    e.preventDefault(); setErr("");
    try {
      const d = await api("/auth/signup", { method: "POST", body: f });
      setDevOtp(d.dev_otp || ""); setStep(2);
    } catch (x) { setErr(x.message); }
  }
  async function verify(e) {
    e.preventDefault(); setErr("");
    try {
      const d = await api("/auth/verify", { method: "POST", body: { email: f.email, otp } });
      saveAuth(d); router.push("/dashboard");
    } catch (x) { setErr(x.message); }
  }
  return (
    <div className="authsplit">
      <div className="right art-teal" aria-hidden>🚀</div>
      <div className="left">
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end", marginBottom: 12 }}>
          {Object.keys(LANG_META).map((code) => (
            <button key={code} type="button" onClick={() => setLang(code)}
              className={"chip" + (code === uiLang ? " on" : "")} style={{ cursor: "pointer" }}>{LANG_META[code].native}</button>
          ))}
        </div>
        {step === 1 ? (<>
          <h2 style={{ margin: "0 0 14px" }}>{tr("createYourAccount")}</h2>
          <form onSubmit={go}>
            <label>{tr("name")}</label><input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
            <label>{tr("emailAddress")}</label><input value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} placeholder="you@example.com" />
            <label>{tr("phoneNumber")}</label><input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} placeholder="01XXXXXXXXX" />
            <label>{tr("password")}</label><input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} placeholder="min 8 chars, 1 uppercase, 1 number" />
            <label>{tr("confirmPassword")}</label><input type="password" value={f.confirm_password} onChange={(e) => setF({ ...f, confirm_password: e.target.value })} />
            <label>{tr("selectRole")} :</label>
            <div style={{ display: "flex", gap: 24, fontSize: 14 }}>
              <label style={{ margin: 0 }}><input type="radio" style={{ width: "auto" }} checked={f.role === "mentor"} onChange={() => setF({ ...f, role: "mentor" })} /> {tr("mentor")}</label>
              <label style={{ margin: 0 }}><input type="radio" style={{ width: "auto" }} checked={f.role === "learner"} onChange={() => setF({ ...f, role: "learner" })} /> {tr("learner")}</label>
            </div>
            <label>{tr("preferredLanguage")}</label>
            <select value={f.lang} onChange={(e) => setF({ ...f, lang: e.target.value })}>
              {Object.keys(LANG_META).map((code) => <option key={code} value={code}>{LANG_META[code].native} · {LANG_META[code].name}</option>)}
            </select>
            {err && <p className="err">{err}</p>}
            <button className="btn teal block" style={{ marginTop: 18 }}>{tr("signup")}</button>
          </form>
          <p className="muted" style={{ marginTop: 14 }}>{tr("alreadyHaveAccount")} <a href="/login">{tr("logIn")}</a></p>
        </>) : (<>
          <h2 style={{ margin: "0 0 8px" }}>{tr("verifyEmailTitle")}</h2>
          <p className="muted">{tr("otpSentTo")} <b>{f.email}</b>.</p>
          {devOtp && <p className="ok" style={{ fontSize: 13 }}>Dev mode — your OTP is: <b>{devOtp}</b></p>}
          <form onSubmit={verify}>
            <label>OTP</label><input value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="6-digit code" />
            {err && <p className="err">{err}</p>}
            <button className="btn teal block" style={{ marginTop: 16 }}>{tr("verifyContinue")}</button>
          </form>
          <p className="muted" style={{ marginTop: 14 }}><a href="/login">{tr("backToLogin")}</a></p>
        </>)}
      </div>
    </div>
  );
}