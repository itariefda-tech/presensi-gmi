const themeToggle = document.querySelector("[data-theme-toggle]");
const THEME_OPTIONS = ["dark", "light", "sage_calm", "silver_line", "noir_warm"];

function normalizeTheme(theme){
  return THEME_OPTIONS.includes(theme) ? theme : "silver_line";
}

function csrfToken(){
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") || "" : "";
}

function persistTheme(theme){
  const token = csrfToken();
  if (!token || typeof fetch !== "function") return;
  fetch("/api/user/theme", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": token,
    },
    body: JSON.stringify({ theme }),
  }).catch(() => {});
}

function setTheme(theme, options = {}){
  const normalized = normalizeTheme(theme);
  const shouldPersist = options.persist !== false;
  document.documentElement.setAttribute("data-theme", normalized);
  localStorage.setItem("gmi_theme", normalized);
  localStorage.setItem("theme", normalized);
  if (themeToggle) {
    themeToggle.classList.toggle("active", normalized === "light");
    themeToggle.setAttribute("data-current-theme", normalized);
    themeToggle.setAttribute("title", `Theme: ${normalized}`);
  }
  updateThemeControls(normalized);
  if (shouldPersist) persistTheme(normalized);
  window.dispatchEvent(new CustomEvent("gmi:theme-applied", { detail: { theme: normalized } }));
}

function currentTheme(){
  return normalizeTheme(document.documentElement.getAttribute("data-theme") || "silver_line");
}

function initTheme(){
  const initial = document.documentElement.getAttribute("data-theme") || localStorage.getItem("theme") || localStorage.getItem("gmi_theme") || "silver_line";
  setTheme(initial, { persist: false });
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    setTheme(next);
  });
}

function updateThemeControls(theme){
  document.querySelectorAll("[data-theme-select]").forEach((select) => {
    const hasOption = Array.from(select.options).some((option) => option.value === theme);
    const value = hasOption ? theme : "silver_line";
    if (select.value !== value) select.value = value;
  });
  document.querySelectorAll("[data-theme-choice]").forEach((button) => {
    const active = normalizeTheme(button.dataset.themeChoice) === theme;
    button.setAttribute("aria-pressed", String(active));
  });
}

document.querySelectorAll("[data-theme-select]").forEach((select) => {
  select.addEventListener("change", () => setTheme(select.value));
});

document.querySelectorAll("[data-theme-choice]").forEach((button) => {
  button.addEventListener("click", () => setTheme(button.dataset.themeChoice));
});

window.GMITheme = { setTheme, currentTheme, options: THEME_OPTIONS.slice() };

initTheme();
