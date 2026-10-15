"use client";
import { useEffect, useState } from "react";
import { api, getUser } from "@/lib/api";
import { Panel, KpiRow, Tabs, Msg, Field, Badge, Btn, Table, Row } from "@/components/ui";
import TxnTable from "@/components/TxnTable";
import AssessBuilder from "@/components/AssessBuilder";

const TAKA = "\u09f3";
const BLANK = { title: "", description: "", category: "Tech", language: "en",
  price: 0, duration_hours: 4, level: "Beginner", tags: "" };

export default function MentorStudio() {
  const [view, setView] = useState("overview");
  const [ov, setOv] = useState(null);
  const [courses, setCourses] = useState([]);
  const [txns, setTxns] = useState([]);
  const [meta, setMeta] = useState(null);
  const [sel, setSel] = useState(0);
  const [tick, setTick] = useState(0);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const say = (m) => { setMsg(m); setErr(""); };
  const cry = (e) => { setErr(e.message || String(e)); setMsg(""); };
  const refresh = () => setTick((t) => t + 1);

  useEffect(() => { api("/meta").then(setMeta).catch(() => {}); }, []);
  useEffect(() => {
    let stop = false;
    Promise.all([api("/mentor/overview"), api("/courses?mine=mentor"), api("/txns/mentor")])
      .then(([o, c, t]) => {
        if (stop) return;
        setOv(o); setCourses(c.courses); setTxns(t.transactions);
        if (!sel && c.courses.length) setSel(c.courses[0].id);
      })
      .catch((e) => { if (!stop) cry(e); });
    return () => { stop = true; };
  }, [tick]);

  const cats = (meta && meta.all_categories) || ["Tech", "Business", "Language"];
  const langs = (meta && meta.languages) || [{ code: "en", name: "English" }];
  const levels = (meta && meta.levels) || ["Beginner", "Intermediate", "Advanced"];
  const mine = courses.find((c) => c.id === sel) || courses[0] || null;

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "courses", label: "My courses", badge: ov ? ov.pending + ov.rejected : 0 },
    { id: "lessons", label: "Lessons" },
    { id: "students", label: "Students" },
    { id: "assess", label: "Quizzes & grading", badge: ov ? ov.ungraded : 0 },
    { id: "reviews", label: "Reviews", badge: ov ? ov.reviews_unanswered : 0 },
    { id: "money", label: "Earnings" },
    { id: "profile", label: "Instructor profile" },
  ];

  return (
    <div>
      <Tabs tabs={tabs} view={view} setView={setView} />
      <Msg err={err} msg={msg} />
      {view === "overview" && (ov
        ? <Overview ov={ov} courses={courses} go={setView} />
        : <Panel title="Loading your studio...">Give it a second.</Panel>)}
      {view === "courses" && (
        <CoursesTab courses={courses} mine={mine} cats={cats} langs={langs}
          levels={levels} say={say} cry={cry} refresh={refresh} sel={sel} setSel={setSel} />
      )}
      {view === "lessons" && (
        <LessonsTab courses={courses} mine={mine} sel={sel} setSel={setSel}
          say={say} cry={cry} refresh={refresh} />
      )}
      {view === "students" && (
        <StudentsTab courses={courses} sel={sel} setSel={setSel} cry={cry} />
      )}
      {view === "assess" && (
        <AssessTab courses={courses} sel={sel} setSel={setSel} say={say} cry={cry}
          refresh={refresh} />
      )}
      {view === "reviews" && <ReviewsTab courses={courses} say={say} cry={cry} refresh={refresh} />}
      {view === "money" && (
        <Panel title="Earnings" sub={txns.filter((t) => t.status === "success").length + " successful payments"}>
          <TxnTable rows={txns} showLearner />
        </Panel>
      )}
      {view === "profile" && <ProfileTab langs={langs} say={say} cry={cry} refresh={refresh} />}
    </div>
  );
}

