"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { api, getUser, setLocalUser } from "@/lib/api";

export default function ProfilePage() {
  const [u, setU] = useState(null);
  const [f, setF] = useState({ name: "", phone: "", dob: "", country: "", bio: "", lang: "en" });
  const [pw, setPw] = useState({ old: "", new1: "", new2: "" });
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  useEffect(() => {
    const g = getUser();
    if (!g) return;
    setU(g);
    api("/auth/me").then((d) => {
      setF({ name: d.name || "", phone: d.phone || "", dob: d.dob || "", country: d.country || "", bio: d.bio || "", lang: d.lang || "en" });
    }).catch(() => {});
  }, []);
  if (!u) return null;
  async function save() {
    setErr(""); setOk("");
    try {
      const d = await api("/auth/profile", { method: "PUT", body: JSON.stringify(f) });
      if (d.user) setLocalUser(d.user);
      setOk("Profile saved.");
      if (d.user) setU(d.user);
    } catch (e) { setErr(e.message); }
  }
  async function changePw() {
    setErr(""); setOk("");
    if (pw.new1 !== pw.new2) { setErr("New password and confirmation must match."); return; }
    try {
      await api("/auth/change-password", { method: "POST", body: JSON.stringify({ current_password: pw.old, new_password: pw.new1, confirm_password: pw.new2 }) });
      setOk("Password changed."); setPw({ old: "", new1: "", new2: "" });
    } catch (e) { setErr(e.message); }
  }
  const inp = "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm";
  return (
    <>
      <Nav />
      <main className="max-w-2xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-1">My Profile</h1>
        <p className="text-sm text-slate-500 mb-6">{u.email} ({u.role})</p>
        {err && <div className="mb-4 p-3 rounded-lg bg-rose-50 text-rose-700 text-sm">{err}</div>}
        {ok && <div className="mb-4 p-3 rounded-lg bg-emerald-50 text-emerald-700 text-sm">{ok}</div>}
        <div className="bg-white border border-slate-200 rounded-xl p-5 mb-6 shadow-sm">
          <h2 className="font-semibold mb-4">Edit profile</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input className={inp} placeholder="Full name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
            <input className={inp} placeholder="Phone (11 digits)" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} />
            <div>
              <label className="text-xs text-slate-500">Date of birth</label>
              <input type="date" className={inp} value={f.dob} onChange={(e) => setF({ ...f, dob: e.target.value })} />
            </div>
            <input className={inp} placeholder="Country" value={f.country} onChange={(e) => setF({ ...f, country: e.target.value })} />
          </div>
          <textarea className={inp + " mt-3"} rows={3} placeholder="Short bio" value={f.bio} onChange={(e) => setF({ ...f, bio: e.target.value })} />
          <div className="mt-3">
            <label className="text-xs text-slate-500">UI language (req #13, saved to your account)</label>
            <select className={inp} value={f.lang} onChange={(e) => setF({ ...f, lang: e.target.value })}>
              <option value="en">English</option>
              <option value="bn">Bangla</option>
            </select>
          </div>
          <button onClick={save} className="mt-4 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold px-4 py-2 rounded-lg">Save changes</button>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h2 className="font-semibold mb-4">Change password</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input type="password" className={inp} placeholder="Current password" value={pw.old} onChange={(e) => setPw({ ...pw, old: e.target.value })} />
            <input type="password" className={inp} placeholder="New password" value={pw.new1} onChange={(e) => setPw({ ...pw, new1: e.target.value })} />
            <input type="password" className={inp} placeholder="Confirm new" value={pw.new2} onChange={(e) => setPw({ ...pw, new2: e.target.value })} />
          </div>
          <button onClick={changePw} className="mt-4 bg-slate-800 hover:bg-slate-900 text-white text-sm font-semibold px-4 py-2 rounded-lg">Update password</button>
        </div>
      </main>
    </>
  );
}
