"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, saveAuth } from "@/lib/api";

export default function LoginPage() {
  const [f, setF] = useState({ email: "", password: "" });
  const [err, setErr] = useState("");
  const router = useRouter();
  useEffect(() => { document.body.classList.add("page-peri"); return () => document.body.classList.remove("page-peri"); }, []);
  async function go(e) {
    e.preventDefault(); setErr("");
    try {
      const d = await api("/auth/login", { method: "POST", body: f });
      saveAuth(d);
      router.push("/browse");
    } catch (x) { setErr(x.message); }
  }
  return (
    <div className="authsplit">
      <div className="left">
        <h1 style={{ color: "#3f51b5", fontWeight: 900, fontSize: 30, margin: "0 0 4px" }}>SkillHub ✦</h1>
        <p className="muted" style={{ marginBottom: 28 }}>Welcome back! Please login to your account.</p>
        <form onSubmit={go}>
          <label>Email Address</label>
          <input value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} placeholder="learner@skillhub.dev" />
          <label>Password</label>
          <input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} placeholder="••••••••" />
          <div style={{ textAlign: "right", marginTop: 6 }}>
            <a href="/forgot" className="muted" style={{ fontSize: 13 }}>Forgot Password?</a>
          </div>
          {err && <p className="err">{err}</p>}
          <div style={{ display: "flex", gap: 12, marginTop: 22 }}>
            <button className="btn" style={{ background: "#3f51b5" }}>Login</button>
            <a href="/signup"><span className="btn ghost">Sign Up</span></a>
          </div>
        </form>
        <p className="muted" style={{ marginTop: 26, fontSize: 12 }}>
          Demo: admin@skillhub.dev / Admin123 · rifat@skillhub.dev / Mentor123 · learner@skillhub.dev / Learner123
        </p>
      </div>
      <div className="right art-blue" aria-hidden>🎓</div>
    </div>
  );
}