function Overview({ ov, courses, go }) {
  return (
    <>
      <KpiRow cols={4} items={[
        { label: "Courses", value: ov.courses, hint: ov.published + " live" },
        { label: "Awaiting review", value: ov.pending, hint: ov.rejected + " rejected", color: ov.pending ? "#b07d10" : undefined },
        { label: "Students", value: ov.students },
        { label: "Revenue", value: TAKA + ov.revenue },
        { label: "Lessons", value: ov.lessons },
        { label: "Quiz attempts", value: ov.quiz_attempts },
        { label: "Submissions to grade", value: ov.ungraded, color: ov.ungraded ? "#c0392b" : undefined },
        { label: "Average rating", value: ov.avg_rating || "-", hint: ov.reviews_total + " reviews" },
      ]} />
      <Panel title="Next actions" sub="Everything an instructor needs, in one place.">
        <div className="grid g3">
          <div>
            <h3 style={{ fontSize: 14, margin: "0 0 6px" }}>Course health</h3>
            {courses.length === 0 && <p className="muted">Create your first course - it goes to the admin queue for approval.</p>}
            {courses.map((c) => (
              <div key={c.id} className="lic" style={{ justifyContent: "space-between" }}>
                <span style={{ fontSize: 13 }}>{c.title}</span>
                <Badge st={c.status} />
              </div>
            ))}
          </div>
          <div>
            <h3 style={{ fontSize: 14, margin: "0 0 6px" }}>Quick jumps</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-start" }}>
              <Btn onClick={() => go("courses")}>Create or edit a course</Btn>
              <Btn tone="teal" onClick={() => go("lessons")}>Upload lessons</Btn>
              <Btn tone="dark" onClick={() => go("assess")}>Grade assignments ({ov.ungraded} waiting)</Btn>
              <Btn tone="ghost" onClick={() => go("reviews")}>Reply to reviews ({ov.reviews_unanswered} waiting)</Btn>
            </div>
          </div>
          <div>
            <h3 style={{ fontSize: 14, margin: "0 0 6px" }}>Approval notes</h3>
            {courses.filter((c) => c.note).length === 0
              && <p className="muted">The review team has not left notes yet.</p>}
            {courses.filter((c) => c.note).map((c) => (
              <div key={c.id} style={{ marginBottom: 8 }}>
                <b style={{ fontSize: 13 }}>{c.title}</b>
                <p className="muted" style={{ marginTop: 2 }}>&quot;{c.note}&quot;</p>
              </div>
            ))}
          </div>
        </div>
      </Panel>
    </>
  );
}
function CoursesTab({ courses, cats, langs, levels, say, cry, refresh, setSel }) {
  const [form, setForm] = useState(BLANK);
  const [editing, setEditing] = useState(0);
  const [file, setFile] = useState(null);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  function fill(c) {
    setEditing(c.id);
    setSel(c.id);
    setForm({ title: c.title, description: c.description || "", category: c.category,
      language: c.language, price: c.price, duration_hours: c.duration_hours,
      level: c.level || "Beginner", tags: c.tags || "" });
  }
  async function uploadThumb(id) {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    await api("/courses/" + id + "/thumbnail", { method: "POST", body: fd });
    setFile(null);
  }
  async function save(e) {
    e.preventDefault();
    try {
      if (editing) {
        const d = await api("/courses/" + editing, { method: "PUT", body: form });
        await uploadThumb(editing);
        say(d.status === "pending"
          ? "Course updated - your changes went straight back to the review queue."
          : "Course updated.");
        setEditing(0);
        setForm(BLANK);
      } else {
        const d = await api("/courses", { method: "POST", body: form });
        await uploadThumb(d.id);
        say("Course #" + d.id + " submitted. The admin team was notified and will review it.");
        setForm(BLANK);
      }
      refresh();
    } catch (e2) { cry(e2); }
  }
  async function resubmit(c) {
    try { await api("/courses/" + c.id + "/resubmit", { method: "PUT" }); say("Sent back to the review queue."); refresh(); }
    catch (e) { cry(e); }
  }
  async function drop(c) {
    if (!confirm("Delete " + c.title + " with its lessons, quizzes and assignments?")) return;
    try { await api("/courses/" + c.id, { method: "DELETE" }); say("Course deleted."); refresh(); }
    catch (e) { cry(e); }
  }
  return (
    <>
      <Panel title={editing ? "Edit course #" + editing : "Create a course"}
        sub="New and edited courses go to the admin review queue before they appear in the catalogue.">
        <form onSubmit={save}>
          <div className="grid g3">
            <Field label="Title" col="1 / span 2">
              <input required value={form.title} onChange={(e) => set("title", e.target.value)}
                placeholder="e.g. Python for Absolute Beginners" />
            </Field>
            <Field label="Cover image (optional)" hint="PNG or JPG, shown on the course card.">
              <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files[0])} />
            </Field>
            <Field label="Description" col="1 / span 3">
              <textarea rows={3} value={form.description}
                onChange={(e) => set("description", e.target.value)}
                placeholder="What will learners be able to do after this course?" />
            </Field>
            <Field label="Category">
              <select value={form.category} onChange={(e) => set("category", e.target.value)}>
                {cats.map((c) => <option key={c}>{c}</option>)}
              </select>
            </Field>
            <Field label="Teaching language">
              <select value={form.language} onChange={(e) => set("language", e.target.value)}>
                {langs.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
              </select>
            </Field>
            <Field label="Level">
              <select value={form.level} onChange={(e) => set("level", e.target.value)}>
                {levels.map((l) => <option key={l}>{l}</option>)}
              </select>
            </Field>
            <Field label={"Price (" + TAKA + ", 0 = free)"}>
              <input type="number" min="0" step="1" value={form.price}
                onChange={(e) => set("price", Number(e.target.value))} />
            </Field>
            <Field label="Duration (hours)">
              <input type="number" min="1" step="0.5" value={form.duration_hours}
                onChange={(e) => set("duration_hours", Number(e.target.value))} />
            </Field>
            <Field label="Tags" hint="Comma separated, used by search.">
              <input value={form.tags} onChange={(e) => set("tags", e.target.value)}
                placeholder="beginner, projects, certificate" />
            </Field>
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
            <button className="btn sm" type="submit">
              {editing ? "Save changes" : "Submit for approval"}
            </button>
            {editing > 0 && (
              <button className="btn sm ghost" type="button"
                onClick={() => { setEditing(0); setForm(BLANK); setFile(null); }}>
                Cancel edit
              </button>)}
          </div>
        </form>
      </Panel>
      <Panel title="My courses" sub={courses.length + " course(s) on this account"} pad={false}>
        <Table head={["Course", "Status", "Level", "Price", "Lessons", "Students", "Rating", ""]}>
          {courses.map((c) => (
            <Row key={c.id}>
              <td>
                <b style={{ fontSize: 13 }}>{c.title}</b>
                {c.note && <p className="muted" style={{ margin: "2px 0 0" }}>Reviewer note: {c.note}</p>}
              </td>
              <td><Badge st={c.status} /></td>
              <td>{c.level}</td>
              <td>{c.price > 0 ? TAKA + c.price : "Free"}</td>
              <td>{c.lessons.length}</td>
              <td>{c.students}</td>
              <td>{c.reviews ? c.rating + " (" + c.reviews + ")" : "-"}</td>
              <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                <Btn tone="ghost" onClick={() => fill(c)}>Edit</Btn>{" "}
                {(c.status === "rejected" || c.status === "unpublished") && (
                  <Btn tone="teal" onClick={() => resubmit(c)}>Resubmit</Btn>)}{" "}
                <a className="btn sm dark" href={"/course/" + c.id}>View</a>{" "}
                <Btn tone="red" onClick={() => drop(c)}>Delete</Btn>
              </td>
            </Row>
          ))}
        </Table>
        {courses.length === 0 && <p className="muted" style={{ padding: 16 }}>No courses yet - create one above.</p>}
      </Panel>
    </>
  );
}
function CoursePick({ courses, sel, setSel }) {
  return (
    <div style={{ marginBottom: 12, maxWidth: 420 }}>
      <label>Course</label>
      <select value={sel} onChange={(e) => setSel(Number(e.target.value))}>
        {courses.map((c) => (
          <option key={c.id} value={c.id}>{c.title} ({c.status})</option>
        ))}
      </select>
    </div>
  );
}

