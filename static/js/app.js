/* =========================
   SLIDER NAV
   order: 0 emp, 1 admin, 2 signup, 3 forgot
========================= */
const track = document.getElementById("track");
const panes = Array.from(document.querySelectorAll(".pane"));
const paneCount = panes.length || 1;
let index = 0;

function go(i){
  index = Math.max(0, Math.min(paneCount - 1, i));
  const step = 100 / paneCount;
  track.style.transform = `translateX(-${index * step}%)`;
  if (window.matchMedia("(max-width: 900px)").matches) {
    document.querySelector(".card").scrollIntoView({behavior:"smooth", block:"start"});
  }
  randomizeCircles();
  animateCircle();
}

document.querySelectorAll("[data-go]").forEach(el => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    go(parseInt(el.dataset.go, 10));
  });
});

/* =========================
   THEME (persist + send to backend)
========================= */
const themeBtns = Array.from(document.querySelectorAll(".themeBtn"));
const themeInputs = [
  document.getElementById("themeEmp"),
  document.getElementById("themeAdmin"),
  document.getElementById("themeSignup"),
  document.getElementById("themeForgot"),
];

function setTheme(theme){
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("gmi_theme", theme);
  themeBtns.forEach(b => b.classList.toggle("active", b.dataset.theme === theme));
  themeInputs.forEach(inp => { if (inp) inp.value = theme; });
}

themeBtns.forEach(btn => {
  btn.addEventListener("click", () => setTheme(btn.dataset.theme));
});

const initialTheme = window.__GMI_INITIAL_THEME || document.documentElement.getAttribute("data-theme") || "dark";
const savedTheme = localStorage.getItem("gmi_theme") || initialTheme;
setTheme(savedTheme);

function currentTheme(){
  return document.documentElement.getAttribute("data-theme") || "dark";
}

/* =========================
   CLOCK (HH:MM, blink ':', no seconds)
========================= */
const hhEl = document.getElementById("hh");
const mmEl = document.getElementById("mm");
const dateText = document.getElementById("dateText");

function pad2(n){ return String(n).padStart(2,"0"); }

function tick(){
  const d = new Date();
  hhEl.textContent = pad2(d.getHours());
  mmEl.textContent = pad2(d.getMinutes());

  const days = ["Min","Sen","Sel","Rab","Kam","Jum","Sab"];
  const months = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
  dateText.textContent = `${days[d.getDay()]}, ${d.getDate()} ${months[d.getMonth()]}`;
}
tick();
setInterval(tick, 1000);

/* =========================
   PASSWORD TOGGLES
========================= */
function togglePass(inputId, btnId){
  const input = document.getElementById(inputId);
  const btn = document.getElementById(btnId);
  if(!input || !btn) return;

  const eyeOpen = '<svg class="eye" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 5c-4.5 0-8.4 2.9-10 7 1.6 4.1 5.5 7 10 7s8.4-2.9 10-7c-1.6-4.1-5.5-7-10-7Zm0 12a5 5 0 1 1 0-10 5 5 0 0 1 0 10Zm0-2.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" fill="currentColor" opacity="0.85"/></svg>';
  const eyeClosed = '<svg class="eye" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m4.2 3 16 16-1.2 1.2-2.3-2.3A12.2 12.2 0 0 1 12 19c-4.5 0-8.4-2.9-10-7a12.7 12.7 0 0 1 3.5-4.9L3 4.2 4.2 3Zm3.2 4.4a10.7 10.7 0 0 0-2.6 3.6c1.4 3.3 4.6 5.5 8.2 5.5 1 0 2-.2 2.8-.5l-2-2A5 5 0 0 1 9.9 10l-2.5-2.6Zm5 1.3 3.9 4A2.5 2.5 0 0 0 12 12.5c0-.6.2-1.2.4-1.8Zm5-2.1 1.6 1.6c.7.9 1.2 1.8 1.6 2.8-1.6 4.1-5.5 7-10 7-.7 0-1.4-.1-2-.2l-1.4-1.4c1 .4 2 .6 3.4.6 3.6 0 6.8-2.2 8.2-5.5a10.7 10.7 0 0 0-1.4-2.3l-.8-.8c-.5-.5-1-.9-1.6-1.2Z" fill="currentColor" opacity="0.85"/></svg>';

  function render(show){
    btn.innerHTML = show ? eyeClosed : eyeOpen;
    btn.setAttribute("aria-label", show ? "Sembunyikan password" : "Lihat password");
  }

  render(false);
  btn.addEventListener("click", () => {
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    render(show);
  });
}
togglePass("empPass","toggleEmpPass");

/* =========================
   TOAST HELPERS
========================= */
function toast(el, msg, type){
  el.classList.remove("ok","err","show");
  el.textContent = msg;
  el.classList.add("show", type === "ok" ? "ok" : "err");
}

