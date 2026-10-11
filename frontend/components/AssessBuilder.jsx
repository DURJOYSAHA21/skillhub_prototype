"use client";
import { useState } from "react";
import { api } from "@/lib/api";

const inp = "w-full border border-slate-300 rounded-lg px-3 py-2 text-sm";
const card = "bg-white border border-slate-200 rounded-xl p-5 shadow-sm";
const btn = "bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg";
const btnDark = "bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg";
const btnRed = "bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold px-3 py-1.5 rounded-lg";
const lbl = "text-xs text-slate-500 flex flex-col gap-1";

const blankQ = () => ({ text: "", options: ["", "", "", ""], correct: 0 });

export default function AssessBuilder({ courses, onDone }) {
  const [qe, setQe] = useState({ course_id: "", title: "", min: 15, pass: 60, tries: 3 });
  const [qs, setQs] = useState([blankQ()]);
  const [ae, setAe] = useState({ course_id: "", title: "", instructions: "", due: "", marks: 100 });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const setQ = (i, patch) => setQs(qs.map((q, j) => (j === i ? { ...q, ...patch } : q)));
  const setOpt = (i, j, v) =>
    setQs(qs.map((q, k) => (k !== i ? q : { ...q, options: q.options.map((o, m) => (m === j ? v : o)) })));

  const picker = (val, set) => (
    <select className={inp} value={val} onChange={(e) => set(e.target.value)}>
      <option value="">Pick course...</option>
      {courses.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}
    </select>
  );

  async function createQuiz(e) {
    e.preventDefault(); setErr(""); setMsg("");
    if (!qe.course_id) { setErr("Pick a course for the quiz first."); return; }
    try {
      const d = await api("/courses/" + qe.course_id + "/quizzes", {
        method: "POST",
        body: {
          title: qe.title, time_limit_min: Number(qe.min),
          passing_score: Number(qe.pass), max_attempts: Number(qe.tries),
          questions: qs.map((q) => ({ text: q.text, options: q.options, correct: q.correct })),
        },
      });
      setMsg("Quiz saved (id " + d.quiz_id + ", " + d.questions + (d.questions === 1 ? " question" : " questions") + ").");
      setQe({ ...qe, title: "" }); setQs([blankQ()]);
      if (onDone) onDone();
    } catch (x) { setErr(x.message); }
  }

  async function createAssignment(e) {
    e.preventDefault(); setErr(""); setMsg("");
    if (!ae.course_id) { setErr("Pick a course for the assignment first."); return; }
    try {
      const d = await api("/courses/" + ae.course_id + "/assignments", {
        method: "POST",
        body: { title: ae.title, instructions: ae.instructions, due: ae.due, marks: Number(ae.marks) },
      });
      setMsg("Assignment saved (id " + d.assignment_id + ").");
      setAe({ ...ae, title: "", instructions: "", due: "" });
      if (onDone) onDone();
    } catch (x) { setErr(x.message); }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      <form onSubmit={createQuiz} className={card}>
        <h2 className="font-semibold mb-1">Build a quiz</h2>
        <p className="text-xs text-slate-400 mb-3">Four options per question - tick the radio beside the right answer.</p>
        {picker(qe.course_id, (v) => setQe({ ...qe, course_id: v }))}
        <input className={inp + " mt-2"} placeholder="Quiz title" value={qe.title}
          onChange={(e) => setQe({ ...qe, title: e.target.value })} />
        <div className="grid grid-cols-3 gap-2 mt-2">
          <label className={lbl}>Minutes<input className={inp} type="number" min="1" value={qe.min}
            onChange={(e) => setQe({ ...qe, min: e.target.value })} /></label>
          <label className={lbl}>Pass %<input className={inp} type="number" min="0" max="100" value={qe.pass}
            onChange={(e) => setQe({ ...qe, pass: e.target.value })} /></label>
          <label className={lbl}>Attempts<input className={inp} type="number" min="1" value={qe.tries}
            onChange={(e) => setQe({ ...qe, tries: e.target.value })} /></label>
        </div>
        {qs.map((q, i) => (
          <div key={i} className="border border-slate-200 rounded-lg p-3 mt-3">
            <div className="flex justify-between items-center">
              <b className="text-xs text-slate-500">QUESTION {i + 1}</b>
              {qs.length > 1 && (
                <button type="button" className={btnRed} onClick={() => setQs(qs.filter((_, j) => j !== i))}>Remove</button>
              )}
            </div>
            <input className={inp + " mt-2"} placeholder="Question text" value={q.text}
              onChange={(e) => setQ(i, { text: e.target.value })} />
            {q.options.map((o, j) => (
              <div key={j} className="flex items-center gap-2 mt-2">
                <input type="radio" style={{ width: "auto" }} name={"qc" + i} checked={q.correct === j}
                  onChange={() => setQ(i, { correct: j })} />
                <input className={inp} placeholder={"Option " + (j + 1)} value={o}
                  onChange={(e) => setOpt(i, j, e.target.value)} />
              </div>
            ))}
          </div>
        ))}
        <div className="mt-3">
          <button type="button" className={btnDark} onClick={() => setQs([...qs, blankQ()])}>+ Add question</button>
          <button type="submit" className={btn + " ml-2"}>Save quiz</button>
        </div>
      </form>
      <form onSubmit={createAssignment} className={card + " self-start"}>
        <h2 className="font-semibold mb-1">Set an assignment</h2>
        <p className="text-xs text-slate-400 mb-3">Learners submit files and notes against it from the course page.</p>
        {picker(ae.course_id, (v) => setAe({ ...ae, course_id: v }))}
        <input className={inp + " mt-2"} placeholder="Assignment title" value={ae.title}
          onChange={(e) => setAe({ ...ae, title: e.target.value })} />
        <textarea className={inp + " mt-2"} rows={5} placeholder="Instructions" value={ae.instructions}
          onChange={(e) => setAe({ ...ae, instructions: e.target.value })} />
        <div className="grid grid-cols-2 gap-2 mt-2">
          <label className={lbl}>Due date<input className={inp} type="date" value={ae.due}
            onChange={(e) => setAe({ ...ae, due: e.target.value })} /></label>
          <label className={lbl}>Marks<input className={inp} type="number" min="1" value={ae.marks}
            onChange={(e) => setAe({ ...ae, marks: e.target.value })} /></label>
        </div>
        <button type="submit" className={btn + " mt-3"}>Save assignment</button>
      </form>
      {err && <div className="lg:col-span-2 p-3 rounded-lg bg-rose-50 text-rose-700 text-sm">{err}</div>}
      {msg && <div className="lg:col-span-2 p-3 rounded-lg bg-emerald-50 text-emerald-700 text-sm">{msg}</div>}
    </div>
  );
}