function LessonsTab({ courses, sel, setSel, say, cry, refresh }) {
  const [data, setData] = useState(null);
  const BL = { title: "", description: "", content: "", video_url: "" };
  const [add, setAdd] = useState(BL);
  const [file, setFile] = useState(null);
  const [edit, setEdit] = useState(null);
  const [tick, setTick] = useState(0);
  const id = sel || (courses[0] && courses[0].id) || 0;

  useEffect(() => {
    let stop = false;
    if (!id) { setData(null); return undefined; }
    api("/courses/" + id + "/lessons")
      .then((d) => { if (!stop) setData(d); })
      .catch((e) => { if (!stop) cry(e); });
    return () => { stop = true; };
  }, [id, tick, courses.length]);

  function fdFrom(o) {
    const fd = new FormData();
    fd.append("title", o.title);
    fd.append("description", o.description || "");
    fd.append("content", o.content || "");
    fd.append("video_url", o.video_url || "");
    if (o.file) fd.append("file", o.file);
    return fd;
  }
  async function submitAdd(e) {
    e.preventDefault();
    try {
      await api("/courses/" + id + "/lessons", { method: "POST", body: fdFrom({ ...add, file }) });
      say("Lesson added to '" + data.course + "'.");
      setAdd(BL); setFile(null); setTick((t) => t + 1); refresh();
    } catch (e2) { cry(e2); }
  }
  async function submitEdit(e) {
    e.preventDefault();
    try {
      await api("/lessons/" + edit.id, { method: "PUT", body: fdFrom(edit) });
      say("Lesson updated.");
      setEdit(null); setTick((t) => t + 1); refresh();
    } catch (e2) { cry(e2); }
  }
  async function move(l, dir) {
    try {
      await api("/lessons/" + l.id + "/move?direction=" + dir, { method: "PUT" });
      setTick((t) => t + 1);
    } catch (e) { cry(e); }
  }
  async function del(l) {
    if (!confirm("Delete lesson: " + l.title + "?")) return;
    try {
      await api("/lessons/" + l.id, { method: "DELETE" });
      say("Lesson deleted."); setTick((t) => t + 1); refresh();
    } catch (e) { cry(e); }
  }
  const busy = (
    <Panel title="Lessons" sub="Pick a course, then add, edit, reorder or remove lessons.">
      <CoursePick courses={courses} sel={id} setSel={setSel} />
      {!courses.length && <p className="muted">Create a course first.</p>}
    </Panel>
  );
  if (!data) return busy;
  return (
    <>
      <CoursePick courses={courses} sel={id} setSel={setSel} />
      <Panel title="Add a lesson" sub={data.course + " - " + data.lessons.length + " lesson(s)"}>
        <form onSubmit={submitAdd}>
          <div className="grid g2">
            <Field label="Lesson title">
              <input required value={add.title} onChange={(e) => setAdd({ ...add, title: e.target.value })} />
            </Field>
            <Field label="Video link (YouTube URL)" hint="Optional - embedded inside the lesson.">
              <input value={add.video_url} onChange={(e) => setAdd({ ...add, video_url: e.target.value })}
                placeholder="https://www.youtube.com/watch?v=..." />
            </Field>
            <Field label="Short summary" col="1 / span 2">
              <input value={add.description} onChange={(e) => setAdd({ ...add, description: e.target.value })} />
            </Field>
            <Field label="Lesson notes" col="1 / span 2" hint="Learners read this inside the course player.">
              <textarea rows={4} value={add.content} onChange={(e) => setAdd({ ...add, content: e.target.value })} />
            </Field>
            <Field label="Attachment (PDF, slides, code zip)">
              <input type="file" onChange={(e) => setFile(e.target.files[0])} />
            </Field>
          </div>
          <button className="btn sm" style={{ marginTop: 12 }} type="submit">Add lesson</button>
        </form>
      </Panel>
      {edit && (
        <Panel title={"Edit lesson #" + edit.id}>
          <form onSubmit={submitEdit}>
            <div className="grid g2">
              <Field label="Lesson title" col="1 / span 2">
                <input value={edit.title} onChange={(e) => setEdit({ ...edit, title: e.target.value })} />
              </Field>
              <Field label="Short summary" col="1 / span 2">
                <input value={edit.description} onChange={(e) => setEdit({ ...edit, description: e.target.value })} />
              </Field>
              <Field label="Lesson notes" col="1 / span 2">
                <textarea rows={4} value={edit.content} onChange={(e) => setEdit({ ...edit, content: e.target.value })} />
              </Field>
              <Field label="Video link">
                <input value={edit.video_url} onChange={(e) => setEdit({ ...edit, video_url: e.target.value })} />
              </Field>
              <Field label="Replace attachment (optional)">
                <input type="file" onChange={(e) => setEdit({ ...edit, file: e.target.files[0] })} />
              </Field>
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button className="btn sm" type="submit">Save lesson</button>
              <button className="btn sm ghost" type="button" onClick={() => setEdit(null)}>Cancel</button>
            </div>
          </form>
        </Panel>
      )}
      <Panel title="Lesson outline" pad={false}>
        <Table head={["#", "Lesson", "Content", "Completed by", ""]}>
          {data.lessons.map((l, i) => (
            <Row key={l.id}>
              <td>{i + 1}</td>
              <td><b style={{ fontSize: 13 }}>{l.title}</b>{l.description && <p className="muted" style={{ margin: "2px 0 0" }}>{l.description}</p>}</td>
              <td style={{ fontSize: 12 }}>
                {l.content && <span className="pill">notes</span>}{" "}{l.video_url && <span className="pill">video</span>}{" "}{l.file && <span className="pill">file</span>}
              </td>
              <td>{l.done_by} learner(s)</td>
              <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                <Btn tone="ghost" onClick={() => move(l, "up")}>Up</Btn>{" "}
                <Btn tone="ghost" onClick={() => move(l, "down")}>Down</Btn>{" "}
                <Btn tone="teal" onClick={() => setEdit({ ...l, file: null })}>Edit</Btn>{" "}
                <Btn tone="red" onClick={() => del(l)}>Delete</Btn>
              </td>
            </Row>
          ))}
        </Table>
        {data.lessons.length === 0 && <p className="muted" style={{ padding: 16 }}>No lessons yet - add one above.</p>}
      </Panel>
    </>
  );
}

