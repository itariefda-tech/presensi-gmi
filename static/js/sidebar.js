const shell = document.querySelector(".shell");
const toggleBtn = document.getElementById("btnToggleSidebar");
const STORAGE_KEY = "gmi_sidebar_collapsed";

function setCollapsed(collapsed){
  if (!shell) return;
  shell.classList.toggle("sidebar-collapsed", collapsed);
  try {
    localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
  } catch (err) {
    // Ignore storage failures.
  }
}

function initSidebar(){
  let collapsed = false;
  try {
    collapsed = localStorage.getItem(STORAGE_KEY) === "1";
  } catch (err) {
    collapsed = false;
  }
  setCollapsed(collapsed);
}

toggleBtn?.addEventListener("click", () => {
  const collapsed = !shell?.classList.contains("sidebar-collapsed");
  setCollapsed(collapsed);
});

initSidebar();
