"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { getUser, getToken, api, setLocalUser } from "../lib/api";
import { t as translate, dirOf, LANG_META } from "../lib/i18n";

const LangCtx = createContext(null);

function initialLang() {
  if (typeof window === "undefined") return "en";
  const u = getUser();
  return (u && u.lang) || localStorage.getItem("sh_lang") || "en";
}

export function LangProvider({ children }) {
  const [lang, setLangState] = useState("en");

  function applyDoc(l) {
    document.documentElement.lang = l;
    document.documentElement.dir = dirOf(l);
  }

  useEffect(() => {
    const l = initialLang();
    setLangState(l);
    applyDoc(l);
    // Re-sync language whenever auth changes (login / verify / logout) so the
    // account's saved preference is applied without a full page reload.
    function onAuth(e) {
      const u = e.detail;
      const next = (u && u.lang) || localStorage.getItem("sh_lang") || "en";
      setLangState(next);
      localStorage.setItem("sh_lang", next);
      applyDoc(next);
    }
    window.addEventListener("sh-auth", onAuth);
    return () => window.removeEventListener("sh-auth", onAuth);
  }, []);

  function apply(l) {
    setLangState(l);
    localStorage.setItem("sh_lang", l);
    applyDoc(l);
    const u = getUser();
    if (u && getToken()) {
      try { api("/auth/profile", { method: "PUT", body: { lang: l } }); } catch (e) {}
      setLocalUser({ ...u, lang: l });
    }
  }

  const value = {
    lang,
    dir: dirOf(lang),
    setLang: apply,
    tr: (key) => translate(lang, key),
  };
  return <LangCtx.Provider value={value}>{children}</LangCtx.Provider>;
}

export function useLang() {
  const c = useContext(LangCtx);
  if (!c) return { lang: "en", dir: "ltr", setLang: () => {}, tr: (k) => k };
  return c;
}
// Convenience hook: returns the translate function bound to the active language.
export function useT() {
  return useLang().tr;
}
export { LANG_META };