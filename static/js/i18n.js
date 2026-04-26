(function () {
  "use strict";

  const STORAGE_KEY = "gmi_language";
  const DEFAULT_LANG = "id";
  const SUPPORTED_LANGS = new Set(["id", "en"]);
  const dictionaries = {};

  function normalizeLang(lang) {
    const value = String(lang || "").toLowerCase().slice(0, 2);
    return SUPPORTED_LANGS.has(value) ? value : DEFAULT_LANG;
  }

  function savedLang() {
    try {
      return normalizeLang(localStorage.getItem(STORAGE_KEY) || DEFAULT_LANG);
    } catch (err) {
      return DEFAULT_LANG;
    }
  }

  async function loadDictionary(lang) {
    const normalized = normalizeLang(lang);
    if (dictionaries[normalized]) return dictionaries[normalized];
    const response = await fetch(`/static/i18n/${normalized}.json`, { cache: "no-cache" });
    if (!response.ok) throw new Error(`Unable to load language: ${normalized}`);
    dictionaries[normalized] = await response.json();
    return dictionaries[normalized];
  }

  function textFor(dict, key) {
    if (!key) return null;
    const value = dict[key];
    return typeof value === "string" ? value : null;
  }

  function applyDictionary(dict) {
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      const value = textFor(dict, node.getAttribute("data-i18n"));
      if (value !== null) node.textContent = value;
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
      const value = textFor(dict, node.getAttribute("data-i18n-placeholder"));
      if (value !== null) node.setAttribute("placeholder", value);
    });
    document.querySelectorAll("[data-i18n-title]").forEach((node) => {
      const value = textFor(dict, node.getAttribute("data-i18n-title"));
      if (value !== null) node.setAttribute("title", value);
    });
    document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
      const value = textFor(dict, node.getAttribute("data-i18n-aria-label"));
      if (value !== null) node.setAttribute("aria-label", value);
    });
  }

  function updateSwitch(lang) {
    document.documentElement.setAttribute("lang", lang);
    document.body?.setAttribute("data-lang", lang);
    document.querySelectorAll("[data-lang-value]").forEach((button) => {
      const isActive = normalizeLang(button.getAttribute("data-lang-value")) === lang;
      button.setAttribute("aria-pressed", String(isActive));
    });
  }

  async function applyLang(lang) {
    const normalized = normalizeLang(lang);
    const dict = await loadDictionary(normalized);
    applyDictionary(dict);
    updateSwitch(normalized);
    window.dispatchEvent(new CustomEvent("gmi:language-applied", { detail: { lang: normalized } }));
    return normalized;
  }

  async function setLang(lang) {
    const normalized = normalizeLang(lang);
    try {
      localStorage.setItem(STORAGE_KEY, normalized);
    } catch (err) {}
    return applyLang(normalized);
  }

  function bindSwitches() {
    document.querySelectorAll("[data-lang-switch] [data-lang-value]").forEach((button) => {
      button.addEventListener("click", () => {
        setLang(button.getAttribute("data-lang-value"));
      });
    });
  }

  window.applyLang = applyLang;
  window.setLang = setLang;

  document.addEventListener("DOMContentLoaded", () => {
    bindSwitches();
    applyLang(savedLang()).catch(() => updateSwitch(DEFAULT_LANG));
  });
})();
