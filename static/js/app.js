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
  moveAuthCircles();
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
const themeToggle = document.querySelector("[data-theme-toggle]");
const THEME_DEFAULT_OPTIONS = ["dark", "light"];
const THEME_EXTRA_OPTIONS = ["sage_calm", "silver_line", "noir_warm"];
let THEME_OPTIONS = Array.isArray(window.__GMI_ENABLED_THEMES)
  ? window.__GMI_ENABLED_THEMES
  : ["dark", "light", "sage_calm", "silver_line", "noir_warm"];
const themeInputs = [
  document.getElementById("themeEmp"),
  document.getElementById("themeAdmin"),
  document.getElementById("themeSignup"),
  document.getElementById("themeForgot"),
];

function normalizeTheme(theme){
  return THEME_OPTIONS.includes(theme) ? theme : (THEME_OPTIONS.includes("dark") ? "dark" : THEME_OPTIONS[0] || "dark");
}

function setTheme(theme){
  const normalized = normalizeTheme(theme);
  document.documentElement.setAttribute("data-theme", normalized);
  localStorage.setItem("gmi_theme", normalized);
  localStorage.setItem("theme", normalized);
  themeBtns.forEach(b => b.classList.toggle("active", b.dataset.theme === normalized));
  if (themeToggle){
    themeToggle.classList.toggle("active", normalized === "light");
    themeToggle.setAttribute("data-current-theme", normalized);
    themeToggle.setAttribute("title", `Theme: ${normalized}`);
  }
  themeInputs.forEach(inp => { if (inp) inp.value = normalized; });
}

themeBtns.forEach(btn => {
  btn.addEventListener("click", () => setTheme(btn.dataset.theme));
});
if (themeToggle){
  themeToggle.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    setTheme(next);
  });
}

const initialTheme = normalizeTheme(window.__GMI_INITIAL_THEME || document.documentElement.getAttribute("data-theme") || "dark");
const storedTheme = normalizeTheme(localStorage.getItem("theme") || localStorage.getItem("gmi_theme") || initialTheme);
const savedTheme = THEME_EXTRA_OPTIONS.includes(storedTheme) && !THEME_EXTRA_OPTIONS.includes(initialTheme)
  ? initialTheme
  : storedTheme;
setTheme(savedTheme);

function currentTheme(){
  return normalizeTheme(document.documentElement.getAttribute("data-theme") || "dark");
}

function csrfJsonHeaders(){
  const headers = {"Content-Type": "application/json"};
  if (window.__GMI_CSRF_TOKEN){
    headers["X-CSRF-Token"] = window.__GMI_CSRF_TOKEN;
  }
  return headers;
}

function csrfHeaders(){
  if (!window.__GMI_CSRF_TOKEN) return {};
  return {"X-CSRF-Token": window.__GMI_CSRF_TOKEN};
}

function apiUrlCandidates(path){
  const normalized = path.startsWith("/") ? path : `/${path}`;
  const urls = [normalized];
  if (window.location.protocol === "http:" || window.location.protocol === "https:" || window.location.protocol === "file:"){
    urls.push(`http://127.0.0.1:5000${normalized}`);
    urls.push(`http://localhost:5000${normalized}`);
  }
  return Array.from(new Set(urls));
}

async function fetchApi(path, options = {}){
  let lastError = null;
  for (const url of apiUrlCandidates(path)){
    try {
      const requestOptions = {...options};
      if (url.startsWith("http://") || url.startsWith("https://")){
        requestOptions.credentials = "include";
      }
      return await fetch(url, requestOptions);
    } catch (err){
      lastError = err;
    }
  }
  throw lastError || new Error("Request gagal.");
}

/* =========================
   CLOCK (HH:MM, blink ':', no seconds)
========================= */
const hhEl = document.getElementById("hh");
const mmEl = document.getElementById("mm");
const dateText = document.getElementById("dateText");

function pad2(n){ return String(n).padStart(2,"0"); }