function setBusy(form, on){
  form.querySelectorAll("button").forEach(btn => {
    btn.disabled = on;
  });
  form.setAttribute("aria-busy", on ? "true" : "false");
}

async function postJSON(url, payload){
  const res = await fetch(url, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload || {})
  });

  let data = {};
  try { data = await res.json(); } catch (e) { data = {}; }

  const ok = res.ok && data.ok !== false;
  return {
    ok,
    message: data.message || (ok ? "Berhasil." : "Gagal."),
    next: data.next_url || data.next || null
  };
}

/* =========================
   FORM HANDLERS
========================= */
function bindForm(formId, toastId, buildPayload, endpoint){
  const form = document.getElementById(formId);
  const toastEl = document.getElementById(toastId);
  if(!form || !toastEl) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = buildPayload();
    if(!payload) return;

    setBusy(form, true);
    try{
      const result = await postJSON(endpoint, payload);
      toast(toastEl, result.message, result.ok ? "ok" : "err");
      if(result.ok && result.next){
        setTimeout(() => { window.location.href = result.next; }, 350);
      }
    }catch(err){
      toast(toastEl, "Terjadi masalah jaringan.", "err");
    }finally{
      setBusy(form, false);
    }
  });
}

function getValue(id){ return (document.getElementById(id)?.value || "").trim(); }

bindForm(
  "form-emp",
  "toast-emp",
  () => {
    const email = getValue("empEmail");
    const pw = getValue("empPass");
    if(!email || !pw){
      toast(document.getElementById("toast-emp"), "Isi email dan password dulu.", "err");
      return null;
    }
    return { email, password: pw, theme: currentTheme() };
  },
  "/api/auth/login"
);

function bindSignupMultipart(){
  const form = document.getElementById("form-signup");
  const toastEl = document.getElementById("toast-signup");
  if (!form || !toastEl) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const inv = getValue("inviteCode");
    const email = getValue("suEmail");
    const p1 = getValue("suPass");
    const p2 = getValue("suPass2");
    const selfieInput = document.getElementById("suSelfie");
    const selfieFile = selfieInput?.files?.[0];

    if(!inv){
      toast(toastEl, "Kode undangan wajib.", "err");
      return;
    }
    if(!email){
      toast(toastEl, "Email wajib diisi.", "err");
      return;
    }
    if(p1.length < 6){
      toast(toastEl, "Password minimal 6 karakter.", "err");
      return;
    }
    if(p1 !== p2){
      toast(toastEl, "Password tidak sama.", "err");
      return;
    }
    if(!selfieFile){
      toast(toastEl, "Selfie wajib untuk daftar.", "err");
      return;
    }

    const formData = new FormData();
    formData.append("invite_code", inv);
    formData.append("email", email);
    formData.append("password", p1);
    formData.append("password2", p2);
    formData.append("theme", currentTheme());
    formData.append("selfie", selfieFile);

    setBusy(form, true);
    try{
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        body: formData,
      });
      let data = {};
      try { data = await res.json(); } catch (err) { data = {}; }
      const ok = res.ok && data.ok !== false;
      toast(toastEl, data.message || (ok ? "Berhasil." : "Gagal."), ok ? "ok" : "err");
      if (ok) {
        form.reset();
      }
    }catch(err){
      toast(toastEl, "Terjadi masalah jaringan.", "err");
    }finally{
      setBusy(form, false);
    }
  });
}

bindForm(
  "form-forgot",
  "toast-forgot",
  () => {
    const email = getValue("fpEmail");
    const method = document.getElementById("fpMethod")?.value || "whatsapp_otp";
    if(!email){
      toast(document.getElementById("toast-forgot"), "Email wajib diisi.", "err");
      return null;
    }
    return { email, method, theme: currentTheme() };
  },
  "/api/auth/forgot"
);

bindSignupMultipart();

// Default view: employee login
go(0);

/* =========================
   RANDOM DECOR CIRCLES (each load)
========================= */
function randomizeCircles(){
  const wrap = document.querySelector(".decor-circles");
  if(!wrap) return;
  const w = wrap.clientWidth;
  const h = wrap.clientHeight;
  if(!w || !h) return;

  const el = wrap.querySelector(".circle");
  if(!el) return;
  const size = el.offsetWidth || 0;
  const minX = -0.2 * w;
  const maxX = w - size * 0.3;
  const minY = -0.2 * h;
  const maxY = h - size * 0.3;
  const x = Math.round(minX + Math.random() * (maxX - minX));
  const y = Math.round(minY + Math.random() * (maxY - minY));
  requestAnimationFrame(() => {
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
    el.style.right = "auto";
    el.style.bottom = "auto";
  });
}

window.addEventListener("load", () => {
  randomizeCircles();
  animateCircle();
});

function animateCircle(){
  const el = document.querySelector(".decor-circles .circle");
  if(!el) return;
  el.classList.remove("animate");
  void el.offsetWidth;
  el.classList.add("animate");
}
