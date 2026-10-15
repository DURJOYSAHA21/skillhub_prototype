"use client";
import { useEffect, useState } from "react";
import { api, downloadFile } from "@/lib/api";
import { Panel, KpiRow, Tabs, Msg, Field, Badge, Btn, Table, Row } from "@/components/ui";
import TxnTable from "@/components/TxnTable";

const TAKA = "\u09f3";

export default function AdminConsole() {
  const [view, setView] = useState("approvals");
  const [an, setAn] = useState(null);
  const [pending, setPending] = useState([]);
  const [users, setUsers] = useState([]);
  const [courses, setCourses] = useState([]);
  const [txns, setTxns] = useState([]);
  const [pms, setPms] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [cats, setCats] = useState([]);
  const [ens, setEns] = useState([]);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const say = (m) => { setMsg(m); setErr(""); };
  const cry = (e) => { setErr(e.message || String(e)); setMsg(""); };

  function loadAll() {
    api("/admin/analytics").then(setAn).catch(cry);
    api("/admin/courses/pending").then((d) => setPending(d.courses)).catch(() => {});
    api("/admin/users").then((d) => setUsers(d.users)).catch(() => {});
    api("/admin/courses").then((d) => setCourses(d.courses)).catch(() => {});
    api("/txns/admin").then((d) => setTxns(d.transactions)).catch(() => {});
    api("/admin/payment-methods").then((d) => setPms(d.methods)).catch(() => {});
    api("/admin/reviews").then((d) => setReviews(d.reviews)).catch(() => {});
    api("/admin/categories").then((d) => setCats(d.categories)).catch(() => {});
    api("/admin/enrollments").then((d) => setEns(d.enrollments)).catch(() => {});
  }
  useEffect(loadAll, []);
  const refresh = () => loadAll();

  const tabs = [
    { id: "approvals", label: "Course approvals", badge: pending.length },
    { id: "analytics", label: "Platform analysis" },
    { id: "courses", label: "All courses" },
    { id: "users", label: "Users", badge: users.filter((u) => u.status !== "active").length },
    { id: "payments", label: "Payments & refunds" },
    { id: "reviews", label: "Review moderation" },
    { id: "enrollments", label: "Enrollments" },
    { id: "categories", label: "Categories" },
    { id: "broadcast", label: "Announcements" },
    { id: "exports", label: "CSV exports" },
  ];
  return (
    <div>
      <Tabs tabs={tabs} view={view} setView={setView} />
      <Msg err={err} msg={msg} />
      {view === "approvals" && <Approvals pending={pending} say={say} cry={cry} refresh={refresh} />}
      {view === "analytics" && <Analytics an={an} />}
      {view === "courses" && <AllCourses courses={courses} say={say} cry={cry} refresh={refresh} />}
      {view === "users" && <Users users={users} say={say} cry={cry} refresh={refresh} />}
      {view === "payments" && <Payments pms={pms} txns={txns} say={say} cry={cry} refresh={refresh} />}
      {view === "reviews" && <Moderation reviews={reviews} say={say} cry={cry} refresh={refresh} />}
      {view === "enrollments" && <Enrollments ens={ens} say={say} cry={cry} refresh={refresh} />}
      {view === "categories" && <Categories cats={cats} say={say} cry={cry} refresh={refresh} />}
      {view === "broadcast" && <Broadcast say={say} cry={cry} />}
      {view === "exports" && <Exports cry={cry} />}
    </div>
  );
}

