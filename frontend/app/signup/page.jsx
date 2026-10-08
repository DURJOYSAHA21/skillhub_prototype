"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, saveAuth } from "@/lib/api";

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [f, setF] = useState({ name: "", email: "", phone: "", password: "", confirm_password: "", role: "learner", lang: "en" });
  const [otp, setOtp] = useState("");
  const [devOtp, setDevOtp] = useState("");
  const [err, setErr] = useState("");
  const router = useRouter();
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
        {step === 1 ? (<>
          <h2 style={{ margin: "0 0 14px" }}>Create your account</h2>
          <form onSubmit={go}>
            <label>Name</label><input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
            <label>Email Address</label><input value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} placeholder="you@example.com" />
            <label>Phone Number</label><input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} placeholder="01XXXXXXXXX" />
            <label>Password</label><input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} placeholder="min 8 chars, 1 uppercase, 1 number" />
            <label>Confirm Password</label><input type="password" value={f.confirm_password} onChange={(e) => setF({ ...f, confirm_password: e.target.value })} />
            <label>Select User Role :</label>
            <div style={{ display: "flex", gap: 24, fontSize: 14 }}>
              <label style={{ margin: 0 }}><input type="radio" style={{ width: "auto" }} checked={f.role === "mentor"} onChange={() => setF({ ...f, role: "mentor" })} /> Mentor</label>
              <label style={{ margin: 0 }}><input type="radio" style={{ width: "auto" }} checked={f.role === "learner"} onChange={() => setF({ ...f, role: "learner" })} /> Learner</label>
            </div>
            <label>Preferred Language</label>
            <select value={f.lang} onChange={(e) => setF({ ...f, lang: e.target.value })}>
              <option value="en">English</option><option value="bn">Bangla</option><option value="hi">Hindi</option>
            </select>
            {err && <p className="err">{err}</p>}
            <button className="btn teal block" style={{ marginTop: 18 }}>Sign Up</button>
          </form>
          <p className="muted" style={{ marginTop: 14 }}>Already have an account? <a href="/login">Log in</a></p>
        </>) : (<>
          <h2 style={{ margin: "0 0 8px" }}>Verify your email</h2>
          <p className="muted">We sent an OTP to <b>{f.email}</b>.</p>
          {devOtp && <p className="ok" style={{ fontSize: 13 }}>Dev mode — your OTP is: <b>{devOtp}</b></p>}
          <form onSubmit={verify}>
            <label>OTP</label><input value={otp} onChange={(e) => setOtp(e.target.value)} placeholder="6-digit code" />
            {err && <p className="err">{err}</p>}
            <button className="btn teal block" style={{ marginTop: 16 }}>Verify &amp; Continue</button>
          </form>
          <p className="muted" style={{ marginTop: 14 }}><a href="/login">Back to login</a></p>
        </>)}
      </div>
    </div>
  );
}