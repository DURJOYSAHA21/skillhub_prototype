"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function ForgotPage() {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [sent, setSent] = useState(false);
  const [pw, setPw] = useState({ a: "", b: "" });
  const [err, setErr] = useState("");
  const [done, setDone] = useState("");
  useEffect(() => { document.body.classList.add("page-dark"); return () => document.body.classList.remove("page-dark"); }, []);
  async function sendOtp(e) {
    e.preventDefault(); setErr(""); setDone("");
    try {
      const d = await api("/auth/forgot", { method: "POST", body: { email } });
      setDevOtp(d.dev_otp || ""); setSent(true);
    } catch (x) { setErr(x.message); }
  }
  async function confirm(e) {
    e.preventDefault(); setErr("");
    if (!sent) { setErr("Send the OTP first."); return; }
    if (pw.a !== pw.b) { setErr("Passwords do not match."); return; }
    try {
      await api("/auth/forgot-confirm", { method: "POST",
        body: { email, otp, new_password: pw.a, confirm_password: pw.b } });
      setDone("Password updated. You can login now.");
    } catch (x) { setErr(x.message); }
  }
  return (
    <div style={{ maxWidth: 640, margin: "46px auto", position: "relative" }}>
      <div className="panel" style={{ padding: "34px 36px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 900, color: "#4b2a6b" }}>Forget Password</h1>
          <a href="/login" className="muted" style={{ fontSize: 13 }}>Back to login →</a>
        </div>
        <p className="muted" style={{ marginTop: 6, marginBottom: 20 }}>Enter your registered email, we will send a one-time code.</p>
        <form onSubmit={sendOtp}>
          <label>Email Address</label>
          <div style={{ display: "flex", gap: 10 }}>
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@skillhub.dev" />
            <button className="btn ghost" style={{ flex: "0 0 auto" }}>Sent OTP</button>
          </div>
        </form>
        {sent && devOtp && <p className="ok">OTP sent (dev mode, code shown): <b>{devOtp}</b></p>}
        {sent && !devOtp && <p className="ok">OTP sent to your email.</p>}
        <form onSubmit={confirm}>
          <label>OTP</label>
          <input value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="6-digit code" />
          <label>New Password</label>
          <input type="password" value={pw.a} onChange={(e) => setPw({ ...pw, a: e.target.value })} placeholder="New password" />
          <label>Confirm Password</label>
          <input type="password" value={pw.b} onChange={(e) => setPw({ ...pw, b: e.target.value })} placeholder="Repeat new password" />
          {err && <p className="err">{err}</p>}
          {done && <p className="ok">{done}</p>}
          <button className="btn dark block" style={{ marginTop: 20 }}>{done ? "Go to Login" : "Confirm Changes"}</button>
        </form>
        {done && <meta http-equiv="refresh" content="1.2;url=/login" />}
      </div>
    </div>
  );
}