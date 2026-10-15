"use client";
import { useEffect, useState } from "react";
import { api, viewPdf } from "@/lib/api";
import { Panel, KpiRow, Tabs, Msg, Badge, Btn, Table, Row } from "@/components/ui";
import TxnTable from "@/components/TxnTable";

const TAKA = "\u09f3";

export default function LearnerHub() {
  const [view, setView] = useState("overview");
  const [ov, setOv] = useState(null);
  const [courses, setCourses] = useState([]);
  const [txns, setTxns] = useState([]);
  const [wish, setWish] = useState([]);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [tick, setTick] = useState(0);
  const say = (m) => { setMsg(m); setErr(""); };
  const cry = (e) => { setErr(e.message || String(e)); setMsg(""); };

  useEffect(() => {
    let stop = false;
    Promise.all([api("/learner/overview"), api("/my/courses"), api("/txns/me"), api("/wishlist")])
      .then(([o, c, t, w]) => {
        if (stop) return;
        setOv(o); setCourses(c.courses); setTxns(t.transactions); setWish(w.courses);
      })
      .catch((e) => { if (!stop) cry(e); });
    return () => { stop = true; };
  }, [tick]);

  const tabs = [
    { id: "overview", label: "My progress" },
    { id: "learning", label: "My learning", badge: courses.filter((c) => !c.completed && c.progress > 0).length },
    { id: "results", label: "Quiz & assignment results" },
    { id: "certs", label: "Certificates" },
    { id: "notes", label: "My notes" },
    { id: "goals", label: "Learning goals" },
    { id: "saved", label: "Saved courses", badge: wish.length },
    { id: "money", label: "My payments" },
  ];
  return (
    <div>
      <Tabs tabs={tabs} view={view} setView={setView} />
      <Msg err={err} msg={msg} />
      {view === "overview" && (ov
        ? <KpiRow cols={4} items={[
            { label: "Courses", value: ov.courses, hint: ov.in_progress + " in progress" },
            { label: "Completed", value: ov.completed, hint: ov.certificates + " certificate(s)" },
            { label: "Hours learned", value: ov.hours_learned },
            { label: "Average quiz score", value: ov.avg_quiz_score + "%", hint: ov.quizzes_taken + " attempt(s)" },
            { label: "Assignments submitted", value: ov.assignments_submitted },
            { label: "Assignments graded", value: ov.assignments_graded, color: (ov.assignments_submitted - ov.assignments_graded) > 0 ? "#b07d10" : undefined },
            { label: "Saved courses", value: ov.wishlist },
            { label: "Unread notifications", value: ov.unread },
          ]} />
        : <Panel title="Loading...">One moment.</Panel>)}
      {view === "learning" && <Learning courses={courses} say={say} cry={cry} refresh={() => setTick((t) => t + 1)} />}
      {view === "results" && <Results cry={cry} />}
      {view === "certs" && <Certificates ov={ov} cry={cry} />}
      {view === "notes" && <Notes cry={cry} />}
      {view === "goals" && <Goals say={say} cry={cry} />}
      {view === "saved" && (
        <Panel title="Saved for later" sub={wish.length + " course(s)"} pad={false}>
          <Table head={["Course", "Level", "Price", ""]}>
            {wish.map((w) => (
              <Row key={w.course_id}>
                <td><a href={"/course/" + w.course_id}>{w.title}</a></td>
                <td>{w.level || "-"}</td>
                <td>{w.price > 0 ? TAKA + w.price : "Free"}</td>
                <td style={{ textAlign: "right" }}>
                  <Btn tone="red" onClick={async () => {
                    try { await api("/wishlist/" + w.course_id, { method: "DELETE" }); setWish(wish.filter((x) => x.course_id !== w.course_id)); setTick((t) => t + 1); }
                    catch (e) { cry(e); }
                  }}>Remove</Btn>
                </td>
              </Row>
            ))}
          </Table>
          {wish.length === 0 && <p className="muted" style={{ padding: 16 }}>Nothing saved yet - tap the heart on any course.</p>}
        </Panel>
      )}
      {view === "money" && (
        <Panel title="My payments" sub="Receipts open as PDF. Refunds are handled by the admin team.">
          <TxnTable rows={txns} />
        </Panel>
      )}
    </div>
  );
}

