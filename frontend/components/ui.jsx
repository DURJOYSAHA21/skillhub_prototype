"use client";
/* Small design-system helpers shared by the three role consoles. */

export function Panel({ title, sub, right, children, pad }) {
  return (
    <div className="panel" style={pad === false ? { padding: 0 } : undefined}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 17, fontWeight: 800 }}>{title}</h2>
          {sub && <p className="muted" style={{ margin: "3px 0 0" }}>{sub}</p>}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>{right}</div>
      </div>
      <div style={{ marginTop: 14 }}>{children}</div>
    </div>
  );
}

export function Kpi({ label, value, hint, color }) {
  return (
    <div className="kpi">
      <b style={color ? { color } : undefined}>{value}</b>
      <p style={{ margin: "2px 0 0", fontSize: 12, fontWeight: 700, color: "#4c4a63" }}>{label}</p>
      {hint && <p style={{ margin: "2px 0 0", fontSize: 11, color: "#7d7b95" }}>{hint}</p>}
    </div>
  );
}

export function KpiRow({ items, cols = 4 }) {
  return (
    <div className={"grid g" + cols} style={{ marginBottom: 6 }}>
      {items.map((k) => <Kpi key={k.label} {...k} />)}
    </div>
  );
}

export function Tabs({ tabs, view, setView }) {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "4px 0 10px" }}>
      {tabs.map((t) => (
        <button key={t.id} className={"chip" + (view === t.id ? " on" : "")}
          onClick={() => setView(t.id)}>{t.label}
          {t.badge > 0 && <b style={{ marginLeft: 6, color: t.id === view ? "#fff" : "#c0392b" }}>{t.badge}</b>}
        </button>
      ))}
    </div>
  );
}

export function Msg({ err, msg }) {
  return (
    <>
      {err && <div className="err">{err}</div>}
      {msg && <div className="ok">{msg}</div>}
    </>
  );
}

export function Field({ label, hint, children, col }) {
  return (
    <div style={col ? { gridColumn: col } : undefined}>
      <label>{label}</label>
      {children}
      {hint && <p style={{ fontSize: 11, color: "#8a8aa0", margin: "3px 0 0" }}>{hint}</p>}
    </div>
  );
}

export function Badge({ st }) {
  const map = { published: "b-pub", pending: "b-pend", rejected: "b-rej",
    inactive: "b-rej", refunded: "b-pend", unpublished: "b-pend",
    active: "b-pub", unverified: "b-pend", draft: "b-pend" };
  return <span className={"badge " + (map[st] || "b-role")}>{st}</span>;
}

export function Bar({ pct }) {
  return (
    <div className="bar"><i style={{ width: (pct || 0) + "%" }} /></div>
  );
}

export function Table({ head, children, empty }) {
  const n = head.length;
  return (
    <div style={{ overflowX: "auto" }}>
      <table>
        <thead><tr>{head.map((h) => <th key={h}>{h}</th>)}</tr></thead>
        <tbody>
          {children}
          {empty && <tr><td colSpan={n} style={{ color: "#8a8aa0" }}>{empty}</td></tr>}
        </tbody>
      </table>
    </div>
  );
}

export function Row({ children, last }) {
  return (
    <tr style={{ borderBottom: last ? "none" : "1px solid #eceaf4" }}>{children}</tr>
  );
}

export function Btn({ tone, sm, type = "button", children, ...rest }) {
  return (
    <button type={type} className={"btn" + (tone ? " " + tone : "") + (sm === false ? "" : " sm")}
      {...rest}>{children}</button>
  );
}

export function Muted({ children }) {
  return <p className="muted" style={{ margin: 0 }}>{children}</p>;
}