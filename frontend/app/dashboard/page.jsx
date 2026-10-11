"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { api, getUser, getToken, pdfUrl } from "@/lib/api";
import AssessBuilder from "@/components/AssessBuilder";

function openPdf(path) {
  fetch(pdfUrl(path), { headers: { Authorization: "Bearer " + getToken() } }).then(async (r) => {
    if (!r.ok) { const d = await r.json().catch(() => ({})); alert(d.detail || "Failed"); return; }
    const b = await r.blob();
    window.open(URL.createObjectURL(b));
  });
}

const btn = "bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg";
const btnDark = "bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg";
const btnRed = "bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg";
const inp = "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm";
const card = "bg-white border border-slate-200 rounded-xl p-5 shadow-sm";
const th = "text-left px-3 py-2 text-xs font-semibold text-slate-500";
const td = "px-3 py-2 text-sm";

async function receipt(txnId) {
  const r = await fetch(pdfUrl("/txns/" + txnId + "/receipt"), {
    headers: { Authorization: "Bearer " + getToken() },
  });
  if (!r.ok) { alert("Receipt not available."); return; }
  const b = await r.blob();
  window.open(URL.createObjectURL(b));
}

function TxnTable({ rows }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead><tr className="border-b border-slate-200">
          <th className={th}>Ref</th><th className={th}>Date</th><th className={th}>Course</th>
          <th className={th}>Method</th><th className={th}>Amount</th><th className={th}>Status</th><th className={th}></th>
        </tr></thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.id} className="border-b border-slate-100">
              <td className={td + " font-mono text-xs"}>{t.ref}</td>
              <td className={td}>{t.date}</td>
              <td className={td}>{t.course}</td>
              <td className={td}>{t.method} •••• {t.card_last4}</td>
              <td className={td}>{"৳"}{t.amount}</td>
              <td className={td}>
                <span className={"px-2 py-0.5 rounded-full text-xs " + (t.status === "success" ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700")}>{t.status}</span>
              </td>
              <td className={td}>{t.status === "success" && <button className={btnDark} onClick={() => receipt(t.id)}>Receipt PDF</button>}</td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td className={td + " text-slate-400"} colSpan={7}>No transactions yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

function LearnerDash() {
  const [courses, setCourses] = useState([]);
  const [txns, setTxns] = useState([]);
  const [wish, setWish] = useState([]);
  async function unwish(cid) {
    try { await api("/wishlist/" + cid, { method: "POST" }); setWish(wish.filter((w) => w.course_id !== cid)); } catch (e) {}
  }
  useEffect(() => {
    api("/my/courses").then((d) => setCourses(d.courses)).catch(() => {});
    api("/wishlist").then((d) => setWish(d.courses)).catch(() => {});
    api("/txns/me").then((d) => setTxns(d.transactions)).catch(() => {});
  }, []);
  return (
    <>
      <div className={card + " mb-6"}>
        <h2 className="font-semibold mb-4">My courses (progress tracking, req #15)</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {courses.map((c) => (
            <div key={c.enrollment_id} className="border border-slate-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <p className="font-medium text-sm">{c.title}</p>
                {c.completed && <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Completed</span>}
              </div>
              <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500" style={{ width: c.progress + "%" }} />
              </div>
              <div className="mt-2 flex gap-2">
                <a href={"/learn/" + c.course_id} className={btn}>Continue learning</a>
                {c.completed && <button className={btnDark} onClick={() => openPdf("/courses/" + c.course_id + "/certificate")}>Certificate</button>}
              </div>
            </div>
          ))}
          {courses.length === 0 && <p className="text-sm text-slate-400">Not enrolled in any course yet. <a className="text-emerald-700 underline" href="/browse">Browse courses</a>.</p>}
        </div>
      </div>
      {wish.length > 0 && (
        <div className={card + " mb-6"}>
          <h2 className="font-semibold mb-3">Saved for later ({wish.length})</h2>
          <div className="flex flex-wrap gap-2">
            {wish.map((w) => (
              <span key={w.course_id} className="flex items-center gap-2 border border-slate-200 rounded-full px-3 py-1 text-sm">
                <a href={"/course/" + w.course_id} className="font-medium">{w.title}</a>
                <button className="text-xs text-rose-600" onClick={() => unwish(w.course_id)}>remove</button>
              </span>
            ))}
          </div>
        </div>
      )}
      <div className={card}>
        <h2 className="font-semibold mb-4">My transactions (req #19)</h2>
        <TxnTable rows={txns} />
      </div>
    </>
  );
}

function MentorDash() {
  const [courses, setCourses] = useState([]);
  const [txns, setTxns] = useState([]);
  const [earned, setEarned] = useState(0);
  const [nf, setNf] = useState({ title: "", description: "", category: "Tech", language: "en", price: 0, duration_hours: 4 });
  const [lid, setLid] = useState({ course_id: "", title: "", description: "", content: "", video_url: "" });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const load = () => {
    api("/courses?mine=mentor").then((d) => setCourses(d.courses || d)).catch(() => {});
    api("/txns/mentor").then((d) => { setTxns(d.transactions); setEarned(d.total_earned); }).catch(() => {});
  };
  useEffect(load, []);
  async function createCourse() {
    setErr(""); setMsg("");
    try {
      const d = await api("/courses", { method: "POST", body: JSON.stringify(nf) });
      setMsg("Course created (id " + d.id + "). Awaiting admin approval.");
      setNf({ ...nf, title: "", description: "" });
      load();
    } catch (e) { setErr(e.message); }
  }
  async function addLesson(e) {
    e.preventDefault();
    setErr(""); setMsg("");
    const fd = new FormData();
    fd.append("course_id", lid.course_id); fd.append("title", lid.title); fd.append("description", lid.description);
    fd.append("content", lid.content); fd.append("video_url", lid.video_url);
    if (e.target.elements.file.files[0]) fd.append("file", e.target.elements.file.files[0]);
    try {
      await api("/courses/" + lid.course_id + "/lessons", { method: "POST", body: fd });
      setMsg("Lesson uploaded.");
      load();
    } catch (er) { setErr(er.message); }
  }
  const badge = (st) => ({ pending: "bg-amber-100 text-amber-700", published: "bg-emerald-100 text-emerald-700", rejected: "bg-rose-100 text-rose-700" }[st] || "");
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className={card}><p className="text-xs text-slate-500">Total earned</p><p className="text-xl font-bold text-emerald-700">{"৳"}{earned}</p><p className="text-xs text-slate-400 mt-1">from {txns.filter((t) => t.status === "success").length} paid enrollments</p></div>
        <div className={card}><p className="text-xs text-slate-500">My courses</p><p className="text-xl font-bold">{courses.length}</p></div>
        <div className={card}><p className="text-xs text-slate-500">Published</p><p className="text-xl font-bold">{courses.filter((c) => c.status === "published").length}</p></div>
      </div>
      {err && <div className="mb-4 p-3 rounded-lg bg-rose-50 text-rose-700 text-sm">{err}</div>}
      {msg && <div className="mb-4 p-3 rounded-lg bg-emerald-50 text-emerald-700 text-sm">{msg}</div>}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className={card}>
          <h2 className="font-semibold mb-4">Create a course (req #6 — goes to admin for approval)</h2>
          <input className={inp} placeholder="Title" value={nf.title} onChange={(e) => setNf({ ...nf, title: e.target.value })} />
          <textarea className={inp + " mt-3"} rows={2} placeholder="Description" value={nf.description} onChange={(e) => setNf({ ...nf, description: e.target.value })} />
          <div className="grid grid-cols-2 gap-3 mt-3">
            <select className={inp} value={nf.category} onChange={(e) => setNf({ ...nf, category: e.target.value })}>
              {["Tech", "Language", "Business", "Academic", "Creative"].map((c) => <option key={c}>{c}</option>)}
            </select>
            <select className={inp} value={nf.language} onChange={(e) => setNf({ ...nf, language: e.target.value })}>
              {["en", "bn", "ar", "es", "fr", "hi", "ur"].map((c) => <option key={c}>{c}</option>)}
            </select>
            <input className={inp} type="number" min="0" placeholder="Price (0 = free)" value={nf.price} onChange={(e) => setNf({ ...nf, price: Number(e.target.value) })} />
            <input className={inp} type="number" min="1" placeholder="Duration hours" value={nf.duration_hours} onChange={(e) => setNf({ ...nf, duration_hours: Number(e.target.value) })} />
          </div>
          <button onClick={createCourse} className={btn + " mt-4"}>Submit for approval</button>
          <h3 className="font-semibold mt-6 mb-2 text-sm">Upload a lesson to my course (req #7)</h3>
          <form onSubmit={addLesson} className="space-y-2">
            <select className={inp} value={lid.course_id} onChange={(e) => setLid({ ...lid, course_id: e.target.value })}>
              <option value="">Pick course...</option>
              {courses.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
            </select>
            <p className="text-xs text-slate-400">Notes and a YouTube link make the lesson readable inside SkillHub.</p>
            <input className={inp} placeholder="Lesson title" value={lid.title} onChange={(e) => setLid({ ...lid, title: e.target.value })} />
            <input className={inp} placeholder="Lesson description" value={lid.description} onChange={(e) => setLid({ ...lid, description: e.target.value })} />
            <textarea className={inp} rows={3} placeholder="Lesson notes (learners read these)" value={lid.content} onChange={(e) => setLid({ ...lid, content: e.target.value })} />
            <input className={inp} placeholder="Video link (YouTube URL)" value={lid.video_url} onChange={(e) => setLid({ ...lid, video_url: e.target.value })} />
            <input className={inp} type="file" name="file" />
            <button className={btnDark} type="submit">Upload lesson</button>
          </form>
        </div>
        <div>
          <div className={card + " mb-6"}>
            <h2 className="font-semibold mb-3">My courses</h2>
            {courses.map((c) => (
              <div key={c.id} className="flex justify-between items-center border-b border-slate-100 py-2">
                <div>
                  <p className="text-sm font-medium">{c.title}</p>
                  <p className="text-xs text-slate-400">{c.lessons.length} lessons · {"৳"}{c.price}</p>
                </div>
                <span className={"px-2 py-0.5 rounded-full text-xs " + badge(c.status)}>{c.status}</span>
              </div>
            ))}
            {courses.length === 0 && <p className="text-sm text-slate-400">No courses yet.</p>}
          </div>
          <div className={card}>
            <h2 className="font-semibold mb-3">Transactions on my courses (req #18)</h2>
            <TxnTable rows={txns} />
          </div>
        </div>
      </div>
      <AssessBuilder courses={courses} onDone={load} />
    </>
  );
}

function AdminDash() {
  const [an, setAn] = useState(null);
  const [pending, setPending] = useState([]);
  const [users, setUsers] = useState([]);
  const [pms, setPms] = useState([]);
  const [txns, setTxns] = useState([]);
  const [tfilter, setTfilter] = useState("");
  const [pmNew, setPmNew] = useState({ name: "", account: "" });
  const [err, setErr] = useState("");
  const [view, setView] = useState("analysis");
  const load = () => {
    api("/admin/analytics").then(setAn).catch((e) => setErr(e.message));
    api("/admin/courses/pending").then((d) => setPending(d.courses)).catch(() => {});
    api("/admin/users").then((d) => setUsers(d.users)).catch(() => {});
    api("/admin/payment-methods").then((d) => setPms(d.methods)).catch(() => {});
    api("/txns/admin" + (tfilter ? "?status=" + tfilter : "")).then((d) => setTxns(d.transactions)).catch(() => {});
  };
  useEffect(load, [tfilter]);
  async function decide(cid, st) {
    try { await api("/admin/courses/" + cid + "/status", { method: "PUT", body: JSON.stringify({ status: st }) }); load(); }
    catch (e) { setErr(e.message); }
  }
  async function setUser(uid, st) {
    try { await api("/admin/users/" + uid + "/status", { method: "PUT", body: JSON.stringify({ status: st }) }); load(); }
    catch (e) { setErr(e.message); }
  }
  async function dropUser(uid) {
    if (!confirm("Permanently remove this user?")) return;
    try { await api("/admin/users/" + uid, { method: "DELETE" }); load(); }
    catch (e) { setErr(e.message); }
  }
  async function addPm() {
    try { await api("/admin/payment-methods", { method: "POST", body: JSON.stringify(pmNew) }); setPmNew({ name: "", account: "" }); load(); }
    catch (e) { setErr(e.message); }
  }
  async function togglePm(id, st) {
    try { await api("/admin/payment-methods/" + id, { method: "PUT", body: JSON.stringify({ status: st }) }); load(); }
    catch (e) { setErr(e.message); }
  }
  const tile = (id, ic, label) => (
    <button className={"tile" + (view === id ? " on" : "")} onClick={() => setView(id)}>
      <span className="ic">{ic}</span>{label}
    </button>
  );
  const kpi = (label, val) => (
    <div className="kpi"><p className="text-xs text-slate-500">{label}</p><b>{val}</b></div>
  );
  return (
    <>
      <div className="tiles" style={{ marginBottom: 22 }}>
        {tile("analysis", "📈", "Platform Analysis")}
        {tile("courses", "📚", "Manage Courses")}
        {tile("users", "👥", "Manage Users")}
        {tile("payments", "💳", "Payment Methods")}
        {tile("txns", "🧾", "Transactions")}
        <a href="/profile" className="tile"><span className="ic">👤</span>View / Edit Profile</a>
      </div>
      {err && <div className="mb-4 p-3 rounded-lg bg-rose-50 text-rose-700 text-sm">{err}</div>}
      {view === "analysis" && an && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {kpi("Users", an.users.admin + an.users.mentor + an.users.learner)}
          {kpi("Mentors / Learners", an.users.mentor + " / " + an.users.learner)}
          {kpi("Published courses", an.courses.published)}
          {kpi("Revenue", "৳" + an.revenue)}
          {kpi("Enrollments", an.enrollments)}
          {kpi("Completions", an.completed)}
          {kpi("Pending approvals", an.courses.pending)}
          {kpi("Failed payments", an.transactions_by_status.failed || 0)}
        </div>
      )}
      {view === "analysis" && an && (
        <div className={card}>
          <h2 className="font-semibold mb-3">Top courses</h2>
          {(an.top_courses || []).map((c, i) => (
            <p key={i} className="text-sm text-slate-600">{i + 1}. {c.title} — {"★"}{c.rating}</p>
          ))}
        </div>
      )}
      {view === "courses" && (
        <div className={card}>
          <h2 className="font-semibold mb-3">Course approvals (req #16)</h2>
          {pending.map((c) => (
            <div key={c.id} className="flex justify-between items-center border-b border-slate-100 py-2">
              <div><p className="text-sm font-medium">{c.title}</p><p className="text-xs text-slate-400">by {c.mentor} · ৳{c.price} · {c.language}</p></div>
              <div className="flex gap-2">
                <button className="btn sm green" onClick={() => decide(c.id, "published")}>Approve</button>
                <button className="btn sm red" onClick={() => decide(c.id, "rejected")}>Reject</button>
              </div>
            </div>
          ))}
          {pending.length === 0 && <p className="text-sm text-slate-400">Nothing waiting for approval.</p>}
        </div>
      )}
      {view === "users" && (
        <div className={card}>
          <h2 className="font-semibold mb-3">User management (req #20)</h2>
          <div className="overflow-x-auto max-h-105">
            <table className="w-full">
              <thead><tr className="border-b border-slate-200">
                <th className={th}>Name</th><th className={th}>Role</th><th className={th}>Status</th><th className={th}>Actions</th>
              </tr></thead>
              <tbody>
                {users.map((x) => (
                  <tr key={x.id} className="border-b border-slate-100">
                    <td className={td}><p className="font-medium">{x.name}</p><p className="text-xs text-slate-400">{x.email}</p></td>
                    <td className={td}>{x.role}</td>
                    <td className={td}><span className={"tstat " + (x.status === "active" ? "ok" : x.status === "blocked" ? "no" : "pend")}>{x.status}</span></td>
                    <td className={td}>
                      {x.role !== "admin" && (
                        <span className="flex gap-2">
                          <button className="btn sm dark" onClick={() => setUser(x.id, x.status === "blocked" ? "active" : "blocked")}>{x.status === "blocked" ? "Unblock" : "Block"}</button>
                          <button className="btn sm red" onClick={() => dropUser(x.id)}>Remove</button>
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {view === "payments" && (
        <div className={card}>
          <h2 className="font-semibold mb-3">Payment methods (req #21)</h2>
          {pms.map((m) => (
            <div key={m.id} className="flex justify-between items-center border-b border-slate-100 py-2">
              <div><p className="text-sm font-medium">{m.name}</p><p className="text-xs text-slate-400">{m.account}</p></div>
              <button className={"btn sm " + (m.status === "active" ? "red" : "green")} onClick={() => togglePm(m.id, m.status === "active" ? "inactive" : "active")}>
                {m.status === "active" ? "Disable" : "Enable"}
              </button>
            </div>
          ))}
          <div className="flex gap-2 mt-3">
            <input className={inp} placeholder="New method name" value={pmNew.name} onChange={(e) => setPmNew({ ...pmNew, name: e.target.value })} />
            <input className={inp} placeholder="Account ref" value={pmNew.account} onChange={(e) => setPmNew({ ...pmNew, account: e.target.value })} />
            <button className="btn sm" onClick={addPm}>Add</button>
          </div>
        </div>
      )}
      {view === "txns" && (
        <div className={card}>
          <h2 className="font-semibold mb-3 flex justify-between">All transactions (req #17)
            <select className="border border-slate-300 rounded-lg px-2 py-1 text-xs" value={tfilter} onChange={(e) => setTfilter(e.target.value)}>
              <option value="">Filter: All</option><option value="success">Success</option><option value="failed">Failed</option>
            </select>
          </h2>
          <TxnTable rows={txns.slice(0, 15)} />
        </div>
      )}
    </>
  );
}
export default function DashboardPage() {
  const [u, setU] = useState(null);
  useEffect(() => setU(getUser()), []);
  if (!u) return <main className="min-h-screen grid place-items-center text-slate-400">Loading…</main>;
  return (
    <>
      <Nav />
      <main className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-1 capitalize">{u.role} dashboard</h1>
        <p className="text-sm text-slate-500 mb-6">Welcome back, {u.name}.</p>
        {u.role === "learner" && <LearnerDash />}
        {u.role === "mentor" && <MentorDash />}
        {u.role === "admin" && <AdminDash />}
      </main>
    </>
  );
}