function Learning({ courses, say, cry, refresh }) {
  async function leave(c) {
    if (!confirm("Remove " + c.title + " from My Learning?")) return;
    try {
      const d = await api("/enrollments/" + c.course_id, { method: "DELETE" });
      say(d.refund_needed ? d.message + " " + d.hint : d.message);
      refresh();
    } catch (e) { cry(e); }
  }
  if (!courses.length) return <Panel title="My learning"><p className="muted">You are not enrolled yet. <a href="/browse">Browse courses</a> or ask SkillBot for a suggestion.</p></Panel>;
  return (
    <div className="grid g2">
      {courses.map((c) => (
        <div key={c.enrollment_id} className="panel" style={{ margin: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
            <b>{c.title}</b>
            {c.completed ? <Badge st="published" /> : <Badge st="pending" />}
          </div>
          <p className="muted" style={{ margin: "4px 0 8px" }}>
            {c.mentor} - {c.lessons} lesson(s), {c.hours}h, {c.category}
          </p>
          <div className="bar"><i style={{ width: c.progress + "%" }} /></div>
          <p className="muted" style={{ fontSize: 12, margin: "6px 0 8px" }}>
            {c.progress}% - {c.completed ? "all lessons done" : "resume picks up where you left off"}
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <a className="btn sm" href={"/learn/" + c.course_id}>{c.progress > 0 ? "Resume" : "Start course"}</a>
            {c.completed && (
              <Btn tone="dark" onClick={async () => {
                try { await viewPdf("/courses/" + c.course_id + "/certificate"); } catch (e) { cry(e); }
              }}>Certificate</Btn>)}
            <a className="btn sm ghost" href={"/chat?to=" + c.mentor_id}>Ask the instructor</a>
            <Btn tone="red" onClick={() => leave(c)}>Leave course</Btn>
          </div>
        </div>
      ))}
    </div>
  );
}

function Results({ cry }) {
  const [rows, setRows] = useState(null);
  useEffect(() => { api("/my/results").then((d) => setRows(d.results)).catch(cry); }, []);
  if (!rows) return <Panel title="Results">Loading...</Panel>;
  return (
    <Panel title="Quiz and assignment results" sub={rows.length + " result(s)"} pad={false}>
      <Table head={["Type", "Course", "Item", "Score", "Status", "Feedback", "Date"]}>
        {rows.map((r, i) => (
          <Row key={i}>
            <td><span className="pill">{r.kind}</span></td>
            <td><a href={"/learn/" + r.course_id}>{r.course}</a></td>
            <td>{r.item}</td>
            <td>{r.score === null ? "-" : (r.kind === "quiz" ? r.score + "%" : r.score)}</td>
            <td>{r.passed ? <Badge st="published" /> : <Badge st={r.kind === "quiz" ? "rejected" : "pending"} />}</td>
            <td style={{ fontSize: 12 }}>{r.feedback || "-"}</td>
            <td>{r.date}</td>
          </Row>
        ))}
      </Table>
      {rows.length === 0 && <p className="muted" style={{ padding: 16 }}>No quiz or assignment attempts yet.</p>}
    </Panel>
  );
}

function Certificates({ cry }) {
  const [rows, setRows] = useState(null);
  useEffect(() => { api("/my/certificates").then((d) => setRows(d.certificates)).catch(cry); }, []);
  if (!rows) return <Panel title="Certificates">Loading...</Panel>;
  return (
    <Panel title="Certificates" sub="Finish every lesson of a course to earn its certificate.">
      {rows.map((c) => (
        <div key={c.course_id} className="lic" style={{ justifyContent: "space-between" }}>
          <div>
            <b style={{ fontSize: 13 }}>{c.title}</b>
            <p className="muted" style={{ margin: 0 }}>{c.mentor} - {c.hours}h - issued {c.issued}</p>
          </div>
          <Btn tone="dark" onClick={async () => {
            try { await viewPdf("/courses/" + c.course_id + "/certificate"); } catch (e) { cry(e); }
          }}>Open PDF</Btn>
        </div>
      ))}
      {rows.length === 0 && <p className="muted">No certificates yet. Complete a course and it appears here.</p>}
    </Panel>
  );
}

function Notes({ cry }) {
  const [rows, setRows] = useState(null);
  useEffect(() => { api("/my/notes").then((d) => setRows(d.notes)).catch(cry); }, []);
  if (!rows) return <Panel title="My notes">Loading...</Panel>;
  return (
    <Panel title="My lesson notes" sub={rows.length + " note(s) - write more inside any lesson"}>
      {rows.map((n) => (
        <div key={n.lesson_id} style={{ borderBottom: "1px solid var(--line)", padding: "8px 0" }}>
          <b style={{ fontSize: 13 }}>{n.lesson}</b>
          <span className="muted"> - {n.course} ({n.date})</span>
          <p style={{ margin: "4px 0 0", whiteSpace: "pre-wrap" }}>{n.text}</p>
          <a className="btn sm ghost" style={{ marginTop: 6 }} href={"/learn/" + n.course_id}>Open lesson</a>
        </div>
      ))}
      {rows.length === 0 && <p className="muted">No notes yet. Every lesson page has a note box.</p>}
    </Panel>
  );
}

function Goals({ say, cry }) {
  const [goals, setGoals] = useState([]);
  const [text, setText] = useState("");
  useEffect(() => { api("/my/goals").then((d) => setGoals(d.goals)).catch(cry); }, []);
  async function save(list) {
    try { const d = await api("/my/goals", { method: "PUT", body: { goals: list } }); setGoals(d.goals); say("Learning goals saved - SkillBot uses them when suggesting courses."); }
    catch (e) { cry(e); }
  }
  return (
    <Panel title="Learning goals" sub="What do you want to be able to do? These guide your recommendations.">
      <div style={{ display: "flex", gap: 8 }}>
        <input value={text} onChange={(e) => setText(e.target.value)}
          placeholder="e.g. get a junior web developer job" />
        <Btn onClick={() => { const v = text.trim(); if (v) { save([...goals, v]); setText(""); } }}>Add goal</Btn>
      </div>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 12 }}>
        {goals.map((g, i) => (
          <span key={i} className="chip on" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            {g}
            <button className="btn sm ghost" style={{ padding: "2px 8px" }}
              onClick={() => save(goals.filter((_, k) => k !== i))}>x</button>
          </span>
        ))}
      </div>
      {goals.length === 0 && <p className="muted" style={{ marginTop: 10 }}>No goals yet.</p>}
    </Panel>
  );
}