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
}
export function setLocalUser(u) {
  localStorage.setItem("sh_user", JSON.stringify(u));
}
export function logout() {
  localStorage.removeItem("sh_token");
  localStorage.removeItem("sh_user");
}
export async function api(path, opts = {}) {
  const headers = opts.headers || {};
  const isForm = opts.body instanceof FormData;
  if (opts.body && !isForm) headers["Content-Type"] = "application/json";
  const t = getToken();
  if (t) headers["Authorization"] = "Bearer " + t;
  const r = await fetch(API + path, {
    ...opts, headers,
    body: opts.body && !isForm ? JSON.stringify(opts.body) : opts.body,
  });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d.detail || "HTTP " + r.status);
  return d;
}
export function pdfUrl(path) {
  return API + path + "?t=" + encodeURIComponent(getToken());
}