function Approvals({ pending, say, cry, refresh }) {
  const [notes, setNotes] = useState({});
  async function decide(c, status) {
    try {
      const d = await api("/admin/courses/" + c.id + "/status", {
        method: "PUT",
        body: { status: status, note: (notes[c.id] || "").trim() },
      });
      say("Course " + status + ". The mentor was notified" + (d.note ? " with your note." : "."));
      refresh();
    } catch (e) { cry(e); }
  }
  return (
    <Panel title="Course review queue" sub={pending.length + " course(s) waiting. Add a note - mentors see it."}>
      {pending.length === 0 && <p className="muted">Nothing waiting. New submissions land here automatically.</p>}
      {pending.map((c) => (
        <div key={c.id} style={{ border: "1px solid var(--line)", borderRadius: 14, padding: 12, marginBottom: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
            <div>
              <b style={{ fontSize: 14 }}>{c.title}</b>
              <p className="muted" style={{ margin: "2px 0 0" }}>by {c.mentor} - {TAKA}{c.price} - {c.language}</p>
            </div>
            <a className="btn sm ghost" href={"/course/" + c.id}>Preview</a>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
            <input style={{ flex: 2, minWidth: 200 }} placeholder="Optional note for the instructor"
              value={notes[c.id] || ""} onChange={(e) => setNotes((n) => ({ ...n, [c.id]: e.target.value }))} />
            <Btn tone="green" onClick={() => decide(c, "published")}>Approve</Btn>
            <Btn tone="red" onClick={() => decide(c, "rejected")}>Reject</Btn>
            <Btn tone="gray" onClick={() => decide(c, "unpublished")}>Take offline</Btn>
            <Btn tone="ghost" onClick={() => decide(c, "pending")}>Keep waiting</Btn>
          </div>
        </div>
      ))}
    </Panel>
  );
}

function Analytics({ an }) {
  if (!an) return <Panel title="Platform analysis">Loading...</Panel>;
  const u = an.users || {}; const c = an.courses || {}; const t = an.transactions_by_status || {};
  return (
    <>
      <KpiRow cols={4} items={[
        { label: "Users", value: (u.admin || 0) + (u.mentor || 0) + (u.learner || 0), hint: "+" + an.new_users_7d + " this week" },
        { label: "Learners / mentors", value: (u.learner || 0) + " / " + (u.mentor || 0) },
        { label: "Published courses", value: c.published || 0, hint: (c.pending || 0) + " pending, " + (c.rejected || 0) + " rejected" },
        { label: "Revenue", value: TAKA + an.revenue, hint: TAKA + an.refunded + " refunded" },
        { label: "Enrollments", value: an.enrollments },
        { label: "Completion rate", value: an.completion_rate + "%", hint: "avg progress " + an.avg_progress + "%" },
        { label: "Successful payments", value: t.success || 0, hint: (t.failed || 0) + " failed" },
        { label: "1-2 star reviews", value: an.low_ratings, color: an.low_ratings ? "#c0392b" : undefined },
      ]} />
      <div className="grid g2">
        <Panel title="Revenue by month" pad={false}>
          <Table head={["Month", "Payments", "Revenue"]}>
            {(an.monthly || []).map((m) => (
              <Row key={m.month}><td>{m.month}</td><td>{m.payments}</td><td>{TAKA}{m.revenue}</td></Row>
            ))}
          </Table>
        </Panel>
        <Panel title="Categories by students" pad={false}>
          <Table head={["Category", "Courses", "Students"]}>
            {(an.categories || []).map((x) => (
              <Row key={x.category}><td>{x.category}</td><td>{x.courses}</td><td>{x.students}</td></Row>
            ))}
          </Table>
        </Panel>
        <Panel title="Top mentors" pad={false}>
          <Table head={["Mentor", "Courses", "Students", "Revenue", "Verified"]}>
            {(an.top_mentors || []).map((m) => (
              <Row key={m.mentor_id}>
                <td>{m.name}</td><td>{m.courses}</td><td>{m.students}</td>
                <td>{TAKA}{m.revenue}</td><td>{m.verified ? "yes" : "no"}</td>
              </Row>
            ))}
          </Table>
        </Panel>
        <Panel title="Top rated courses" pad={false}>
          <Table head={["Course", "Rating"]}>
            {(an.top_courses || []).map((x, i) => (
              <Row key={i}><td>{x.title}</td><td>{x.rating}</td></Row>
            ))}
          </Table>
        </Panel>
      </div>
    </>
  );
}

function AllCourses({ courses, say, cry, refresh }) {
  const [q, setQ] = useState("");
  const [st, setSt] = useState("");
  async function feature(c, v) {
    try { await api("/admin/courses/" + c.id + "/feature", { method: "PUT", body: { featured: v } }); say(v ? "Featured on the homepage." : "Removed from the homepage."); refresh(); } catch (e) { cry(e); }
  }
  async function setStatus(c, status) {
    try { await api("/admin/courses/" + c.id + "/status", { method: "PUT", body: { status: status, note: "Set by the admin team." } }); say("Course is now " + status + "."); refresh(); } catch (e) { cry(e); }
  }
  async function drop(c) {
    if (!confirm("Delete " + c.title + " permanently (lessons, quizzes, enrollments)?")) return;
    try { await api("/admin/courses/" + c.id, { method: "DELETE" }); say("Course deleted."); refresh(); } catch (e) { cry(e); }
  }
  const rows = courses.filter((c) => (!q || c.title.toLowerCase().includes(q.toLowerCase())) && (!st || c.status === st));
  return (
    <Panel title="All courses" sub={rows.length + " of " + courses.length + " course(s)"}
      right={<>
        <input placeholder="Search title" value={q} onChange={(e) => setQ(e.target.value)} style={{ width: 180 }} />
        <select value={st} onChange={(e) => setSt(e.target.value)} style={{ width: 140 }}>
          <option value="">All statuses</option>
          {["published", "pending", "rejected", "unpublished"].map((x) => <option key={x}>{x}</option>)}
        </select>
      </>}>
      <Table head={["Course", "Mentor", "Status", "Level", "Price", "Lessons", "Students", "Revenue", "Rating", ""]}>
        {rows.map((c) => (
          <Row key={c.id}>
            <td><a href={"/course/" + c.id}>{c.title}</a>{c.featured && <span className="pill" style={{ marginLeft: 6 }}>featured</span>}{c.note && <p className="muted" style={{ margin: 0 }}>note: {c.note}</p>}</td>
            <td>{c.mentor}</td>
            <td><Badge st={c.status} /></td>
            <td>{c.level || "-"}</td>
            <td>{c.price > 0 ? TAKA + c.price : "Free"}</td>
            <td>{c.lessons}</td>
            <td>{c.students}</td>
            <td>{TAKA}{c.revenue}</td>
            <td>{c.reviews ? c.rating : "-"}</td>
            <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
              <Btn tone="ghost" onClick={() => feature(c, !c.featured)}>{c.featured ? "Unfeature" : "Feature"}</Btn>{" "}
              {c.status !== "published" && <Btn tone="green" onClick={() => setStatus(c, "published")}>Approve</Btn>}{" "}
              {c.status === "published" && <Btn tone="gray" onClick={() => setStatus(c, "unpublished")}>Offline</Btn>}{" "}
              <Btn tone="red" onClick={() => drop(c)}>Delete</Btn>
            </td>
          </Row>
        ))}
      </Table>
      {rows.length === 0 && <p className="muted">No courses match this filter.</p>}
    </Panel>
  );
}
function Users({ users, say, cry, refresh }) {
  const [role, setRole] = useState("");
  const [open, setOpen] = useState(0);
  const [detail, setDetail] = useState(null);
  async function setStatus(u, status) {
    try { await api("/admin/users/" + u.id + "/status", { method: "PUT", body: { status: status } }); say(u.name + " is now " + status + "."); refresh(); } catch (e) { cry(e); }
  }
  async function unlock(u) {
    try { await api("/admin/users/" + u.id + "/unlock", { method: "PUT" }); say("Login lock cleared for " + u.name + "."); refresh(); } catch (e) { cry(e); }
  }
  async function verify(u, v) {
    try { await api("/admin/mentors/" + u.id + "/verify", { method: "PUT", body: { verified: v } }); say(v ? u.name + " is now a verified instructor." : "Verification removed from " + u.name + "."); refresh(); } catch (e) { cry(e); }
  }
  async function changeRole(u, r) {
    try { await api("/admin/users/" + u.id + "/role", { method: "PUT", body: { role: r } }); say(u.name + " is now a " + r + "."); refresh(); } catch (e) { cry(e); }
  }
  async function drop(u) {
    if (!confirm("Permanently delete " + u.name + " and all their data?")) return;
    try { await api("/admin/users/" + u.id, { method: "DELETE" }); say("User deleted."); refresh(); } catch (e) { cry(e); }
  }
  async function show(u) {
    if (open === u.id) { setOpen(0); setDetail(null); return; }
    setOpen(u.id); setDetail(null);
    try { setDetail(await api("/admin/users/" + u.id)); } catch (e) { cry(e); }
  }
  const rows = users.filter((u) => !role || u.role === role);
  return (
    <>
      <Panel title="User management" sub={rows.length + " account(s)"}
        right={<select value={role} onChange={(e) => setRole(e.target.value)} style={{ width: 150 }}>
          <option value="">All roles</option><option value="learner">Learners</option>
          <option value="mentor">Mentors</option><option value="admin">Admins</option>
        </select>}>
        <Table head={["Account", "Role", "Status", "Joined", "Actions"]}>
          {rows.map((u) => (
            <Row key={u.id}>
              <td><b style={{ fontSize: 13 }}>{u.name}</b><p className="muted" style={{ margin: 0 }}>{u.email}</p></td>
              <td>{u.role}</td>
              <td><span className={"tstat " + (u.status === "active" ? "ok" : u.status === "blocked" ? "no" : "pend")}>{u.status}</span></td>
              <td>{u.created}</td>
              <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                <Btn tone="ghost" onClick={() => show(u)}>{open === u.id ? "Hide" : "Details"}</Btn>{" "}
                {u.role !== "admin" && (
                  <Btn tone={u.status === "blocked" ? "green" : "red"}
                    onClick={() => setStatus(u, u.status === "blocked" ? "active" : "blocked")}>
                    {u.status === "blocked" ? "Unblock" : "Block"}
                  </Btn>)}{" "}
                {u.role === "mentor" && <Btn tone="teal" onClick={() => verify(u, true)}>Verify</Btn>}{" "}
                {u.role === "mentor" && <Btn tone="gray" onClick={() => verify(u, false)}>Unverify</Btn>}{" "}
                {u.role !== "admin" && <Btn tone="red" onClick={() => drop(u)}>Delete</Btn>}
              </td>
            </Row>
          ))}
        </Table>
      </Panel>
      {open > 0 && detail && (
        <Panel title={detail.name + " - account detail"} sub={detail.email}>
          <div className="grid g4">
            <div><label>Role</label>
              <select value={detail.role} onChange={(e) => changeRole(detail, e.target.value)}>
                <option value="learner">learner</option><option value="mentor">mentor</option><option value="admin">admin</option>
              </select>
            </div>
            <div><label>Status</label><p><Badge st={detail.status} /></p></div>
            <div><label>Login locked</label><p>{detail.locked ? "yes - failed attempts " + detail.last_login_fail : "no"}</p>
              {detail.locked && <Btn tone="orange" onClick={() => unlock(detail)}>Clear lock</Btn>}</div>
            <div><label>Created</label><p>{detail.created}</p></div>
          </div>
          {detail.role === "mentor" && (
            <p className="muted">Verified: {detail.verified ? "yes" : "no"} - headline: {detail.headline || "(none)"} - courses: {(detail.courses || []).join(", ") || "none"}</p>
          )}
          {detail.role === "learner" && (
            <>
              <p className="muted">Total spend: {TAKA}{detail.spend}</p>
              <Table head={["Course", "Progress"]}>
                {(detail.enrollments || []).map((e, i) => (
                  <Row key={i}><td>{e.course}</td><td>{e.progress}%</td></Row>
                ))}
              </Table>
            </>
          )}
        </Panel>
      )}
    </>
  );
}

function Payments({ pms, txns, say, cry, refresh }) {
  const [pm, setPm] = useState({ name: "", account: "" });
  const [st, setSt] = useState("");
  async function add() {
    try { await api("/admin/payment-methods", { method: "POST", body: pm }); setPm({ name: "", account: "" }); say("Payment method added."); refresh(); } catch (e) { cry(e); }
  }
  async function toggle(m) {
    try { await api("/admin/payment-methods/" + m.id, { method: "PUT", body: { status: m.status === "active" ? "inactive" : "active" } }); refresh(); } catch (e) { cry(e); }
  }
  async function refund(t) {
    if (!confirm("Mark " + t.ref + " (" + TAKA + t.amount + ") as refunded?")) return;
    try { await api("/admin/txns/" + t.id + "/refund", { method: "POST" }); say("Refund recorded - learner and mentor were notified."); refresh(); } catch (e) { cry(e); }
  }
  const rows = txns.filter((t) => !st || t.status === st);
  return (
    <>
      <Panel title="Payment methods" sub="These are shown at checkout.">
        <Table head={["Method", "Account reference", "Status", ""]}>
          {pms.map((m) => (
            <Row key={m.id}>
              <td>{m.name}</td><td>{m.account}</td><td><Badge st={m.status} /></td>
              <td style={{ textAlign: "right" }}><Btn tone={m.status === "active" ? "red" : "green"} onClick={() => toggle(m)}>
                {m.status === "active" ? "Disable" : "Enable"}</Btn></td>
            </Row>
          ))}
        </Table>
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <input placeholder="Method name (e.g. bKash Nexus)" value={pm.name} onChange={(e) => setPm({ ...pm, name: e.target.value })} />
          <input placeholder="Account / number shown to learners" value={pm.account} onChange={(e) => setPm({ ...pm, account: e.target.value })} />
          <Btn onClick={add}>Add method</Btn>
        </div>
      </Panel>
      <Panel title="Transactions" sub={rows.length + " payment(s)"} pad={false}
        right={<select value={st} onChange={(e) => setSt(e.target.value)} style={{ width: 150 }}>
          <option value="">All statuses</option><option value="success">success</option>
          <option value="failed">failed</option><option value="refunded">refunded</option>
        </select>}>
        <div style={{ padding: 0 }}>
          <TxnTable rows={rows} showLearner onRefund={refund} />
        </div>
      </Panel>
    </>
  );
}

function Moderation({ reviews, say, cry, refresh }) {
  async function drop(r) {
    if (!confirm("Remove this review by " + r.name + "? The course average is recalculated.")) return;
    try { await api("/admin/reviews/" + r.id, { method: "DELETE" }); say("Review removed."); refresh(); } catch (e) { cry(e); }
  }
  return (
    <Panel title="Review moderation" sub={reviews.length + " most recent review(s)"} pad={false}>
      <Table head={["Course", "Learner", "Rating", "Comment", "Instructor reply", "Date", ""]}>
        {reviews.map((r) => (
          <Row key={r.id}>
            <td><a href={"/course/" + r.course_id}>{r.course}</a></td>
            <td>{r.name}</td>
            <td>{r.rating <= 2 ? <Badge st="rejected" /> : <Badge st="published" />} {r.rating}</td>
            <td style={{ maxWidth: 260 }}>{r.comment || "-"}</td>
            <td style={{ maxWidth: 200 }}>{r.reply || "-"}</td>
            <td>{r.date}</td>
            <td style={{ textAlign: "right" }}><Btn tone="red" onClick={() => drop(r)}>Remove</Btn></td>
          </Row>
        ))}
      </Table>
      {reviews.length === 0 && <p className="muted" style={{ padding: 16 }}>No reviews yet.</p>}
    </Panel>
  );
}

function Enrollments({ ens, say, cry, refresh }) {
  async function drop(e) {
    if (!confirm("Remove " + e.learner + " from " + e.course + "?")) return;
    try { await api("/admin/enrollments/" + e.id, { method: "DELETE" }); say("Enrollment removed."); refresh(); } catch (x) { cry(x); }
  }
  return (
    <Panel title="Enrollments" sub={ens.length + " enrollment(s)"} pad={false}>
      <Table head={["Learner", "Course", "Progress", "Status", "Enrolled", ""]}>
        {ens.map((e) => (
          <Row key={e.id}>
            <td>{e.learner}</td><td>{e.course}</td><td>{e.progress}%</td>
            <td>{e.completed ? <Badge st="published" /> : <Badge st="pending" />}</td>
            <td>{e.enrolled}</td>
            <td style={{ textAlign: "right" }}><Btn tone="red" onClick={() => drop(e)}>Remove</Btn></td>
          </Row>
        ))}
      </Table>
      {ens.length === 0 && <p className="muted" style={{ padding: 16 }}>No enrollments yet.</p>}
    </Panel>
  );
}

function Categories({ cats, say, cry, refresh }) {
  const [c, setC] = useState({ name: "", icon: "" });
  async function add() {
    try { await api("/admin/categories", { method: "POST", body: { name: c.name, icon: c.icon || "\ud83d\udcda" } }); say("Category added."); setC({ name: "", icon: "" }); refresh(); } catch (e) { cry(e); }
  }
  async function del(name) {
    if (!confirm("Delete category " + name + "?")) return;
    try { await api("/admin/categories/" + encodeURIComponent(name), { method: "DELETE" }); say("Category removed."); refresh(); } catch (e) { cry(e); }
  }
  return (
    <Panel title="Course categories" sub="Shown as filters on the browse page.">
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <input placeholder="New category name" value={c.name} onChange={(e) => setC({ ...c, name: e.target.value })} />
        <input placeholder="Icon (emoji)" style={{ maxWidth: 120 }} value={c.icon} onChange={(e) => setC({ ...c, icon: e.target.value })} />
        <Btn onClick={add}>Add</Btn>
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {cats.map((x) => (
          <span key={x.name} className="chip" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {x.icon} {x.name}
            <button onClick={() => del(x.name)} style={{ border: "none", background: "transparent", color: "#c0392b", cursor: "pointer", fontWeight: 800 }}>x</button>
          </span>
        ))}
      </div>
    </Panel>
  );
}

function Broadcast({ say, cry }) {
  const [b, setB] = useState({ message: "", role: "" });
  async function send(e) {
    e.preventDefault();
    try { const d = await api("/admin/broadcast", { method: "POST", body: b }); say(d.message); setB({ ...b, message: "" }); } catch (x) { cry(x); }
  }
  return (
    <Panel title="Send an announcement" sub="Delivered to the notification bell and to SkillBot history.">
      <form onSubmit={send}>
        <Field label="Audience">
          <select value={b.role} onChange={(e) => setB({ ...b, role: e.target.value })} style={{ maxWidth: 240 }}>
            <option value="">Everyone</option><option value="learner">Learners only</option>
            <option value="mentor">Mentors only</option><option value="admin">Admins only</option>
          </select>
        </Field>
        <Field label="Message">
          <textarea rows={3} value={b.message} onChange={(e) => setB({ ...b, message: e.target.value })}
            placeholder="New month, new courses: 20% off all paid courses this week!" />
        </Field>
        <button className="btn sm" type="submit" style={{ marginTop: 12 }}>Send announcement</button>
      </form>
    </Panel>
  );
}

function Exports({ cry }) {
  const items = [["users", "All users"], ["courses", "All courses"], ["transactions", "All transactions"], ["enrollments", "All enrollments"]];
  return (
    <Panel title="CSV exports" sub="Open the file in Excel for reporting.">
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        {items.map(([k, label]) => (
          <Btn key={k} tone="dark" onClick={async () => {
            try { await downloadFile("/admin/export/" + k, "skillhub-" + k + ".csv"); } catch (e) { cry(e); }
          }}>{label}</Btn>
        ))}
      </div>
    </Panel>
  );
}