function StudentsTab({ courses, sel, setSel, cry }) {
  const [roster, setRoster] = useState(null);
  const id = sel || (courses[0] && courses[0].id) || 0;
  useEffect(() => {
    let stop = false;
    if (!id) { setRoster(null); return undefined; }
    api("/courses/" + id + "/students").then((d) => { if (!stop) setRoster(d); }).catch(cry);
    return () => { stop = true; };
  }, [id, courses.length]);
  if (!courses.length) return <Panel title="Students">Create a course and enroll learners first.</Panel>;
  return (
    <Panel title="Who is learning" sub={roster ? roster.course + " - " + roster.count + " enrolled" : "Loading..."} pad={false}
      right={<select value={id} onChange={(e) => setSel(Number(e.target.value))} style={{ maxWidth: 260 }}>
        {courses.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
      </select>}>
      {roster && (
        <Table head={["Learner", "Progress", "Status", "Enrolled", "Avg grade", ""]}>
          {roster.students.map((s) => (
            <Row key={s.user_id}>
              <td><b style={{ fontSize: 13 }}>{s.name}</b><p className="muted" style={{ margin: 0 }}>{s.email}</p></td>
              <td style={{ minWidth: 120 }}><div className="bar"><i style={{ width: s.progress + "%" }} /></div><span className="muted">{s.progress}%</span></td>
              <td>{s.completed ? <Badge st="published" /> : <Badge st="pending" />}</td>
              <td>{s.enrolled}</td>
              <td>{s.graded_avg === null ? "-" : s.graded_avg}</td>
              <td style={{ textAlign: "right" }}><a className="btn sm ghost" href={"/chat?to=" + s.user_id}>Message</a></td>
            </Row>
          ))}
        </Table>
      )}
      {roster && roster.students.length === 0 && <p className="muted" style={{ padding: 16 }}>Nobody enrolled yet - share your course link.</p>}
    </Panel>
  );
}
function AssessTab({ courses, say, cry, refresh }) {
  const quizzes = [];
  const assignments = [];
  courses.forEach((c) => {
    (c.quizzes || []).forEach((q) => quizzes.push({ ...q, course: c.title }));
    (c.assignments || []).forEach((a) => assignments.push({ ...a, course: c.title }));
  });
  const [qid, setQid] = useState(0);
  const [aid, setAid] = useState(0);
  const [res, setRes] = useState(null);
  const [subs, setSubs] = useState(null);
  const [grades, setGrades] = useState({});
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!qid && quizzes.length) setQid(quizzes[0].id);
    if (!aid && assignments.length) setAid(assignments[0].id);
  }, [courses.length]);
  useEffect(() => {
    let stop = false;
    if (qid) api("/quizzes/" + qid + "/results").then((d) => { if (!stop) setRes(d); }).catch(cry);
    return () => { stop = true; };
  }, [qid, tick]);
  useEffect(() => {
    let stop = false;
    if (aid) api("/assignments/" + aid + "/submissions").then((d) => { if (!stop) setSubs(d); }).catch(cry);
    return () => { stop = true; };
  }, [aid, tick]);

  function setG(sid, k, v) { setGrades((g) => ({ ...g, [sid]: { ...(g[sid] || {}), [k]: v } })); }
  async function grade(sid, marks) {
    const g = grades[sid] || {};
    try {
      await api("/assignments/submissions/" + sid + "/grade", {
        method: "PUT",
        body: { grade: Number(g.grade || 0), feedback: g.feedback || "" },
      });
      say("Grade saved - the learner has been notified.");
      setTick((t) => t + 1);
      refresh();
    } catch (e) { cry(e); }
  }
  if (!courses.length) return <Panel title="Quizzes and assignments">Create a course first.</Panel>;
  return (
    <>
      <Panel title="Assignment grading" sub={subs ? subs.assignment + " - " + subs.ungraded + " waiting to be graded" : "Pick an assignment"}>
        <div style={{ maxWidth: 420 }}>
          <label>Assignment</label>
          <select value={aid} onChange={(e) => setAid(Number(e.target.value))}>
            {assignments.map((a) => <option key={a.id} value={a.id}>{a.course} - {a.title}</option>)}
          </select>
          {assignments.length === 0 && <p className="muted">No assignments yet - build one below.</p>}
        </div>
        {subs && (
          <Table head={["Learner", "Submitted", "Note / file", "Grade", "Feedback", ""]}>
            {subs.submissions.map((x) => (
              <Row key={x.id}>
                <td>{x.learner}</td>
                <td>{x.submitted}{x.draft && <Badge st="draft" />}</td>
                <td style={{ maxWidth: 220, fontSize: 12 }}>
                  {x.comment && <p style={{ margin: 0 }}>{x.comment}</p>}
                  {x.file && <a href={"/files/" + x.file} target="_blank" rel="noreferrer">attachment</a>}
                </td>
                <td>
                  <input type="number" min="0" max={x.marks} style={{ width: 80 }}
                    defaultValue={x.grade === null ? "" : x.grade}
                    onChange={(e) => setG(x.id, "grade", e.target.value)} />
                  <span className="muted"> / {x.marks}</span>
                </td>
                <td>
                  <input placeholder="Feedback for the learner"
                    defaultValue={x.feedback}
                    onChange={(e) => setG(x.id, "feedback", e.target.value)} />
                </td>
                <td style={{ textAlign: "right" }}>
                  <Btn onClick={() => grade(x.id, x.marks)}>Save</Btn>
                </td>
              </Row>
            ))}
          </Table>
        )}
        {subs && subs.submissions.length === 0 && <p className="muted">No submissions for this assignment yet.</p>}
      </Panel>
      <Panel title="Quiz analytics" sub={res ? res.quiz + " - " + res.takers + " attempt row(s), avg " + res.avg_score + "%, pass rate " + res.pass_rate + "%" : "Pick a quiz"}>
        <div style={{ maxWidth: 420 }}>
          <label>Quiz</label>
          <select value={qid} onChange={(e) => setQid(Number(e.target.value))}>
            {quizzes.map((q) => <option key={q.id} value={q.id}>{q.course} - {q.title}{q.published ? "" : " (draft)"}</option>)}
          </select>
          {quizzes.length === 0 && <p className="muted">No quizzes yet - build one below.</p>}
        </div>
        {res && (
          <Table head={["Learner", "Score", "Result", "Attempts", "Date"]}>
            {res.results.map((r, i) => (
              <Row key={i}>
                <td>{r.learner}</td>
                <td>{r.score}%</td>
                <td>{r.passed ? <Badge st="published" /> : <Badge st="rejected" />}</td>
                <td>{r.attempts}</td>
                <td>{r.date}</td>
              </Row>
            ))}
          </Table>
        )}
      </Panel>
      <AssessBuilder courses={courses} onDone={() => { refresh(); setTick((t) => t + 1); }} />
    </>
  );
}

