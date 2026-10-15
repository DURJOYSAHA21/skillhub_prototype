"use client";
import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import MentorStudio from "@/components/MentorStudio";
import LearnerHub from "@/components/LearnerHub";
import AdminConsole from "@/components/AdminConsole";
import { getUser, getToken } from "@/lib/api";

const TITLES = {
  mentor: ["Mentor Studio", "Create courses, manage lessons, grade work and answer reviews."],
  learner: ["Learner Hub", "Track progress, results, certificates, notes and payments."],
  admin: ["Admin Console", "Approve courses, manage users, payments, reviews and reports."],
};

export default function DashboardPage() {
  const [u, setU] = useState(undefined);
  useEffect(() => { setU(getUser()); }, []);
  if (u === undefined) {
    return <><Nav /><main className="wrap"><p className="muted">Loading your dashboard...</p></main></>;
  }
  if (!u || !getToken()) {
    return (
      <>
        <Nav />
        <main className="wrap">
          <div className="panel">
            <h2>Please log in</h2>
            <p className="muted">Your dashboard needs an account. Demo: admin@skillhub.dev / Admin123, rifat@skillhub.dev / Mentor123, learner@skillhub.dev / Learner123.</p>
            <a className="btn sm" href="/login">Log in</a>
          </div>
        </main>
      </>
    );
  }
  const [title, sub] = TITLES[u.role] || ["Dashboard", ""];
  return (
    <>
      <Nav />
      <main className="wrap">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: 10 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 26, fontWeight: 900 }}>{title}</h1>
            <p className="muted" style={{ margin: "4px 0 0" }}>{sub}</p>
          </div>
          <p className="muted" style={{ margin: 0 }}>Signed in as <b>{u.name}</b> ({u.role})</p>
        </div>
        <div style={{ marginTop: 18 }}>
          {u.role === "mentor" && <MentorStudio />}
          {u.role === "learner" && <LearnerHub />}
          {u.role === "admin" && <AdminConsole />}
        </div>
      </main>
    </>
  );
}