const themeToggle = document.querySelector("[data-theme-toggle]");

function setTheme(theme){
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("gmi_theme", theme);
  if (themeToggle) {
    themeToggle.classList.toggle("active", theme === "light");
  }
}

function currentTheme(){
  return document.documentElement.getAttribute("data-theme") || "dark";
}

function initTheme(){
  const saved = localStorage.getItem("gmi_theme") || "dark";
  setTheme(saved);
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    setTheme(next);
  });
}

initTheme();