function ReviewsTab({ courses, say, cry, refresh }) {
  const [rows, setRows] = useState([]);
  const [reply, setReply] = useState({});
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let stop = false;
    Promise.all(courses.map((c) => api("/courses/" + c.id + "/reviews")
      .then((d) => d.reviews.map((r) => ({ ...r, course: c.title, course_id: c.id })))
      .catch(() => [])))
      .then((all) => { if (!stop) setRows([].concat.apply([], all)); });
    return () => { stop = true; };
  }, [courses.length, tick]);
  async function send(r) {
    const text = (reply[r.id] || "").trim();
    if (!text) { cry(new Error("Write a reply first.")); return; }
    try {
      await api("/reviews/" + r.id + "/reply", { method: "POST", body: { reply: text } });
      say("Reply posted - the learner was notified.");
      setReply((p) => ({ ...p, [r.id]: "" }));
      setTick((t) => t + 1);
      refresh();
    } catch (e) { cry(e); }
  }
  if (!courses.length) return <Panel title="Learner reviews">You need a published course first.</Panel>;
  return (
    <Panel title="Learner reviews" sub={rows.length + " review(s) across your courses"}>
      {rows.length === 0 && <p className="muted">No reviews yet.</p>}
      {rows.map((r) => (
        <div key={r.id} style={{ border: "1px solid var(--line)", borderRadius: 14, padding: 12, marginBottom: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
            <b style={{ fontSize: 13 }}>{r.name} - {"*".repeat(r.rating)} on {r.course}</b>
            <span className="muted">{r.date}</span>
          </div>
          <p style={{ margin: "6px 0" }}>{r.comment || "(no comment)"}</p>
          {r.reply ? (
            <p className="muted" style={{ margin: 0 }}>Your reply: {r.reply}</p>
          ) : (
            <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
              <input placeholder="Public reply to this review"
                value={reply[r.id] || ""} onChange={(e) => setReply((p) => ({ ...p, [r.id]: e.target.value }))} />
              <Btn onClick={() => send(r)}>Reply</Btn>
            </div>
          )}
        </div>
      ))}
    </Panel>
  );
}

function ProfileTab({ langs, say, cry, refresh }) {
  const me = getUser();
  const [p, setP] = useState(null);
  const [rows, setRows] = useState([]);
  const [lgs, setLgs] = useState([]);
  useEffect(() => {
    if (!me) return;
    api("/mentors/" + me.id).then((d) => {
      setP(d);
      setRows((d.skills || []).map((s) => ({ name: s.skill, proficiency: s.proficiency, years: s.years })));
      setLgs((d.langs || []).map((l) => ({ code: l.code, fluency: l.fluency })));
    }).catch(cry);
  }, []);
  function addSkill() { setRows((r) => [...r, { name: "", proficiency: 4, years: 2 }]); }
  async function save(e) {
    e.preventDefault();
    try {
      const d = await api("/mentor/profile", {
        method: "PUT",
        body: { headline: p.headline || "", about: p.about || "", country: p.country || "Bangladesh",
          skills: rows.filter((r) => r.name.trim()), langs: lgs },
      });
      say(d.message + (d.verified ? "" : " (verification badge is granted by the admin team)"));
      refresh();
    } catch (x) { cry(x); }
  }
  if (!p) return <Panel title="Instructor profile">Loading...</Panel>;
  return (
    <Panel title="Instructor profile" sub="This is what learners see on your public page."
      right={<Badge st={p.verified ? "published" : "pending"} />}>
      <form onSubmit={save}>
        <div className="grid g2">
          <Field label="Headline" hint="One line under your name.">
            <input value={p.headline || ""} onChange={(e) => setP({ ...p, headline: e.target.value })}
              placeholder="Senior Python engineer, 8 years teaching" />
          </Field>
          <Field label="Country">
            <input value={p.country || ""} onChange={(e) => setP({ ...p, country: e.target.value })} />
          </Field>
          <Field label="About you" col="1 / span 2">
            <textarea rows={4} value={p.about || ""} onChange={(e) => setP({ ...p, about: e.target.value })} />
          </Field>
        </div>
        <h3 style={{ fontSize: 14, margin: "14px 0 6px" }}>Skills you teach</h3>
        {rows.map((r, i) => (
          <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "center" }}>
            <input style={{ flex: 2 }} placeholder="Skill name (e.g. Python)" value={r.name}
              onChange={(e) => setRows((all) => all.map((x, k) => (k === i ? { ...x, name: e.target.value } : x)))} />
            <select style={{ flex: 1 }} value={r.proficiency}
              onChange={(e) => setRows((all) => all.map((x, k) => (k === i ? { ...x, proficiency: Number(e.target.value) } : x)))}>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>level {n}</option>)}
            </select>
            <input type="number" step="0.5" min="0" style={{ width: 90 }} value={r.years}
              onChange={(e) => setRows((all) => all.map((x, k) => (k === i ? { ...x, years: Number(e.target.value) } : x)))} />
            <Btn tone="ghost" onClick={() => setRows((all) => all.filter((_, k) => k !== i))}>Remove</Btn>
          </div>
        ))}
        <Btn tone="teal" onClick={addSkill}>Add skill</Btn>
        <h3 style={{ fontSize: 14, margin: "14px 0 6px" }}>Teaching languages</h3>
        {langs.map((l) => {
          const on = lgs.find((x) => x.code === l.code);
          return (
            <button type="button" key={l.code} className={"chip" + (on ? " on" : "")}
              style={{ marginRight: 6, marginBottom: 6 }}
              onClick={() => setLgs(on ? lgs.filter((x) => x.code !== l.code)
                : [...lgs, { code: l.code, fluency: "fluent" }])}>
              {l.name}
            </button>
          );
        })}
        <div style={{ marginTop: 14 }}><button className="btn sm" type="submit">Save profile</button></div>
      </form>
    </Panel>
  );
}