function tick(){
  if (document.hidden) return;
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
   HERO TOGGLES
========================= */
const toggleLogo = document.getElementById("toggleLogo");
const toggleLabel = document.getElementById("toggleLabel");
const toggleClock = document.getElementById("toggleClock");
const toggleNotice = document.getElementById("toggleNotice");
const toggleInvite = document.getElementById("toggleInvite");
const toggleHeroCircles = document.getElementById("toggleHeroCircles");
const toggleFormCircles = document.getElementById("toggleFormCircles");
const toggleLockCircles = document.getElementById("toggleLockCircles");
const primaryKeySelect = document.getElementById("primaryKeySelect");
const toggleModeGpsSelfie = document.getElementById("toggleModeGpsSelfie");
const toggleModeGps = document.getElementById("toggleModeGps");
const toggleModeQr = document.getElementById("toggleModeQr");
const togglePagePatroli = document.getElementById("togglePagePatroli");
const displaySettingsSave = document.getElementById("displaySettingsSave");
const displaySettingsStatus = document.getElementById("displaySettingsStatus");

const heroLogo = document.getElementById("heroLogo");
const heroLabel = document.getElementById("heroLabel");
const heroClock = document.getElementById("heroClock");
const marqueeToasts = Array.from(document.querySelectorAll(".toast[data-marquee]"));
  const inviteCodeWrap = document.getElementById("inviteCodeWrap");
  const inviteCodeInput = document.getElementById("inviteCode");
const labelInputWrap = document.getElementById("labelInputWrap");
const labelInput = document.getElementById("companyLabelInput");
const brandCircles = document.querySelector(".brand-circles");
const formCircles = document.querySelector(".card .decor-circles");
let circlesLocked = false;
const attendanceModeStorage = {
  gps_selfie: "gmi_att_mode_gps_selfie",
  gps: "gmi_att_mode_gps",
  qr: "gmi_att_mode_qr",
};
const displaySettingsStorage = "gmi_display_settings";

const defaultLabel = heroLabel ? heroLabel.textContent.trim() : "";

function setHidden(el, hidden){
  if(!el) return;
  el.classList.toggle("is-hidden", hidden);
}

function syncHero(){
  if(toggleLogo) setHidden(heroLogo, !toggleLogo.checked);
  if(toggleLabel){
    setHidden(heroLabel, !toggleLabel.checked);
    setHidden(labelInputWrap, !toggleLabel.checked);
  }
  if(toggleClock) setHidden(heroClock, !toggleClock.checked);
  if(toggleNotice){
    marqueeToasts.forEach(t => t.classList.toggle("marquee-hidden", !toggleNotice.checked));
  }
    if(toggleInvite){
      const inviteEnabled = toggleInvite.checked;
      setHidden(inviteCodeWrap, !inviteEnabled);
      if (inviteCodeInput) {
        if (!inviteEnabled) {
          inviteCodeInput.value = "SUDAHBYADMIN";
        } else if (inviteCodeInput.value === "SUDAHBYADMIN") {
          inviteCodeInput.value = "";
        }
      }
    }
  if (toggleHeroCircles){
    setHidden(brandCircles, !toggleHeroCircles.checked);
  }
  if (toggleFormCircles){
    setHidden(formCircles, !toggleFormCircles.checked);
  }
  if (toggleLockCircles){
    circlesLocked = toggleLockCircles.checked;
    document.querySelectorAll(".brand-circle, .decor-circles .circle").forEach(el => {
      el.classList.toggle("is-locked", circlesLocked);
    });
  }
}

[toggleLogo, toggleLabel, toggleClock, toggleNotice, toggleInvite, toggleHeroCircles, toggleFormCircles, toggleLockCircles].forEach(cb => {
  if(cb) cb.addEventListener("change", syncHero);
});

function setDisplaySettingsStatus(message, state){
  if (!displaySettingsStatus) return;
  displaySettingsStatus.textContent = message || "";
  if (state){
    displaySettingsStatus.dataset.state = state;
  } else {
    delete displaySettingsStatus.dataset.state;
  }
}

function loadDisplaySettings(){
  try {
    const raw = localStorage.getItem(displaySettingsStorage);
    if (!raw) return;
    const settings = JSON.parse(raw);
    if (!settings || typeof settings !== "object") return;
    [
      ["logo", toggleLogo],
      ["label", toggleLabel],
      ["clock", toggleClock],
      ["notice", toggleNotice],
      ["invite", toggleInvite],
      ["heroCircles", toggleHeroCircles],
      ["formCircles", toggleFormCircles],
      ["lockCircles", toggleLockCircles],
    ].forEach(([key, toggle]) => {
      if (toggle && typeof settings[key] === "boolean"){
        toggle.checked = settings[key];
      }
    });
    if (labelInput && typeof settings.companyLabel === "string"){
      labelInput.value = settings.companyLabel;
      if (heroLabel){
        heroLabel.textContent = settings.companyLabel.trim() || defaultLabel || "Label";
      }
    }
  } catch (_err) {
    localStorage.removeItem(displaySettingsStorage);
  }
}

function saveDisplaySettings(){
  const settings = {
    logo: Boolean(toggleLogo?.checked),
    label: Boolean(toggleLabel?.checked),
    clock: Boolean(toggleClock?.checked),
    notice: Boolean(toggleNotice?.checked),
    invite: Boolean(toggleInvite?.checked),
    heroCircles: Boolean(toggleHeroCircles?.checked),
    formCircles: Boolean(toggleFormCircles?.checked),
    lockCircles: Boolean(toggleLockCircles?.checked),
    companyLabel: labelInput?.value || "",
  };
  localStorage.setItem(displaySettingsStorage, JSON.stringify(settings));
  if (primaryKeySelect){
    localStorage.setItem("gmi_primary_key", primaryKeySelect.value);
    applyPrimaryKeyMode(primaryKeySelect.value);
  }
  handleAttendanceModeChange(null);
  if (togglePagePatroli){
    const enabled = togglePagePatroli.checked;
    localStorage.setItem("gmi_page_patroli_enabled", enabled ? "1" : "0");
    window.dispatchEvent(new CustomEvent("gmi_patroli_toggle_changed", { detail: { enabled } }));
  }
  syncHero();
  setDisplaySettingsStatus("Pengaturan tampilan diterapkan.", "success");
}

loadDisplaySettings();

function loadAttendanceModeToggle(toggle, key){
  if (!toggle) return true;
  const stored = localStorage.getItem(key);
  const enabled = stored === null ? true : stored === "1";
  toggle.checked = enabled;
  return enabled;
}

function saveAttendanceModeToggle(toggle, key){
  if (!toggle) return true;
  const enabled = toggle.checked;
  localStorage.setItem(key, enabled ? "1" : "0");
  return enabled;
}

function syncAttendanceModeToggles(){
  const enabledSelfie = loadAttendanceModeToggle(toggleModeGpsSelfie, attendanceModeStorage.gps_selfie);
  const enabledGps = loadAttendanceModeToggle(toggleModeGps, attendanceModeStorage.gps);
  const enabledQr = loadAttendanceModeToggle(toggleModeQr, attendanceModeStorage.qr);
  if (enabledSelfie && enabledGps && toggleModeGpsSelfie && toggleModeGps){
    toggleModeGpsSelfie.checked = false;
    localStorage.setItem(attendanceModeStorage.gps_selfie, "0");
  }
  if (!enabledSelfie && !enabledGps && !enabledQr && toggleModeGpsSelfie){
    toggleModeGpsSelfie.checked = true;
    localStorage.setItem(attendanceModeStorage.gps_selfie, "1");
  }
}

function enforceGpsExclusive(source){
  if (!toggleModeGpsSelfie || !toggleModeGps) return;
  if (source === toggleModeGpsSelfie && toggleModeGpsSelfie.checked) {
    toggleModeGps.checked = false;
  } else if (source === toggleModeGps && toggleModeGps.checked) {
    toggleModeGpsSelfie.checked = false;
  }
  if (!toggleModeGpsSelfie.checked && !toggleModeGps.checked) {
    if (source === toggleModeGpsSelfie) {
      toggleModeGps.checked = true;
    } else if (source === toggleModeGps) {
      toggleModeGpsSelfie.checked = true;
    } else {
      toggleModeGpsSelfie.checked = true;
    }
  }
}

function handleAttendanceModeChange(source){
  enforceGpsExclusive(source);
  const enabledSelfie = saveAttendanceModeToggle(toggleModeGpsSelfie, attendanceModeStorage.gps_selfie);
  const enabledGps = saveAttendanceModeToggle(toggleModeGps, attendanceModeStorage.gps);
  const enabledQr = saveAttendanceModeToggle(toggleModeQr, attendanceModeStorage.qr);
  if (!enabledSelfie && !enabledGps && !enabledQr && toggleModeGpsSelfie){
    toggleModeGpsSelfie.checked = true;
    localStorage.setItem(attendanceModeStorage.gps_selfie, "1");
  }
}

[toggleModeGpsSelfie, toggleModeGps, toggleModeQr].forEach(cb => {
  if (cb) cb.addEventListener("change", () => handleAttendanceModeChange(cb));
});

syncAttendanceModeToggles();

// Handle togglePagePatroli
if (togglePagePatroli) {
  const patroli_key = "gmi_page_patroli_enabled";
  const stored = localStorage.getItem(patroli_key);
  const isEnabled = stored === null ? true : stored === "1";
  togglePagePatroli.checked = isEnabled;
  
  togglePagePatroli.addEventListener("change", () => {
    const enabled = togglePagePatroli.checked;
    localStorage.setItem(patroli_key, enabled ? "1" : "0");
    // Broadcast change ke halaman employee jika terbuka
    window.dispatchEvent(new CustomEvent("gmi_patroli_toggle_changed", { detail: { enabled } }));
  });
}

if(labelInput && heroLabel){
  labelInput.addEventListener("input", () => {
    const next = labelInput.value.trim();
    heroLabel.textContent = next || defaultLabel || "Label";
  });
}

syncHero();

const heroTrack = document.getElementById("heroTrack");
const heroTabs = Array.from(document.querySelectorAll("[data-hero-go]"));
const heroPanes = heroTrack ? Array.from(heroTrack.children) : [];
const heroPaneCount = heroPanes.length;
if (heroTrack && heroPaneCount){
  heroTrack.style.width = `${heroPaneCount * 100}%`;
  heroPanes.forEach(pane => {
    const basis = `${100 / heroPaneCount}%`;
    pane.style.width = basis;
    pane.style.flex = `0 0 ${basis}`;
  });
}
const heroGalleryMainImage = document.getElementById("heroGalleryMainImage");
const heroGalleryData = document.getElementById("heroGalleryData");
const heroGalleryFileInput = document.getElementById("heroGalleryFileInput");
const heroGalleryCameraInput = document.getElementById("heroGalleryCameraInput");
const heroGalleryFileBtn = document.getElementById("heroGalleryFileBtn");
const heroGalleryCameraBtn = document.getElementById("heroGalleryCameraBtn");
const heroGalleryUploadStatus = document.getElementById("heroGalleryUploadStatus");
const HERO_GALLERY_TAB_INDEX = Math.max(0, heroPanes.findIndex(pane => pane.querySelector("#heroGalleryMainImage")));
const HERO_GALLERY_AUTO_SLIDE_MS = 5000;
let heroGalleryImages = [];
let heroIndex = 0;
let heroGalleryIndex = 0;
let heroGalleryIntervalId = null;
const ownerAddonPassword = document.getElementById("ownerAddonPassword");
const ownerAddonUnlock = document.getElementById("ownerAddonUnlock");
const ownerAddonSave = document.getElementById("ownerAddonSave");
const ownerAddonStatus = document.getElementById("ownerAddonStatus");
const ownerAddonTogglesStatus = document.getElementById("ownerAddonTogglesStatus");
const ownerAddonToggles = Array.from(document.querySelectorAll("[data-owner-addon]"));
const ownerExtraThemesEnabled = document.getElementById("ownerExtraThemesEnabled");
const ownerAddonOpen = document.getElementById("ownerAddonOpen");
const ownerAddonModal = document.getElementById("ownerAddonModal");
const ownerAddonTogglesModal = document.getElementById("ownerAddonTogglesModal");
const ownerAddonCloseButtons = Array.from(document.querySelectorAll("[data-owner-addon-close]"));
const ownerAddonTogglesCloseButtons = Array.from(document.querySelectorAll("[data-owner-addon-toggles-close]"));

if (heroGalleryData){
  try {
    const parsed = JSON.parse(heroGalleryData.textContent || "[]");
    if (Array.isArray(parsed)){
      heroGalleryImages = parsed.filter(src => typeof src === "string" && src.trim() !== "");
    }
  } catch (_err) {
    heroGalleryImages = [];
  }
}

if (!heroGalleryImages.length && heroGalleryMainImage?.getAttribute("src")){
  heroGalleryImages = [heroGalleryMainImage.getAttribute("src")];
}

function setOwnerAddonStatus(message, state){
  if (!ownerAddonStatus) return;
  ownerAddonStatus.textContent = message || "";
  if (state){
    ownerAddonStatus.dataset.state = state;
  } else {
    delete ownerAddonStatus.dataset.state;
  }
}

function setOwnerAddonTogglesStatus(message, state){
  if (!ownerAddonTogglesStatus) return;
  ownerAddonTogglesStatus.textContent = message || "";
  if (state){
    ownerAddonTogglesStatus.dataset.state = state;
  } else {
    delete ownerAddonTogglesStatus.dataset.state;
  }
}

function ownerAddonErrorMessage(response, payload, fallback){
  const message = payload?.message || fallback;
  if ((response.status === 401 || response.status === 403) && message === "Unauthorized."){
    return "Login HR superadmin diperlukan untuk membuka add-on.";
  }
  return message;
}

function setOwnerAddonModalOpen(open){
  if (!ownerAddonModal) return;
  ownerAddonModal.classList.toggle("show", open);
  ownerAddonModal.setAttribute("aria-hidden", open ? "false" : "true");
  if (!open && ownerAddonTogglesModal){
    ownerAddonTogglesModal.classList.remove("show");
    ownerAddonTogglesModal.setAttribute("aria-hidden", "true");
  }
  if (open){
    setOwnerAddonStatus("", null);
    setOwnerAddonTogglesStatus("", null);
    window.setTimeout(() => ownerAddonPassword?.focus(), 50);
  }
}

function setOwnerAddonTogglesModalOpen(open){
  if (!ownerAddonTogglesModal) return;
  ownerAddonTogglesModal.classList.toggle("show", open);
  ownerAddonTogglesModal.setAttribute("aria-hidden", open ? "false" : "true");
  if (open){
    setDisplaySettingsStatus("", null);
  }
}

function setOwnerAddonUnlocked(unlocked){
  ownerAddonToggles.forEach(toggle => {
    toggle.disabled = !unlocked;
  });
  if (ownerExtraThemesEnabled) ownerExtraThemesEnabled.disabled = !unlocked;
  if (ownerAddonSave){
    ownerAddonSave.disabled = !unlocked;
  }
}

function setOwnerAddonValues(addons){
  const active = new Set(Array.isArray(addons) ? addons : []);
  ownerAddonToggles.forEach(toggle => {
    toggle.checked = active.has(toggle.dataset.ownerAddon);
  });
}

function setOwnerThemeValues(enabled){
  if (ownerExtraThemesEnabled) ownerExtraThemesEnabled.checked = Boolean(enabled);
}

function selectedOwnerAddons(){
  return ownerAddonToggles
    .filter(toggle => toggle.checked)
    .map(toggle => toggle.dataset.ownerAddon)
    .filter(Boolean);
}

function ownerExtraThemesSelected(){
  return Boolean(ownerExtraThemesEnabled?.checked);
}

async function loadOwnerAddons(){
  if (!ownerAddonToggles.length) return;
  setOwnerAddonTogglesStatus("Memuat add-on...", "loading");
  try {
    const response = await fetchApi("/api/owner/addons");
    const payload = await response.json().catch(() => ({}));
    if (response.ok && payload.ok){
      setOwnerAddonValues(payload.data?.addons || []);
      setOwnerThemeValues(payload.data?.extra_themes_enabled);
      setOwnerAddonUnlocked(Boolean(payload.data?.unlocked));
      setOwnerAddonTogglesStatus("", null);
    } else if (response.status === 401 || response.status === 403){
      setOwnerAddonUnlocked(false);
      setOwnerAddonTogglesStatus("Akses owner belum aktif.", "error");
    }
  } catch (_err) {
    setOwnerAddonTogglesStatus("Add-on belum dapat dimuat.", "error");
  }
}

async function unlockOwnerAddons(){
  if (!ownerAddonPassword) return;
  const password = ownerAddonPassword.value.trim();
  if (!password){
    setOwnerAddonStatus("Password owner wajib diisi.", "error");
    return;
  }
  setOwnerAddonStatus("Membuka akses...", "loading");
  try {
    const response = await fetchApi("/api/owner/addons/verify", {
      method: "POST",
      headers: csrfJsonHeaders(),
      body: JSON.stringify({password}),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok){
      throw new Error(ownerAddonErrorMessage(response, payload, "Akses owner gagal."));
    }
    setOwnerAddonValues(payload.data?.addons || []);
    setOwnerThemeValues(payload.data?.extra_themes_enabled);
    setOwnerAddonUnlocked(true);
    ownerAddonPassword.value = "";
    setOwnerAddonStatus(payload.message || "Akses owner aktif.", "success");
    setOwnerAddonModalOpen(false);
    setOwnerAddonTogglesModalOpen(true);
    await loadOwnerAddons();
  } catch (err){
    const message = err instanceof Error ? err.message : "Akses owner gagal.";
    setOwnerAddonUnlocked(false);
    setOwnerAddonStatus(message, "error");
  }
}

async function saveOwnerAddons(){
  setOwnerAddonTogglesStatus("Menyimpan add-on...", "loading");
  try {
    const response = await fetchApi("/api/owner/addons", {
      method: "POST",
      headers: csrfJsonHeaders(),
      body: JSON.stringify({
        addons: selectedOwnerAddons(),
        extra_themes_enabled: ownerExtraThemesSelected(),
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok){
      throw new Error(ownerAddonErrorMessage(response, payload, "Add-on gagal disimpan."));
    }
    setOwnerAddonValues(payload.data?.addons || []);
    const enabledThemes = payload.data?.enabled_extra_themes || [];
    setOwnerThemeValues(Boolean(payload.data?.extra_themes_enabled));
    window.__GMI_ENABLED_EXTRA_THEMES = enabledThemes;
    window.__GMI_ENABLED_THEMES = [...THEME_DEFAULT_OPTIONS, ...enabledThemes];
    THEME_OPTIONS = window.__GMI_ENABLED_THEMES;
    if (!window.__GMI_ENABLED_THEMES.includes(currentTheme())){
      setTheme("dark");
    }
    setOwnerAddonTogglesStatus(payload.message || "Pengaturan owner tersimpan.", "success");
  } catch (err){
    const message = err instanceof Error ? err.message : "Add-on gagal disimpan.";
    setOwnerAddonTogglesStatus(message, "error");
  }
}

if (ownerAddonUnlock){
  ownerAddonUnlock.addEventListener("click", unlockOwnerAddons);
}
if (ownerAddonPassword){
  ownerAddonPassword.addEventListener("keydown", event => {
    if (event.key === "Enter"){
      event.preventDefault();
      unlockOwnerAddons();
    }
  });
}
if (ownerAddonSave){
  ownerAddonSave.addEventListener("click", saveOwnerAddons);
}
if (ownerAddonOpen){
  ownerAddonOpen.addEventListener("click", () => setOwnerAddonModalOpen(true));
}
ownerAddonCloseButtons.forEach(button => {
  button.addEventListener("click", () => setOwnerAddonModalOpen(false));
});
ownerAddonTogglesCloseButtons.forEach(button => {
  button.addEventListener("click", () => setOwnerAddonTogglesModalOpen(false));
});
if (ownerAddonModal){
  ownerAddonModal.addEventListener("click", event => {
    if (event.target === ownerAddonModal){
      setOwnerAddonModalOpen(false);
    }
  });
}
if (ownerAddonTogglesModal){
  ownerAddonTogglesModal.addEventListener("click", event => {
    if (event.target === ownerAddonTogglesModal){
      setOwnerAddonTogglesModalOpen(false);
    }
  });
}
document.addEventListener("keydown", event => {
  if (event.key === "Escape" && ownerAddonModal?.classList.contains("show")){
    setOwnerAddonModalOpen(false);
  }
  if (event.key === "Escape" && ownerAddonTogglesModal?.classList.contains("show")){
    setOwnerAddonTogglesModalOpen(false);
  }
});

if (displaySettingsSave){
  displaySettingsSave.addEventListener("click", saveDisplaySettings);
}

function renderHeroGalleryImage(){
  if (!heroGalleryMainImage) return;
  if (!heroGalleryImages.length){
    heroGalleryMainImage.removeAttribute("src");
    heroGalleryMainImage.classList.add("is-hidden");
    return;
  }
  heroGalleryMainImage.classList.remove("is-hidden");
  heroGalleryMainImage.src = heroGalleryImages[heroGalleryIndex];
}

function stopHeroGalleryAutoSlide(){
  if (heroGalleryIntervalId !== null){
    window.clearInterval(heroGalleryIntervalId);
    heroGalleryIntervalId = null;
  }
}

function startHeroGalleryAutoSlide(){
  stopHeroGalleryAutoSlide();
  if (!heroGalleryMainImage || heroGalleryImages.length <= 1 || heroIndex !== HERO_GALLERY_TAB_INDEX){
    return;
  }
  heroGalleryIntervalId = window.setInterval(() => {
    heroGalleryIndex = (heroGalleryIndex + 1) % heroGalleryImages.length;
    renderHeroGalleryImage();
  }, HERO_GALLERY_AUTO_SLIDE_MS);
}

function setHeroGalleryUploadStatus(message, state){
  if (!heroGalleryUploadStatus) return;
  heroGalleryUploadStatus.textContent = message || "";
  if (state){
    heroGalleryUploadStatus.dataset.state = state;
  } else {
    delete heroGalleryUploadStatus.dataset.state;
  }
}

function addHeroGalleryImage(nextUrl){
  if (typeof nextUrl !== "string" || !nextUrl.trim()) return;
  const cleanUrl = nextUrl.trim();
  if (!heroGalleryImages.includes(cleanUrl)){
    heroGalleryImages.push(cleanUrl);
  }
  if (heroGalleryImages.length === 1){
    heroGalleryIndex = 0;
  }
  renderHeroGalleryImage();
  if (heroIndex === HERO_GALLERY_TAB_INDEX){
    startHeroGalleryAutoSlide();
  }
}

async function uploadHeroGalleryFile(file){
  if (!file) return;
  const formData = new FormData();
  formData.append("image", file);
  setHeroGalleryUploadStatus("Mengunggah gambar...", "loading");
  try {
    const response = await fetchApi("/api/hero-gallery/upload", {
      method: "POST",
      headers: csrfHeaders(),
      body: formData,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok){
      throw new Error(payload.message || "Upload gambar gagal.");
    }
    addHeroGalleryImage(payload.url || "");
    setHeroGalleryUploadStatus("Upload berhasil.", "success");
  } catch (err){
    const message = err instanceof Error ? err.message : "Upload gambar gagal.";
    setHeroGalleryUploadStatus(message, "error");
  }
}

function bindHeroGalleryUploadButton(button, input){
  if (!button || !input) return;
  button.addEventListener("click", () => input.click());
  input.addEventListener("change", async () => {
    const file = input.files && input.files[0];
    input.value = "";
    if (!file) return;
    await uploadHeroGalleryFile(file);
  });
}

function heroGo(i){
  if (!heroTrack || !heroPaneCount) return;
  heroIndex = Math.max(0, Math.min(heroPaneCount - 1, i));
  const step = 100 / heroPaneCount;
  heroTrack.style.transform = `translateX(-${heroIndex * step}%)`;
  heroTabs.forEach(btn => {
    btn.classList.toggle("active", parseInt(btn.dataset.heroGo, 10) === heroIndex);
  });
  if (heroIndex === HERO_GALLERY_TAB_INDEX){
    startHeroGalleryAutoSlide();
  } else {
    stopHeroGalleryAutoSlide();
  }
}

heroTabs.forEach(btn => {
  btn.addEventListener("click", () => {
    heroGo(parseInt(btn.dataset.heroGo, 10));
  });
});

renderHeroGalleryImage();
bindHeroGalleryUploadButton(heroGalleryFileBtn, heroGalleryFileInput);
bindHeroGalleryUploadButton(heroGalleryCameraBtn, heroGalleryCameraInput);
document.addEventListener("visibilitychange", () => {
  if (document.hidden){
    stopHeroGalleryAutoSlide();
    return;
  }
  if (heroIndex === HERO_GALLERY_TAB_INDEX){
    startHeroGalleryAutoSlide();
  }
});

heroGo(0);

/* =========================
   LOGIN METHOD TOGGLE
========================= */
function initLoginToggles(){
  const scopes = Array.from(document.querySelectorAll("[data-login-scope]"));
  scopes.forEach(scope => {
    const methodInput = scope.querySelector("[data-login-method-input]");
    const resetMethodInput = scope.querySelector("[data-reset-method-input]");
    const buttons = Array.from(scope.querySelectorAll("[data-login-method-btn]"));
    const fields = Array.from(scope.querySelectorAll("[data-login-field]"));
    if (!methodInput || !buttons.length || !fields.length) return;

    function syncResetMethod(nextMethod){
      if (!resetMethodInput) return;
      resetMethodInput.value = nextMethod === "phone" ? "whatsapp_otp" : "email_link";
    }

    function setMethod(method){
      const nextMethod = method === "phone" ? "phone" : "email";
      methodInput.value = nextMethod;
      syncResetMethod(nextMethod);
      buttons.forEach(btn => {
        const active = btn.dataset.loginMethodBtn === nextMethod;
        btn.classList.toggle("active", active);
        btn.setAttribute("aria-pressed", active ? "true" : "false");
      });
      fields.forEach(field => {
        const show = field.dataset.loginField === nextMethod;
        field.classList.toggle("is-hidden", !show);
        field.querySelectorAll("input").forEach(input => {
          input.disabled = !show;
          input.required = show;
        });
      });
    }

    buttons.forEach(btn => {
      btn.addEventListener("click", () => setMethod(btn.dataset.loginMethodBtn));
    });

    setMethod(methodInput.value || "email");
  });
}

function getLoginMethod(formId){
  const form = document.getElementById(formId);
  return form?.querySelector("[data-login-method-input]")?.value || "email";
}

initLoginToggles();

function applyPrimaryKeyMode(mode){
  const scopes = Array.from(document.querySelectorAll("[data-login-scope]"));
  const nextMode = mode === "email" || mode === "phone" ? mode : "both";
  scopes.forEach(scope => {
    const methodInput = scope.querySelector("[data-login-method-input]");
    const resetMethodInput = scope.querySelector("[data-reset-method-input]");
    const switchWrap = scope.querySelector(".login-switch");
    const buttons = Array.from(scope.querySelectorAll("[data-login-method-btn]"));
    const fields = Array.from(scope.querySelectorAll("[data-login-field]"));
    if (!methodInput || !fields.length) return;

    if (nextMode === "both"){
      if (switchWrap) switchWrap.classList.remove("is-hidden");
      const current = methodInput.value || "email";
      methodInput.value = current === "phone" ? "phone" : "email";
    } else {
      if (switchWrap) switchWrap.classList.add("is-hidden");
      methodInput.value = nextMode;
    }

    if (resetMethodInput){
      resetMethodInput.value = methodInput.value === "phone" ? "whatsapp_otp" : "email_link";
    }

    const showMethod = methodInput.value;
    buttons.forEach(btn => {
      const active = btn.dataset.loginMethodBtn === showMethod;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
    fields.forEach(field => {
      const show = field.dataset.loginField === showMethod;
      field.classList.toggle("is-hidden", !show);
      field.querySelectorAll("input").forEach(input => {
        input.disabled = !show;
        input.required = show;
      });
    });
  });
}

if (primaryKeySelect){
  const primaryKeyBoot = window.__GMI_BOOT_ID || "";
  const primaryKeyStorage = "gmi_primary_key";
  const primaryKeyBootStorage = "gmi_primary_key_boot";
  const defaultPrimaryKey = primaryKeySelect.value;
  const savedBoot = localStorage.getItem(primaryKeyBootStorage);

  if (primaryKeyBoot && savedBoot !== primaryKeyBoot){
    localStorage.removeItem(primaryKeyStorage);
    localStorage.setItem(primaryKeyBootStorage, primaryKeyBoot);
    primaryKeySelect.value = defaultPrimaryKey;
  } else if (primaryKeyBoot && !savedBoot){
    localStorage.setItem(primaryKeyBootStorage, primaryKeyBoot);
  }

  const savedPrimaryKey = localStorage.getItem(primaryKeyStorage);
  if (savedPrimaryKey){
    primaryKeySelect.value = savedPrimaryKey;
  }

  primaryKeySelect.addEventListener("change", () => {
    localStorage.setItem(primaryKeyStorage, primaryKeySelect.value);
    applyPrimaryKeyMode(primaryKeySelect.value);
  });
  applyPrimaryKeyMode(primaryKeySelect.value);
}

/* =========================
   SELFIE INDICATOR
========================= */
const selfieInput = document.getElementById("suSelfie");
if (selfieInput){
  const selfieWrap = selfieInput.closest(".selfie-pick");
  const updateSelfieIndicator = () => {
    const hasFile = Boolean(selfieInput.files && selfieInput.files.length);
    if (selfieWrap) selfieWrap.classList.toggle("has-file", hasFile);
  };
  selfieInput.addEventListener("change", updateSelfieIndicator);
  updateSelfieIndicator();
}

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
    const method = getLoginMethod("form-emp");
    const identifier = method === "phone" ? getValue("empPhone") : getValue("empEmail");
    const pw = getValue("empPass");
    if(!identifier || !pw){
      const msg = method === "phone"
        ? "Isi nomor telp dan password dulu."
        : "Isi email dan password dulu.";
      toast(document.getElementById("toast-emp"), msg, "err");
      return null;
    }
    return { identifier, login_type: method, password: pw, theme: currentTheme() };
  },
  "/api/auth/login"
);

function bindSignupMultipart(){
  const form = document.getElementById("form-signup");
  const toastEl = document.getElementById("toast-signup");
  if (!form || !toastEl) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const method = getLoginMethod("form-signup");
    const inv = getValue("inviteCode");
    const identifier = method === "phone" ? getValue("suPhone") : getValue("suEmail");
    const p1 = getValue("suPass");
    const p2 = getValue("suPass2");
    const selfieInput = document.getElementById("suSelfie");
    const selfieFile = selfieInput?.files?.[0];

    if(!inv){
      toast(toastEl, "Kode undangan wajib.", "err");
      return;
    }
    if(!identifier){
      const msg = method === "phone"
        ? "No telp wajib diisi."
        : "Email wajib diisi.";
      toast(toastEl, msg, "err");
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
    formData.append("login_type", method);
    formData.append("identifier", identifier);
    if (method === "email") {
      formData.append("email", identifier);
    } else {
      formData.append("phone", identifier);
    }
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
        // Otomatis kembali ke halaman login setelah 2 detik
        setTimeout(() => {
          go(0); // Kembali ke form login (index 0)
        }, 2000);
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
    const loginType = getLoginMethod("form-forgot");
    const identifier = loginType === "phone" ? getValue("fpPhone") : getValue("fpEmail");
    const resetMethod = document.getElementById("fpMethod")?.value || "whatsapp_otp";
    if(!identifier){
      const msg = loginType === "phone"
        ? "No telp wajib diisi."
        : "Email wajib diisi.";
      toast(document.getElementById("toast-forgot"), msg, "err");
      return null;
    }
    return { identifier, login_type: loginType, method: resetMethod, theme: currentTheme() };
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
  if (circlesLocked) return;
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
  moveAuthCircles();
});

function animateCircle(){
  const el = document.querySelector(".decor-circles .circle");
  if(!el) return;
  el.classList.remove("animate");
  void el.offsetWidth;
  el.classList.add("animate");
}

function moveAuthCircles(){
  if (circlesLocked) return;
  const wrap = document.querySelector(".brand-circles");
  if(!wrap) return;
  const w = wrap.clientWidth;
  const h = wrap.clientHeight;
  if(!w || !h) return;

  wrap.querySelectorAll(".brand-circle").forEach(el => {
    const size = el.offsetWidth || 0;
    const minX = -0.2 * w;
    const maxX = w - size * 0.2;
    const minY = -0.2 * h;
    const maxY = h - size * 0.2;
    const x = Math.round(minX + Math.random() * (maxX - minX));
    const y = Math.round(minY + Math.random() * (maxY - minY));
    el.style.left = `${x}px`;
    el.style.top = `${y}px`;
  });
}
