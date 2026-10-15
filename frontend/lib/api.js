export const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8030";
export function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("sh_token") || "";
}
export function getUser() {
  if (typeof window === "undefined") return null;
  try { return JSON.parse(localStorage.getItem("sh_user") || "null"); }
  catch (e) { return null; }
}
export function saveAuth(d) {
  localStorage.setItem("sh_token", d.token);
  localStorage.setItem("sh_user", JSON.stringify(d.user));
  // Notify the language provider so the account's saved language is applied
  // immediately after a client-side login/verify (no full reload).
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("sh-auth", { detail: d.user || null }));
  }
}
export function setLocalUser(u) {
  localStorage.setItem("sh_user", JSON.stringify(u));
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("sh-auth", { detail: u || null }));
  }
}
export function logout() {
  localStorage.removeItem("sh_token");
  localStorage.removeItem("sh_user");
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("sh-auth", { detail: null }));
  }
}
// body may be: a plain object (sent as JSON), a FormData (multipart),
// a string (treated as JSON text), or null.
export async function api(path, opts = {}) {
  const headers = Object.assign({}, opts.headers || {});
  let body = opts.body;
  if (body instanceof FormData) {
    // browser sets the multipart boundary itself
  } else if (body !== undefined && body !== null) {
    if (typeof body !== "string") body = JSON.stringify(body);
    if (!headers["Content-Type"]) headers["Content-Type"] = "application/json";
  }
  const t = getToken();
  if (t) headers["Authorization"] = "Bearer " + t;
  const r = await fetch(API + path, { ...opts, headers, body });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) {
    const det = d && d.detail;
    const msg = typeof det === "string" ? det
      : Array.isArray(det) ? (det[0] && det[0].msg) || "Invalid input"
      : "HTTP " + r.status;
    throw new Error(msg);
  }
  return d;
}
export function pdfUrl(path) {
  return API + path + "?t=" + encodeURIComponent(getToken());
}
// Open an authenticated binary response (PDF receipt / certificate) in a new tab.
export async function viewPdf(path) {
  const r = await fetch(API + path, { headers: { Authorization: "Bearer " + getToken() } });
  if (!r.ok) {
    const d = await r.json().catch(() => ({}));
    throw new Error(typeof d.detail === "string" ? d.detail : "Not available yet.");
  }
  const b = await r.blob();
  window.open(URL.createObjectURL(b));
}

// Download an authenticated file (CSV export).
export async function downloadFile(path, filename) {
  const r = await fetch(API + path, { headers: { Authorization: "Bearer " + getToken() } });
  if (!r.ok) {
    const d = await r.json().catch(() => ({}));
    throw new Error(typeof d.detail === "string" ? d.detail : "Download failed.");
  }
  const b = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(b);
  a.download = filename || "skillhub.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}