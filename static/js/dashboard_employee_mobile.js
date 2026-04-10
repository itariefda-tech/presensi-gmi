// Geolocation shim: use Capacitor plugin when available, fallback to browser API.
const Geolocation = (() => {
  const capacitorGeo = window.Capacitor?.Plugins?.Geolocation;
  if (capacitorGeo) return capacitorGeo;
  const hasBrowserGeo = "geolocation" in navigator;
  return {
    async requestPermissions() {
      return { location: hasBrowserGeo ? "granted" : "denied" };
    },
    async checkPermissions() {
      return { location: hasBrowserGeo ? "granted" : "denied" };
    },
    async getCurrentPosition(options) {
      return new Promise((resolve, reject) => {
        if (!hasBrowserGeo) {
          reject(new Error("Geolocation not supported"));
          return;
        }
        navigator.geolocation.getCurrentPosition(resolve, reject, options);
      });
    },
  };
})();

const themeToggle = document.querySelector("[data-theme-toggle]");
const clockHH = document.getElementById("clockHH");
const clockMM = document.getElementById("clockMM");
const clockColon = document.getElementById("clockColon");
const bodyEl = document.body;

const swipeTrack = document.getElementById("swipeTrack");
const swipeViewport = document.querySelector(".swipe-viewport");
const navButtons = Array.from(document.querySelectorAll(".nav-btn"));
const floatingNav = document.getElementById("floatingNav");
const navHandle = document.getElementById("navHandle");

const attMethod = document.getElementById("attMethod");
const modeChips = Array.from(document.querySelectorAll("#attendanceModeChips .chip"));
const btnLocation = document.getElementById("btnLocation");
const latEl = document.getElementById("lat");
const lonEl = document.getElementById("lon");
const presenceStatusTitle = document.getElementById("presenceStatusTitle");
const selfieFile = document.getElementById("selfieFile");
const selfiePreview = document.getElementById("selfiePreview");
const selfiePick = document.querySelector(".selfie-pick");
const selfieBlock = document.querySelector(".tool-selfie");
const btnScan = document.getElementById("btnScan");
const qrStatus = document.getElementById("qrStatus");
const qrVideo = document.getElementById("qrVideo");
const qrData = document.getElementById("qrData");
const qrBlock = document.querySelector(".tool-qr");
const btnCheckin = document.getElementById("btnCheckin");
const btnCheckout = document.getElementById("btnCheckout");
const checkinStatus = document.getElementById("checkinStatus");
const checkoutStatus = document.getElementById("checkoutStatus");
const attToast = document.getElementById("attToast");
const lastActionTime = document.getElementById("lastActionTime");
const lastActionBadge = document.getElementById("lastActionBadge");
const helpModal = document.getElementById("helpModal");
const btnHelp = document.getElementById("btnHelp");
const btnHelpClose = document.getElementById("btnHelpClose");
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

const leaveType = document.getElementById("leaveType");
const leaveFrom = document.getElementById("leaveFrom");
const leaveTo = document.getElementById("leaveTo");
const leaveReason = document.getElementById("leaveReason");
const leaveAttachment = document.getElementById("leaveAttachment");
const btnLeave = document.getElementById("btnLeave");
const leaveToast = document.getElementById("leaveToast");
const leaveStory = document.getElementById("leaveStory");
const leaveActionButtons = Array.from(document.querySelectorAll(".leave-action-btn"));
const leaveSheet = document.getElementById("leaveSheet");
const leaveTypeLabel = document.getElementById("leaveTypeLabel");
const leavePendingCount = document.getElementById("leavePendingCount");
const btnLeaveRefresh = document.getElementById("btnLeaveRefresh");
const leaveSheetClose = document.getElementById("leaveSheetClose");
const leaveDetailModal = document.getElementById("leaveDetailModal");
const leaveDetailClose = document.getElementById("leaveDetailClose");
const leaveDetailType = document.getElementById("leaveDetailType");
const leaveDetailRange = document.getElementById("leaveDetailRange");
const leaveDetailReason = document.getElementById("leaveDetailReason");
const leaveDetailNote = document.getElementById("leaveDetailNote");
const kpiLocationValue = document.getElementById("kpiLocationStatus");
const kpiLocationCoords = document.getElementById("kpiLocationCoords");
const kpiMasukValue = document.getElementById("kpiMasukValue");
const kpiMasukMeta = document.getElementById("kpiMasukMeta");
const presenceMethodLabel = document.getElementById("presenceMethodLabel");
const netStatusBadge = document.getElementById("netStatusHeader");
const netStatusLabel = netStatusBadge?.querySelector(".network-label");
const netStatusAlert = document.getElementById("netStatusAlert");
const reportFieldEls = {
  present: document.querySelector(".report-item[data-field='present'] strong"),
  late: document.querySelector(".report-item[data-field='late'] strong"),
  izin: document.querySelector(".report-item[data-field='izin'] strong"),
  sakit: document.querySelector(".report-item[data-field='sakit'] strong"),
};
const dailyReportRows = document.getElementById("dailyReportRows");
const patrolRouteLabel = document.getElementById("patrolRouteLabel");
const patrolStatusBadge = document.getElementById("patrolStatusBadge");
const patrolProgressText = document.getElementById("patrolProgressText");
const patrolProgressPercent = document.getElementById("patrolProgressPercent");
const patrolProgressBar = document.getElementById("patrolProgressBar");
const patrolNextCheckpoint = document.getElementById("patrolNextCheckpoint");
const patrolSecurityMode = document.getElementById("patrolSecurityMode");
const patrolCheckpointList = document.getElementById("patrolCheckpointList");
const patrolHistoryList = document.getElementById("patrolHistoryList");
const patrolUpgradeHint = document.getElementById("patrolUpgradeHint");
const patrolToast = document.getElementById("patrolToast");
const btnPatrolStart = document.getElementById("btnPatrolStart");
const btnPatrolRefresh = document.getElementById("btnPatrolRefresh");
const btnPatrolScan = document.getElementById("btnPatrolScan");
const btnPatrolNfc = document.getElementById("btnPatrolNfc");
const btnPatrolSubmit = document.getElementById("btnPatrolSubmit");
const btnPatrolLocation = document.getElementById("btnPatrolLocation");
const patrolModeChips = Array.from(document.querySelectorAll(".patrol-mode-chip"));
const patrolScanPanelQr = document.getElementById("patrolScanPanelQr");
const patrolScanPanelNfc = document.getElementById("patrolScanPanelNfc");
const patrolScanStatus = document.getElementById("patrolScanStatus");
const patrolNfcStatus = document.getElementById("patrolNfcStatus");
const patrolQrVideo = document.getElementById("patrolQrVideo");
const patrolScanData = document.getElementById("patrolScanData");
const patrolGpsStatus = document.getElementById("patrolGpsStatus");
const patrolGpsCoords = document.getElementById("patrolGpsCoords");
const patrolSelfieFile = document.getElementById("patrolSelfieFile");
const patrolSelfiePreview = document.getElementById("patrolSelfiePreview");
const patrolSelfieHint = document.getElementById("patrolSelfieHint");

let qrStream = null;
let qrDetector = null;
let qrActive = false;
let qrLastValue = "";
let swipeIndex = 0;
let toastTimer = null;
let leaveToastTimer = null;
let lastAccuracy = "";
let lastDeviceTime = "";
let locationActive = false;
let hasLocation = false;
let isOnline = navigator.onLine;
let hasCheckedIn = lastActionBadge?.textContent === "IN";
let patrolState = null;
let patrolMode = "qr";
let patrolQrStream = null;
let patrolQrDetector = null;
let patrolQrActive = false;
let patrolQrLastValue = "";
let patrolGpsLat = "";
let patrolGpsLng = "";
let patrolGpsAccuracy = "";
let patrolGpsDeviceTime = "";
let patrolToastTimer = null;
let patrolAutoRefreshTimer = null;
const attendanceModeStorage = {
  gps_selfie: "gmi_att_mode_gps_selfie",
  gps: "gmi_att_mode_gps",
  qr: "gmi_att_mode_qr",
};
const methodLabelMap = {
  gps_selfie: "GPS+SELFIE",
  gps: "GPS",
  qr: "SCAN QR",
};

function pad2(n){
  return String(n).padStart(2, "0");
}

function toIsoDate(value){
  const raw = (value || "").trim();
  if (!raw) return "";
  const match = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (match) {
    return `${match[3]}-${match[2]}-${match[1]}`;
  }
  return raw;
}

function parseIsoDate(value){
  const iso = toIsoDate(value);
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return { iso, date };
}

function appendCsrf(formData){
  if (!formData || !csrfToken) return;
  formData.append("csrf_token", csrfToken);
}

function updatePresenceReadiness(){
  if (!presenceStatusTitle) {
    console.log("[READINESS] presenceStatusTitle not found");
    return;
  }
  
  const isStatusDone = presenceStatusTitle.classList.contains("is-done");
  if (isStatusDone && !hasCheckedIn) {
    console.log("[READINESS] Skipped: Status already is-done (final state)");
    return;
  }
  const shouldRefreshStatusLabel = !isStatusDone;
  
  // Get current selected method
  const currentMethod = attMethod?.value || "gps_selfie";
  console.log("[READINESS] Current method:", currentMethod);
  
  // Determine readiness for check-in vs check-out
  let checkinReady = false;
  let checkoutReady = false;
  
  if (currentMethod === "gps") {
    // GPS only: needs location only, selfie NOT required
    checkinReady = isOnline && locationActive && hasLocation;
    checkoutReady = checkinReady;
  } else if (currentMethod === "gps_selfie") {
    // GPS + Selfie: check-in needs selfie, check-out does not
    const hasSelfie = selfieFile?.files?.length > 0 && selfiePreview?.style?.display !== "none";
    checkinReady = isOnline && locationActive && hasLocation && hasSelfie;
    checkoutReady = isOnline && locationActive && hasLocation;
    console.log("[READINESS] GPS+Selfie check:", {isOnline, locationActive, hasLocation, hasSelfie, checkinReady, checkoutReady});
  } else if (currentMethod === "qr") {
    // QR mode: needs QR data, location not required
    const hasQr = qrData?.value && qrData.value.trim() !== "";
    checkinReady = isOnline && hasQr;
    checkoutReady = checkinReady;
  }
  
  const statusReady = hasCheckedIn ? checkoutReady : checkinReady;
  if (shouldRefreshStatusLabel) {
    console.log("[READINESS] Setting status to:", statusReady ? "Siap Absen" : "Belum siap Absen");
    presenceStatusTitle.textContent = statusReady ? "Siap Absen" : "Belum siap Absen";
    presenceStatusTitle.classList.toggle("is-ready", statusReady);
    presenceStatusTitle.setAttribute("aria-label", statusReady ? "Siap Absen" : "Belum siap Absen");
  }
  if (btnLocation) {
    btnLocation.classList.toggle("is-warning", !hasLocation);
  }
  if (btnCheckin) {
    btnCheckin.disabled = !checkinReady;
    btnCheckin.setAttribute("aria-disabled", checkinReady ? "false" : "true");
  }
  if (btnCheckout) {
    const canCheckout = checkoutReady && hasCheckedIn;
    btnCheckout.disabled = !canCheckout;
    btnCheckout.setAttribute("aria-disabled", canCheckout ? "false" : "true");
  }
}

function setLocationStatus(active){
  locationActive = active;
  updatePresenceReadiness();
  refreshLocationKpi();
}

function getMethodLabel(value){
  if (!value) {
    return methodLabelMap.gps_selfie;
  }
  return methodLabelMap[value] || value.replace(/_/g, " ").toUpperCase();
}

function refreshLocationKpi(){
  if (!kpiLocationValue) return;
  kpiLocationValue.textContent = locationActive ? "Aktif" : "Tidak aktif";
}

function refreshLocationCoords(){
  if (!kpiLocationCoords || !latEl || !lonEl) return;
  const lat = (latEl.value || "").trim();
  const lon = (lonEl.value || "").trim();
  if (lat && lon) {
    kpiLocationCoords.textContent = `${lat}, ${lon}`;
  } else {
    kpiLocationCoords.textContent = "Belum ada koordinat.";
  }
}

function refreshNetworkBadge(){
  if (!netStatusBadge) return;
  const statusText = isOnline ? "Online" : "Offline";
  netStatusBadge.classList.toggle("online", isOnline);
  netStatusBadge.classList.toggle("offline", !isOnline);
  netStatusBadge.setAttribute("aria-label", `${statusText} jaringan`);
  netStatusBadge.dataset.status = statusText.toLowerCase();
  if (netStatusLabel) {
    netStatusLabel.textContent = statusText;
  }
  if (netStatusAlert) {
    if (isOnline) {
      netStatusAlert.textContent = "";
      netStatusAlert.classList.remove("active");
    } else {
      netStatusAlert.textContent = "Segera periksa data/internet (wajib online)";
      netStatusAlert.classList.add("active");
    }
  }
}

function hideSelfiePreview(){
  if (!selfiePreview) return;
  selfiePreview.src = "";
  selfiePreview.style.display = "none";
}

function updateSelfiePickState(ready){
  if (!selfiePick) return;
  selfiePick.classList.toggle("is-ready", ready);
}

function resetSelfieSelection(){
  if (selfieFile) {
    selfieFile.value = "";
  }
  updateSelfiePickState(false);
  hideSelfiePreview();
  // Update presence readiness when selfie is reset
  updatePresenceReadiness();
}

function refreshMasukKpi(){
  if (kpiMasukValue) {
    const timeText = (lastActionTime?.textContent?.trim() || "--:--");
    kpiMasukValue.textContent = timeText;
  }
  if (kpiMasukMeta) {
    const badgeText = (lastActionBadge?.textContent?.trim() || "-");
    const statusText = badgeText === "IN" ? "Masuk tercatat" : badgeText === "OUT" ? "Pulang tercatat" : "Belum absen";
    kpiMasukMeta.textContent = `Status: ${statusText}`;
  }
}

function refreshAbsentKpi(){
  // Kept for legacy hooks; no KPI card to update.
}

async function requestLocationPermission() {
    try {
        const status = await Geolocation.requestPermissions();
        return status.location === 'granted';
    } catch (e) {
        console.error('Geolocation permission request failed.', e);
        return false;
    }
}

async function checkLocationStatus(){
  try {
    const status = await Geolocation.checkPermissions();
    setLocationStatus(status.location === 'granted');
  } catch (e) {
    console.error('Geolocation status check failed.', e);
    setLocationStatus(false);
  }
}

function setTheme(theme){
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("gmi_theme", theme);
  if (themeToggle) {
    themeToggle.classList.toggle("active", theme === "light");
  }
}

function initTheme(){
  const saved = localStorage.getItem("gmi_theme") || "dark";
  setTheme(saved);
}

function currentTheme(){
  return document.documentElement.getAttribute("data-theme") || "dark";
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    setTheme(next);
  });
}

function tickClock(){
  if (document.hidden) return;
  const d = new Date();
  clockHH.textContent = pad2(d.getHours());
  clockMM.textContent = pad2(d.getMinutes());
  clockColon.classList.toggle("is-blink-off");
}

function initProfile(){
  const email = bodyEl.dataset.email || "";
  const key = `gmi_profile_${email.toLowerCase()}`;
  const stored = localStorage.getItem(key);
  const img = document.getElementById("profilePhoto");
  if (!img) return;
  if (img.getAttribute("src")) return;
  if (stored) {
    img.src = stored;
    return;
  }
  const svg = encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
      <rect width="80" height="80" rx="40" fill="#1f2937"/>
      <circle cx="40" cy="30" r="14" fill="#9fb2d0"/>
      <path d="M16 68c6-12 17-18 24-18s18 6 24 18" fill="#9fb2d0"/>
    </svg>`
  );
  img.src = `data:image/svg+xml,${svg}`;
}

function showPresenceToast(msg, type = "ok"){
  showToast(type === "error" ? "error" : "success", msg, { target: attToast });
}

function showLeaveToast(msg, type = "ok"){
  showToast(type === "error" ? "error" : "success", msg, { target: leaveToast });
}

function showToast(type, message, opts = {}){
  const target = opts.target || attToast;
  if (!target) return;
  const tone = type === "error" ? "error" : type === "info" ? "info" : "ok";
  const timeoutMs = typeof opts.timeoutMs === "number" ? opts.timeoutMs : 3200;
  target.textContent = message;
  target.classList.remove("ok", "error", "info", "show");
  target.classList.add(tone, "show");
  if (target === leaveToast) {
    if (leaveToastTimer) window.clearTimeout(leaveToastTimer);
    if (!opts.persist) {
      leaveToastTimer = window.setTimeout(() => {
        target.classList.remove("show");
      }, timeoutMs);
    }
    return;
  }
  if (toastTimer) window.clearTimeout(toastTimer);
  if (!opts.persist) {
    toastTimer = window.setTimeout(() => {
      target.classList.remove("show");
    }, timeoutMs);
  }
}

async function safeFetch(url, options = {}){
  let res = null;
  try {
    res = await fetch(url, options);
  } catch (err) {
    return { ok: false, data: null, message: "Koneksi bermasalah. Coba lagi." };
  }
  let data = null;
  try {
    data = await res.json();
  } catch (err) {
    data = null;
  }
  const ok = res.ok;
  const message = data?.message || (ok ? "Berhasil." : "Permintaan gagal.");
  return { ok, data, message, status: res.status };
}

function updateReportField(field, value){
  const el = reportFieldEls[field];
  if (!el) return;
  const numeric = Number.isFinite(value) ? value : Number(value);
  el.textContent = Number.isFinite(numeric) ? String(Math.max(0, numeric)) : "0";
}

async function loadMonthlySummary(){
  try {
    const result = await safeFetch("/api/attendance/summary");
    if (!result.ok) return;
    const data = result.data?.data || {};
    updateReportField("present", data.present ?? 0);
    updateReportField("late", data.late ?? 0);
    updateReportField("izin", data.izin ?? 0);
    updateReportField("sakit", data.sakit ?? 0);
  } catch (err) {
    console.error("Failed to load monthly summary", err);
  }
}

function formatDateDisplay(value){
  if (!value) return "-";
  const parts = value.split("-");
  if (parts.length !== 3) return value;
  return `${parts[2]}/${parts[1]}`;
}

function createMethodBadge(method) {
  const methodName = (method || "N/A").toUpperCase().replace(/_/g, " + ");
  let badgeClass = "secondary";
  if (method === "gps_selfie") {
    badgeClass = "primary";
  } else if (method === "qr") {
    badgeClass = "success";
  } else if (method === "gps") {
    badgeClass = "info";
  } else if (method === "manual") {
    badgeClass = "warning";
  }
  return `<span class="badge ${badgeClass}">${methodName}</span>`;
}

function renderDailyReport(records){
  if (!dailyReportRows) return;
  dailyReportRows.innerHTML = "";
  if (!records.length){
    const rowEl = document.createElement("div");
    rowEl.className = "daily-report-row empty";
    rowEl.innerHTML = `<div class="muted">Belum ada</div>`;
    dailyReportRows.appendChild(rowEl);
    return;
  }
  records.forEach((row) => {
    const rowEl = document.createElement("div");
    rowEl.className = "daily-report-row";
    const statusLabel = row.action === "checkout" ? "Pulang" : "Hadir";
    const methodBadge = createMethodBadge(row.method);
    const timeText = row.time ? row.time.slice(0,5) : "-";
    rowEl.innerHTML = `
      <div>${formatDateDisplay(row.date)}<div class="muted">${timeText}</div></div>
      <div>${statusLabel}</div>
      <div>${methodBadge}</div>
    `;
    dailyReportRows.appendChild(rowEl);
  });
}

async function loadDailyReport(){
  if (!dailyReportRows) return;
  try {
    const today = await safeFetch("/api/attendance/today");
    if (!today.ok) {
      dailyReportRows.innerHTML = '<div class="daily-report-row empty"><div class="muted">Gagal memuat laporan harian.</div></div>';
      return;
    }
    const records = today.data?.data || [];
    renderDailyReport(records);
  } catch (err) {
    dailyReportRows.innerHTML = '<div class="daily-report-row empty"><div class="muted">Gagal memuat laporan harian.</div></div>';
    console.error(err);
  }
}

function showPatrolToast(type, message, opts = {}){
  showToast(type, message, { target: patrolToast, ...opts });
}

function patrolStatusClass(status){
  const value = (status || "").toLowerCase();
  if (value === "completed") return "status-completed";
  if (value === "invalid") return "status-invalid";
  if (value === "incomplete") return "status-incomplete";
  if (value === "ongoing") return "status-ongoing";
  return "status-idle";
}

function patrolStatusLabel(status){
  const value = (status || "").toLowerCase();
  if (value === "completed") return "completed";
  if (value === "invalid") return "invalid";
  if (value === "incomplete") return "incomplete";
  if (value === "ongoing") return "ongoing";
  return "idle";
}

function formatPatrolDateTime(value){
  if (!value) return "-";
  const date = new Date(String(value).replace(" ", "T"));
  if (Number.isNaN(date.getTime())) return value;
  const dd = pad2(date.getDate());
  const mm = pad2(date.getMonth() + 1);
  const hh = pad2(date.getHours());
  const mi = pad2(date.getMinutes());
  return `${dd}/${mm} ${hh}:${mi}`;
}

function clearPatrolScanValue(){
  if (patrolScanData) {
    patrolScanData.value = "";
  }
}

function setPatrolMode(mode){
  patrolMode = mode === "nfc" ? "nfc" : "qr";
  patrolModeChips.forEach((chip) => {
    const active = chip.dataset.patrolMode === patrolMode;
    chip.classList.toggle("active", active);
    chip.setAttribute("aria-pressed", active ? "true" : "false");
  });
  patrolScanPanelQr?.classList.toggle("is-hidden", patrolMode !== "qr");
  patrolScanPanelNfc?.classList.toggle("is-hidden", patrolMode !== "nfc");
  if (patrolMode !== "qr") {
    stopPatrolQrScan();
  }
}

function updatePatrolGpsView(active){
  if (patrolGpsStatus) {
    patrolGpsStatus.textContent = active ? "GPS aktif" : "GPS tidak tersedia";
  }
  if (patrolGpsCoords) {
    patrolGpsCoords.textContent =
      patrolGpsLat && patrolGpsLng
        ? `${patrolGpsLat}, ${patrolGpsLng}`
        : "Koordinat belum tersedia.";
  }
}

async function capturePatrolLocation(){
  if (patrolGpsCoords) {
    patrolGpsCoords.textContent = "Mengambil lokasi...";
  }
  const loc = await ensureLocation();
  patrolGpsLat = loc.lat;
  patrolGpsLng = loc.lon;
  patrolGpsAccuracy = loc.accuracy || "";
  patrolGpsDeviceTime = loc.deviceTime || new Date().toISOString();
  updatePatrolGpsView(true);
  return loc;
}

function renderPatrolCheckpointList(rows){
  if (!patrolCheckpointList) return;
  patrolCheckpointList.innerHTML = "";
  if (!rows || !rows.length) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "Belum ada data checkpoint.";
    patrolCheckpointList.appendChild(empty);
    return;
  }
  rows.forEach((row) => {
    const item = document.createElement("article");
    const status = (row.status || "pending").toLowerCase();
    item.className = `patrol-checkpoint-item is-${status}`;

    const seq = document.createElement("span");
    seq.className = "patrol-checkpoint-seq";
    seq.textContent = String(row.sequence_no || "-");

    const body = document.createElement("div");
    body.className = "patrol-checkpoint-body";

    const name = document.createElement("div");
    name.className = "patrol-checkpoint-name";
    name.textContent = row.name || "-";

    const meta = document.createElement("div");
    meta.className = "patrol-checkpoint-meta";
    const marker = row.marker_type ? `Marker: ${row.marker_type.toUpperCase()}` : "Marker: -";
    const scanned = row.scanned_at ? ` • ${formatPatrolDateTime(row.scanned_at)}` : "";
    meta.textContent = `${marker}${scanned}`;

    body.append(name, meta);
    item.append(seq, body);
    patrolCheckpointList.appendChild(item);
  });
}

function renderPatrolHistory(rows){
  if (!patrolHistoryList) return;
  patrolHistoryList.innerHTML = "";
  if (!rows || !rows.length) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "Belum ada riwayat guard tour.";
    patrolHistoryList.appendChild(empty);
    return;
  }
  rows.forEach((row) => {
    const item = document.createElement("div");
    item.className = "story-item";

    const top = document.createElement("div");
    top.className = "story-row";
    const title = document.createElement("span");
    title.textContent = `Route #${row.route_id || "-"}`;
    const status = document.createElement("span");
    status.className = `patrol-history-badge ${patrolStatusClass(row.status)}`;
    status.textContent = patrolStatusLabel(row.status);
    top.append(title, status);

    const bottom = document.createElement("div");
    bottom.className = "muted";
    const progressLabel = `${row.completed_checkpoints || 0}/${row.total_checkpoints || 0}`;
    bottom.textContent = `${row.date || "-"} • ${progressLabel} • ${formatPatrolDateTime(row.started_at)} - ${formatPatrolDateTime(row.ended_at)}`;

    item.append(top, bottom);
    patrolHistoryList.appendChild(item);
  });
}

function renderPatrolState(data){
  patrolState = data || null;
  const route = data?.route || null;
  const checkpoints = Array.isArray(data?.checkpoints) ? data.checkpoints : [];
  const progress = data?.progress || {};
  const constraints = data?.constraints || {};
  const allowed = data?.allowed || {};
  const status = patrolStatusLabel(data?.status);

  if (patrolRouteLabel) {
    patrolRouteLabel.textContent = route
      ? `${route.name || "Route"}${data?.site_name ? ` • ${data.site_name}` : ""}`
      : "Belum ada rute aktif.";
  }
  if (patrolStatusBadge) {
    patrolStatusBadge.textContent = status;
    patrolStatusBadge.className = `patrol-status-badge ${patrolStatusClass(status)}`;
  }
  if (patrolProgressText) {
    patrolProgressText.textContent = `${progress.completed || 0}/${progress.total || 0} checkpoint`;
  }
  if (patrolProgressPercent) {
    patrolProgressPercent.textContent = `${progress.percent || 0}%`;
  }
  if (patrolProgressBar) {
    patrolProgressBar.style.width = `${progress.percent || 0}%`;
  }
  if (patrolSecurityMode) {
    patrolSecurityMode.textContent = constraints.strict_mode
      ? "Strict (GPS + Selfie)"
      : "Standard";
  }
  if (patrolSelfieHint) {
    patrolSelfieHint.textContent = constraints.require_selfie
      ? "Strict mode aktif: selfie wajib di setiap checkpoint."
      : "Selfie opsional, menjadi wajib saat strict mode aktif.";
  }

  let nextText = "-";
  const nextCp = checkpoints.find((cp) => (cp.status || "").toLowerCase() === "next");
  if (nextCp) {
    nextText = `#${nextCp.sequence_no || "-"} ${nextCp.name || "-"}`;
  } else if (status === "completed") {
    nextText = "Semua checkpoint selesai";
  }
  if (patrolNextCheckpoint) {
    patrolNextCheckpoint.textContent = nextText;
  }

  if (btnPatrolStart) {
    btnPatrolStart.disabled = !Boolean(allowed.can_start);
  }
  if (btnPatrolSubmit) {
    btnPatrolSubmit.disabled = !Boolean(allowed.can_scan);
  }
  if (btnPatrolScan) {
    btnPatrolScan.disabled = !Boolean(allowed.can_scan) || patrolMode !== "qr";
  }
  if (btnPatrolNfc) {
    btnPatrolNfc.disabled = !Boolean(allowed.can_scan) || patrolMode !== "nfc";
  }
  if (!allowed.can_scan) {
    stopPatrolQrScan();
  }

  if (patrolUpgradeHint) {
    patrolUpgradeHint.textContent = constraints.pro_upgrade_required
      ? (constraints.pro_upgrade_message || "Rute melebihi 30 checkpoint. Upgrade ke PRO+.")
      : "Batas standar rute adalah 30 checkpoint. Jika lebih, gunakan versi PRO+.";
  }

  renderPatrolCheckpointList(checkpoints);
  renderPatrolHistory(data?.history || []);
}

async function loadPatrolStatus(opts = {}){
  if (!patrolRouteLabel) return;
  const silent = Boolean(opts.silent);
  const result = await safeFetch("/api/patrol/status");
  if (!result.ok) {
    if (!silent) {
      showPatrolToast("error", result.message || "Gagal memuat status guard tour.");
    }
    return;
  }
  const payload = result.data?.data || null;
  renderPatrolState(payload);
}

async function startPatrolTour(){
  if (!btnPatrolStart) return;
  btnPatrolStart.disabled = true;
  const formData = new FormData();
  appendCsrf(formData);
  const result = await safeFetch("/api/patrol/start", {
    method: "POST",
    body: formData,
  });
  showPatrolToast(result.ok ? "success" : "error", result.message || "Selesai.");
  if (result.data?.data) {
    renderPatrolState(result.data.data);
  } else {
    await loadPatrolStatus({ silent: true });
  }
  btnPatrolStart.disabled = false;
}

async function startPatrolQrScan(){
  if (patrolQrActive) {
    stopPatrolQrScan();
    if (patrolScanStatus) patrolScanStatus.textContent = "Scan dihentikan.";
    return;
  }
  if (!("mediaDevices" in navigator) || !navigator.mediaDevices.getUserMedia) {
    if (patrolScanStatus) patrolScanStatus.textContent = "Kamera tidak tersedia.";
    return;
  }
  if (!("BarcodeDetector" in window)) {
    if (patrolScanStatus) patrolScanStatus.textContent = "Browser tidak mendukung scan QR.";
    return;
  }
  try {
    patrolQrDetector = new BarcodeDetector({ formats: ["qr_code", "code_128", "code_39"] });
    if (patrolScanStatus) patrolScanStatus.textContent = "Memulai kamera...";
    patrolQrStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    if (patrolQrVideo) {
      patrolQrVideo.srcObject = patrolQrStream;
      patrolQrVideo.style.display = "block";
      await patrolQrVideo.play();
    }
    patrolQrActive = true;
    patrolQrLoop();
  } catch (err) {
    if (patrolScanStatus) patrolScanStatus.textContent = "Gagal akses kamera.";
    stopPatrolQrScan();
  }
}

async function patrolQrLoop(){
  if (!patrolQrActive || !patrolQrDetector || !patrolQrVideo) return;
  try {
    const barcodes = await patrolQrDetector.detect(patrolQrVideo);
    if (barcodes.length) {
      const rawValue = (barcodes[0].rawValue || "").trim();
      if (rawValue && rawValue !== patrolQrLastValue) {
        patrolQrLastValue = rawValue;
        if (patrolScanData) patrolScanData.value = rawValue;
        if (patrolScanStatus) patrolScanStatus.textContent = "Checkpoint terdeteksi.";
        stopPatrolQrScan();
        return;
      }
    }
  } catch (err) {
    if (patrolScanStatus) patrolScanStatus.textContent = "Gagal scan QR.";
  }
  requestAnimationFrame(patrolQrLoop);
}

function stopPatrolQrScan(){
  patrolQrActive = false;
  patrolQrLastValue = "";
  if (patrolQrStream) {
    patrolQrStream.getTracks().forEach((track) => track.stop());
    patrolQrStream = null;
  }
}

async function startPatrolNfcScan(){
  if (!patrolNfcStatus) return;
  if (!("NDEFReader" in window)) {
    patrolNfcStatus.textContent = "Device ini belum mendukung Web NFC. Gunakan mode QR.";
    return;
  }
  try {
    const ndef = new NDEFReader();
    await ndef.scan();
    patrolNfcStatus.textContent = "Dekatkan device ke NFC tag checkpoint...";
    ndef.onreading = (event) => {
      let payload = event.serialNumber || "";
      if (!payload && event.message?.records?.length) {
        const firstRecord = event.message.records[0];
        if (firstRecord.recordType === "text") {
          const decoder = new TextDecoder(firstRecord.encoding || "utf-8");
          payload = decoder.decode(firstRecord.data);
        }
      }
      payload = (payload || "").trim();
      if (payload) {
        if (patrolScanData) patrolScanData.value = payload;
        patrolNfcStatus.textContent = "NFC checkpoint terdeteksi.";
      }
    };
    ndef.onreadingerror = () => {
      patrolNfcStatus.textContent = "Tag terbaca tetapi data NFC tidak valid.";
    };
  } catch (err) {
    patrolNfcStatus.textContent = "Scan NFC dibatalkan atau gagal diakses.";
  }
}

async function submitPatrolCheckpoint(){
  if (!patrolState?.tour?.id) {
    showPatrolToast("error", "Mulai guard tour terlebih dahulu.");
    return;
  }
  if (!patrolState?.allowed?.can_scan) {
    showPatrolToast("error", "Guard tour tidak dapat di-scan saat ini.");
    return;
  }
  const scanValue = (patrolScanData?.value || "").trim();
  if (!scanValue) {
    showPatrolToast("error", "Lakukan scan checkpoint terlebih dahulu.");
    return;
  }
  if (patrolState?.constraints?.require_gps) {
    try {
      await capturePatrolLocation();
    } catch (err) {
      showPatrolToast("error", "GPS wajib aktif untuk validasi checkpoint.");
      return;
    }
  }

  const formData = new FormData();
  appendCsrf(formData);
  formData.append("tour_id", String(patrolState.tour.id));
  formData.append("method", patrolMode);
  formData.append("scan_data", scanValue);
  if (patrolGpsLat && patrolGpsLng) {
    formData.append("lat", patrolGpsLat);
    formData.append("lng", patrolGpsLng);
    formData.append("accuracy", patrolGpsAccuracy || "");
    formData.append("device_time", patrolGpsDeviceTime || new Date().toISOString());
  }
  const selfie = patrolSelfieFile?.files?.[0];
  if (selfie) {
    formData.append("selfie", selfie);
  }

  if (btnPatrolSubmit) btnPatrolSubmit.disabled = true;
  const result = await safeFetch("/api/patrol/scan", {
    method: "POST",
    body: formData,
  });
  showPatrolToast(result.ok ? "success" : "error", result.message || "Scan selesai.");
  if (result.data?.data) {
    renderPatrolState(result.data.data);
  } else {
    await loadPatrolStatus({ silent: true });
  }
  if (result.ok) {
    clearPatrolScanValue();
    if (patrolSelfieFile) patrolSelfieFile.value = "";
    if (patrolSelfiePreview) {
      patrolSelfiePreview.src = "";
      patrolSelfiePreview.style.display = "none";
    }
  }
  if (btnPatrolSubmit) btnPatrolSubmit.disabled = false;
}

function initPatrolSelfie(){
  patrolSelfieFile?.addEventListener("change", (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      if (patrolSelfiePreview) {
        patrolSelfiePreview.src = "";
        patrolSelfiePreview.style.display = "none";
      }
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (patrolSelfiePreview) {
        patrolSelfiePreview.src = reader.result || "";
        patrolSelfiePreview.style.display = "block";
      }
    };
    reader.readAsDataURL(file);
  });
}

function initPatrol(){
  if (!patrolRouteLabel) return;
  setPatrolMode("qr");
  patrolModeChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      setPatrolMode(chip.dataset.patrolMode || "qr");
    });
  });
  btnPatrolRefresh?.addEventListener("click", () => loadPatrolStatus());
  btnPatrolStart?.addEventListener("click", () => startPatrolTour());
  btnPatrolScan?.addEventListener("click", () => startPatrolQrScan());
  btnPatrolNfc?.addEventListener("click", () => startPatrolNfcScan());
  btnPatrolSubmit?.addEventListener("click", () => submitPatrolCheckpoint());
  btnPatrolLocation?.addEventListener("click", async () => {
    try {
      await capturePatrolLocation();
    } catch (err) {
      updatePatrolGpsView(false);
      showPatrolToast("error", "Gagal mendapatkan lokasi checkpoint.");
    }
  });
  initPatrolSelfie();
  loadPatrolStatus({ silent: true });
  if (patrolAutoRefreshTimer) window.clearInterval(patrolAutoRefreshTimer);
  patrolAutoRefreshTimer = window.setInterval(() => {
    if (!document.hidden) {
      loadPatrolStatus({ silent: true });
    }
  }, 25000);
}

function go(index){
  const max = 3;
  swipeIndex = Math.max(0, Math.min(max, index));
  const offset = swipeIndex * 100;
  swipeTrack.style.transform = `translateX(-${offset}%)`;
  navButtons.forEach((btn) => {
    const tab = parseInt(btn.dataset.tab, 10);
    if (Number.isNaN(tab)) return;
    btn.classList.toggle("active", tab === swipeIndex);
  });
  if (swipeIndex !== 1) {
    closeLeaveSheet();
    closeLeaveDetail();
  }
  if (swipeIndex === 3) {
    loadPatrolStatus({ silent: true });
  }
}

navButtons.forEach((btn) => {
  if (!btn.dataset.tab) return;
  btn.addEventListener("click", () => go(parseInt(btn.dataset.tab, 10)));
});

function initSwipe(){
  if (!swipeViewport) return;
  let startX = 0;
  let startY = 0;
  let moved = false;

  swipeViewport.addEventListener("touchstart", (e) => {
    const touch = e.touches[0];
    startX = touch.clientX;
    startY = touch.clientY;
    moved = false;
  }, { passive: true });

  swipeViewport.addEventListener("touchmove", (e) => {
    const touch = e.touches[0];
    const dx = touch.clientX - startX;
    const dy = touch.clientY - startY;
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 10) {
      moved = true;
      e.preventDefault();
    }
  }, { passive: false });

  swipeViewport.addEventListener("touchend", (e) => {
    if (!moved) return;
    const touch = e.changedTouches[0];
    const dx = touch.clientX - startX;
    const dy = touch.clientY - startY;
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
      if (dx < 0) go(swipeIndex + 1);
      if (dx > 0) go(swipeIndex - 1);
    }
  });
}

function initNavPosition(){
  if (!floatingNav) return;
  if (floatingNav.classList.contains("bottom-nav-floating")) return;
  floatingNav.style.left = "0";
  floatingNav.style.top = "0";
  floatingNav.style.bottom = "auto";
  const navRect = floatingNav.getBoundingClientRect();
  const x = Math.round((window.innerWidth - navRect.width) / 2);
  const y = Math.round(window.innerHeight - navRect.height - 16);
  floatingNav.style.transform = `translate3d(${x}px, ${y}px, 0)`;
  floatingNav.dataset.x = x;
  floatingNav.dataset.y = y;
}

function initNavDrag(){
  if (!floatingNav || !navHandle) return;
  if (floatingNav.classList.contains("bottom-nav-floating")) return;
  let startX = 0;
  let startY = 0;
  let originX = 0;
  let originY = 0;
  let dragging = false;

  navHandle.addEventListener("pointerdown", (e) => {
    dragging = true;
    navHandle.setPointerCapture(e.pointerId);
    startX = e.clientX;
    startY = e.clientY;
    originX = parseFloat(floatingNav.dataset.x || "0");
    originY = parseFloat(floatingNav.dataset.y || "0");
  });

  navHandle.addEventListener("pointermove", (e) => {
    if (!dragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    const navRect = floatingNav.getBoundingClientRect();
    const maxX = window.innerWidth - navRect.width;
    const maxY = window.innerHeight - navRect.height;
    let nextX = Math.min(Math.max(originX + dx, 0), maxX);
    let nextY = Math.min(Math.max(originY + dy, 0), maxY);
    floatingNav.style.transform = `translate3d(${nextX}px, ${nextY}px, 0)`;
    floatingNav.dataset.x = nextX;
    floatingNav.dataset.y = nextY;
  });

  navHandle.addEventListener("pointerup", () => {
    dragging = false;
  });
}

async function getLocation(){
    const permission = await requestLocationPermission();
    if (!permission) {
        setLocationStatus(false);
        throw new Error("Izin lokasi ditolak.");
    }

    try {
        const pos = await Geolocation.getCurrentPosition({ enableHighAccuracy: true, timeout: 12000 });
        setLocationStatus(true);
        hasLocation = true;
        updatePresenceReadiness();
        return pos;
    } catch (err) {
        setLocationStatus(false);
        hasLocation = Boolean(latEl?.value && lonEl?.value);
        updatePresenceReadiness();
        throw err;
    }
}

function validateQrPayload(value){
  const payload = (value || "").trim();
  if (!payload) return { ok: false, message: "QR code wajib di-scan." };
  if (payload.includes("|")) {
    const parts = payload.split("|");
    if (parts.length !== 4 && parts.length !== 5) {
      return { ok: false, message: "QR tidak valid." };
    }
    if (parts[0].toUpperCase() !== "GMI") {
      return { ok: false, message: "QR tidak dikenali." };
    }
    if (!/^\d+$/.test(parts[1] || "")) {
      return { ok: false, message: "QR tidak valid." };
    }
    return { ok: true, message: "ok" };
  }
  if (payload.toUpperCase().startsWith("GMI-")) {
    return { ok: true, message: "ok" };
  }
  return { ok: false, message: "QR tidak dikenali." };
}

btnLocation?.addEventListener("click", async () => {
  try {
    if (kpiLocationCoords) {
      kpiLocationCoords.textContent = "Mengambil lokasi...";
    }
    const pos = await getLocation();
    latEl.value = pos.coords.latitude.toFixed(6);
    lonEl.value = pos.coords.longitude.toFixed(6);
    lastAccuracy = String(pos.coords.accuracy || "");
    lastDeviceTime = new Date().toISOString();
    hasLocation = true;
    refreshLocationCoords();
    btnLocation?.classList.add("is-ready");
    updatePresenceReadiness();
  } catch (err) {
    if (kpiLocationCoords) {
      kpiLocationCoords.textContent = "Gagal ambil lokasi.";
    }
    btnLocation?.classList.remove("is-ready");
    hasLocation = Boolean(latEl?.value && lonEl?.value);
    updatePresenceReadiness();
  }
});

if (btnLocation) {
  window.addEventListener("load", () => {
    btnLocation.click();
  });
}

selfieFile?.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (!file) {
    resetSelfieSelection();
    return;
  }
  updateSelfiePickState(true);
  const reader = new FileReader();
  reader.onload = () => {
    selfiePreview.src = reader.result || "";
    selfiePreview.style.display = "block";
    // Update presence readiness when selfie is selected
    updatePresenceReadiness();
  };
  reader.readAsDataURL(file);
});

selfiePreview?.addEventListener("click", () => {
  if (!selfieFile || selfiePreview.style.display === "none") return;
  resetSelfieSelection();
  selfieFile.click();
});

async function startScan(){
  if (!("mediaDevices" in navigator) || !navigator.mediaDevices.getUserMedia) {
    qrStatus.textContent = "Kamera tidak tersedia.";
    return;
  }
  if (!("BarcodeDetector" in window)) {
    qrStatus.textContent = "Browser tidak mendukung scan QR.";
    return;
  }
  try {
    qrDetector = new BarcodeDetector({ formats: ["qr_code", "code_128", "code_39"] });
    qrStatus.textContent = "Memulai kamera...";
    qrStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    qrVideo.srcObject = qrStream;
    qrVideo.style.display = "block";
    await qrVideo.play();
    qrActive = true;
    scanLoop();
  } catch (err) {
    qrStatus.textContent = "Gagal akses kamera.";
    stopScan();
  }
}

async function scanLoop(){
  if (!qrActive || !qrDetector) return;
  try {
    const barcodes = await qrDetector.detect(qrVideo);
    if (barcodes.length) {
      const rawValue = barcodes[0].rawValue || "";
      if (rawValue === qrLastValue) {
        requestAnimationFrame(scanLoop);
        return;
      }
      qrLastValue = rawValue;
      const validation = validateQrPayload(rawValue);
      if (!validation.ok) {
        qrStatus.textContent = validation.message;
        requestAnimationFrame(scanLoop);
        return;
      }
      qrData.value = rawValue;
      qrStatus.textContent = "QR terdeteksi.";
      stopScan();
      return;
    }
  } catch (err) {
    qrStatus.textContent = "Gagal scan QR.";
  }
  requestAnimationFrame(scanLoop);
}

function stopScan(){
  qrActive = false;
  qrLastValue = "";
  if (qrStream) {
    qrStream.getTracks().forEach((t) => t.stop());
    qrStream = null;
  }
}

btnScan?.addEventListener("click", () => {
  if (qrActive) {
    stopScan();
    qrStatus.textContent = "Scan dihentikan.";
    return;
  }
  startScan();
});

leaveAttachment?.addEventListener("change", () => {
  const file = leaveAttachment?.files?.[0];
  if (!file) return;
});

function setPresenceLoading(activeBtn, isLoading){
  [btnCheckin, btnCheckout].forEach((btn) => {
    if (!btn) return;
    const label = btn.querySelector(".btn-label");
    if (label) {
      if (!btn.dataset.label) {
        btn.dataset.label = label.textContent || "";
      }
      label.textContent = isLoading && btn === activeBtn ? "Memproses..." : (btn.dataset.label || label.textContent);
    }
    btn.disabled = isLoading;
    btn.classList.toggle("is-loading", isLoading && btn === activeBtn);
    btn.setAttribute("aria-busy", isLoading && btn === activeBtn ? "true" : "false");
  });
}

function updateLastAction(badgeText){
  const now = new Date();
  if (lastActionTime) {
    lastActionTime.textContent = `${pad2(now.getHours())}:${pad2(now.getMinutes())}`;
  }
  if (lastActionBadge) {
    lastActionBadge.textContent = badgeText;
    lastActionBadge.classList.toggle("in", badgeText === "IN");
    lastActionBadge.classList.toggle("out", badgeText === "OUT");
  }
  refreshMasukKpi();
  refreshAbsentKpi();
}

async function ensureLocation(){
  const lat = latEl.value;
  const lon = lonEl.value;
  if (lat && lon) {
    setLocationStatus(true);
    hasLocation = true;
    btnLocation?.classList.add("is-ready");
    refreshLocationCoords();
    updatePresenceReadiness();
    return { lat, lon, accuracy: lastAccuracy, deviceTime: lastDeviceTime };
  }
  const pos = await getLocation();
  const nextLat = pos.coords.latitude.toFixed(6);
  const nextLon = pos.coords.longitude.toFixed(6);
  latEl.value = nextLat;
  lonEl.value = nextLon;
  lastAccuracy = String(pos.coords.accuracy || "");
  lastDeviceTime = new Date().toISOString();
  refreshLocationCoords();
  hasLocation = true;
  setLocationStatus(true);
  btnLocation?.classList.add("is-ready");
  updatePresenceReadiness();
  return { lat: nextLat, lon: nextLon, accuracy: lastAccuracy, deviceTime: lastDeviceTime };
}

async function submitAttendance(url, labelEl){
  applyAttendanceModes();
  const enabledModes = getEnabledAttendanceModes();
  let method = attMethod?.value || "gps_selfie";
  if (!enabledModes.includes(method)) {
    method = enabledModes[0];
    if (attMethod) attMethod.value = method;
  }

  // Validate method-specific requirements
  let locationData = null;
  
  if (method === "qr") {
    // QR mode: validate QR data
    if (!qrData?.value?.trim()) {
      showToast("error", "QR code wajib di-scan.", { target: attToast });
      return { ok: false };
    }
    const validation = validateQrPayload(qrData?.value || "");
    if (!validation.ok) {
      showToast("error", validation.message, { target: attToast });
      return { ok: false };
    }
  } else {
    // GPS and GPS+Selfie modes: require location
    try {
      locationData = await ensureLocation();
    } catch (err) {
      showToast("error", "Lokasi GPS wajib diisi.", { target: attToast });
      return { ok: false };
    }

    // GPS+Selfie specific: validate selfie
    if (method === "gps_selfie") {
      const file = selfieFile?.files?.[0];
      if (!file) {
        showToast("error", "Selfie wajib untuk presensi.", { target: attToast });
        return { ok: false };
      }
    }
  }

  const file = selfieFile?.files?.[0];
  const formData = new FormData();
  appendCsrf(formData);
  formData.append("method", method);
  
  // Only append location data for GPS-based methods
  if (method !== "qr" && locationData) {
    formData.append("lat", locationData.lat);
    formData.append("lng", locationData.lon);
    formData.append("accuracy", locationData.accuracy || "");
    formData.append("device_time", locationData.deviceTime || new Date().toISOString());
  }
  
  // Append selfie if present
  if (file) {
    formData.append("selfie", file);
  }
  
  // Append QR data if present
  if (qrData?.value?.trim()) {
    formData.append("qr_data", qrData.value.trim());
  }

  const result = await safeFetch(url, { method: "POST", body: formData });
  showToast(result.ok ? "success" : "error", result.message || "Selesai.", { target: attToast });
  if (result.ok && labelEl) {
    const now = new Date();
    labelEl.textContent = `${labelEl.dataset.label}: ${pad2(now.getHours())}:${pad2(now.getMinutes())}`;
  }
  return { ok: result.ok };
}

async function handleAttendance(action){
  const isCheckin = action === "checkin";
  const url = isCheckin ? "/api/attendance/checkin" : "/api/attendance/checkout";
  const labelEl = isCheckin ? checkinStatus : checkoutStatus;
  const activeBtn = isCheckin ? btnCheckin : btnCheckout;
  const badgeText = isCheckin ? "IN" : "OUT";
  if (!activeBtn) return;
  
  if (isCheckin && presenceStatusTitle?.textContent === "Belum siap Absen") {
    showToast("error", "Belum siap absen. Pastikan lokasi aktif dan internet tersambung.", { target: attToast });
    return;
  }
  if (!isCheckin && !hasCheckedIn) {
    showToast("error", "Belum check-in. Silakan Masuk terlebih dahulu.", { target: attToast });
    return;
  }
  if (!isCheckin) {
    const confirmText = window.prompt('Ketik "yes" untuk konfirmasi pulang');
    if (!confirmText || confirmText.trim().toLowerCase() !== "yes") {
      showToast("error", "Konfirmasi dibatalkan.", { target: attToast });
      return;
    }
  }
  const start = Date.now();
  setPresenceLoading(activeBtn, true);
  const result = await submitAttendance(url, labelEl);
  const elapsed = Date.now() - start;
  if (elapsed < 2000) {
    await new Promise((resolve) => setTimeout(resolve, 2000 - elapsed));
  }
  setPresenceLoading(activeBtn, false);
  if (result.ok) {
    hasCheckedIn = isCheckin;
    updateLastAction(badgeText);
    updatePresenceReadiness();
    
    // UBAH BUTTON STATE KE SUCCESS
    activeBtn.classList.add("is-success");
    activeBtn.disabled = true;
    
    // Ubah text button
    const btnLabel = activeBtn.querySelector(".btn-label");
    if (btnLabel) {
      btnLabel.textContent = isCheckin ? "✓ Sudah Masuk" : "✓ Sudah Pulang";
    }
    
    // Update status badge
    if (presenceStatusTitle) {
      presenceStatusTitle.textContent = isCheckin ? "Siap Absen Pulang" : "✓ Sudah Pulang";
      presenceStatusTitle.classList.remove("is-ready");
      presenceStatusTitle.classList.add("is-done");
    }
    
    // Update KPI Card dengan jam checkin/checkout
    if (isCheckin && (kpiMasukValue || kpiMasukMeta)) {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, "0");
      const minutes = String(now.getMinutes()).padStart(2, "0");
      const waktuCheckin = `${hours}:${minutes}`;
      
      if (kpiMasukValue) {
        kpiMasukValue.textContent = waktuCheckin;
      }
      if (kpiMasukMeta) {
        kpiMasukMeta.textContent = `Status: ✓ Sudah Checkin (${waktuCheckin})`;
      }
      
      // Add success class ke KPI card
      const kpiCard = document.querySelector('[data-card="masuk"]');
      if (kpiCard) {
        kpiCard.classList.add("is-success");
      }
    }
  }
}

btnCheckin?.addEventListener("click", () => handleAttendance("checkin"));
btnCheckout?.addEventListener("click", () => handleAttendance("checkout"));

/**
 * Restore attendance state dari server setelah login
 * Fitur: Jika user sudah checkin, state tetap persisted meskipun logout
 */
async function restoreAttendanceState(){
  try {
    const result = await safeFetch("/api/attendance/today");
    console.log("[RESTORE] API response:", result);
    if (!result.ok || !result.data) {
      console.log("[RESTORE] Skipped: API not ok or no data");
      return;
    }
    const records = result.data.data || [];
    console.log("[RESTORE] Records from API:", records, "Count:", records.length);
    if (records.length === 0) {
      console.log("[RESTORE] No records found");
      return;
    }
    if (records.length > 0) {
      console.log("[RESTORE] First record structure:", Object.keys(records[0]));
      console.log("[RESTORE] First record sample:", records[0]);
    }
    // Sort by created_at ascending untuk proper sequence check
    try {
      records.sort((a, b) => {
        const aDate = a.created_at ? new Date(a.created_at) : new Date(0);
        const bDate = b.created_at ? new Date(b.created_at) : new Date(0);
        if (isNaN(aDate.getTime())) {
          console.warn("[RESTORE] Invalid date for A:", a);
        }
        if (isNaN(bDate.getTime())) {
          console.warn("[RESTORE] Invalid date for B:", b);
        }
        return aDate - bDate;
      });
      console.log("[RESTORE] Sort successful");
    } catch (sortErr) {
      console.error("[RESTORE] Sort error, using original order:", sortErr);
    }
    console.log("[RESTORE] Sorted records:", records);
    // Cek sequence: checkin diikuti checkout atau belum
    let hasCheckinToday = false;
    let hasCheckoutToday = false;
    let lastCheckinTime = null;
    let checkinFound = false;
    for (const record of records) {
      console.log("[RESTORE] Processing record:", record);
      if (record.action === "checkin") {
        hasCheckinToday = true;
        checkinFound = true;
        lastCheckinTime = record.time;
        hasCheckoutToday = false; // Reset checkout flag untuk checkin baru
        console.log("[RESTORE] Found checkin:", record);
      }
      if (record.action === "checkout" && checkinFound) {
        hasCheckoutToday = true;
        console.log("[RESTORE] Found checkout:", record);
      }
    }
    console.log("[RESTORE] Final state:", {hasCheckinToday, hasCheckoutToday, lastCheckinTime});
    // Log DOM elements
    console.log("[RESTORE] DOM kpiMasukValue:", kpiMasukValue);
    console.log("[RESTORE] DOM kpiMasukMeta:", kpiMasukMeta);
    console.log("[RESTORE] DOM btnCheckin:", btnCheckin);
    console.log("[RESTORE] DOM presenceStatusTitle:", presenceStatusTitle);
    // Update state variable
    hasCheckedIn = hasCheckinToday && !hasCheckoutToday;
    console.log("[RESTORE] hasCheckedIn global:", hasCheckedIn);
    // Restore button state jika sudah checkin
    if (hasCheckinToday && !hasCheckoutToday) {
      console.log("[RESTORE] Restoring checkin state...");
      if (btnCheckin) {
        console.log("[RESTORE] btnCheckin found, adding is-success class");
        btnCheckin.classList.add("is-success");
        btnCheckin.disabled = true;
        const btnLabel = btnCheckin.querySelector(".btn-label");
        if (btnLabel) {
          btnLabel.textContent = "✓ Sudah Masuk";
        } else {
          console.log("[RESTORE] btnLabel not found inside btnCheckin");
        }
      } else {
        console.log("[RESTORE] WARNING: btnCheckin is null/undefined");
      }
      if (presenceStatusTitle) {
        console.log("[RESTORE] Updating presenceStatusTitle");
        presenceStatusTitle.textContent = "Siap Absen Pulang";
        presenceStatusTitle.classList.remove("is-ready");
        presenceStatusTitle.classList.add("is-done");
      } else {
        console.log("[RESTORE] WARNING: presenceStatusTitle is null/undefined");
      }
      if (lastCheckinTime && (kpiMasukValue || kpiMasukMeta)) {
        console.log("[RESTORE] Updating KPI card with time:", lastCheckinTime);
        if (kpiMasukValue) {
          kpiMasukValue.textContent = lastCheckinTime;
        } else {
          console.log("[RESTORE] kpiMasukValue is null/undefined");
        }
        if (kpiMasukMeta) {
          kpiMasukMeta.textContent = `Status: ✓ Sudah Checkin (${lastCheckinTime})`;
        } else {
          console.log("[RESTORE] kpiMasukMeta is null/undefined");
        }
        const kpiCard = document.querySelector('[data-card="masuk"]');
        if (kpiCard) {
          kpiCard.classList.add("is-success");
        } else {
          console.log("[RESTORE] kpiCard [data-card=masuk] not found");
        }
      } else {
        console.log("[RESTORE] WARNING: KPI elements missing or no checkinTime", {lastCheckinTime, kpiMasukValue: !!kpiMasukValue, kpiMasukMeta: !!kpiMasukMeta});
      }
      if (checkinStatus) {
        checkinStatus.textContent = `Check-in: ${lastCheckinTime}`;
      } else {
        console.log("[RESTORE] checkinStatus is null/undefined");
      }
    }
    if (hasCheckoutToday) {
      console.log("[RESTORE] Restoring checkout state...");
      if (btnCheckout) {
        btnCheckout.classList.add("is-success");
        btnCheckout.disabled = true;
        const btnLabel = btnCheckout.querySelector(".btn-label");
        if (btnLabel) {
          btnLabel.textContent = "✓ Sudah Pulang";
        } else {
          console.log("[RESTORE] btnLabel not found inside btnCheckout");
        }
      }
      if (presenceStatusTitle) {
        presenceStatusTitle.textContent = "✓ Sudah Pulang";
        presenceStatusTitle.classList.remove("is-ready");
        presenceStatusTitle.classList.add("is-done");
      }
    }
  } catch (err) {
    console.error("[RESTORE] ERROR:", err);
  }
}

async function loadLeaveStory(){
  if (!leaveStory) return;
  try {
    leaveStory.innerHTML = '<div class="muted">Memuat data...</div>';
    const result = await safeFetch("/api/leave/my");
    if (!result.ok) {
      showToast("error", result.message || "Gagal memuat data", { target: leaveToast });
      leaveStory.innerHTML = '<div class="muted">Gagal memuat data.</div>';
      return;
    }
    const rows = result.data?.data || [];
    const pendingCount = rows.filter((r) => r.status === "pending").length;
    if (leavePendingCount) {
      leavePendingCount.textContent = `Menunggu: ${pendingCount}`;
      leavePendingCount.classList.toggle("is-pending", pendingCount > 0);
    }
    leaveStory.innerHTML = "";
    if (!rows.length) {
      const empty = document.createElement("div");
      empty.className = "muted";
      empty.textContent = "Belum ada pengajuan.";
      leaveStory.appendChild(empty);
      return;
    }
    rows.forEach((r) => {
      const range = `${r.date_from} s/d ${r.date_to}`;
      const rawType = (r.type || "").toLowerCase();
      const typeLabel = rawType === "izin" ? "Izin" : (r.type || "").toUpperCase();
      const status = (r.status || "pending").toLowerCase();
      const statusClass = status === "approved" ? "badge-approved" : status === "rejected" ? "badge-rejected" : "badge-pending";

      const item = document.createElement("div");
      item.className = "story-item";
      item.dataset.reason = r.reason || "-";
      item.dataset.note = r.note || "-";
      item.dataset.type = typeLabel || "-";
      item.dataset.typeRaw = rawType || "";
      item.dataset.range = range;

      const rowTop = document.createElement("div");
      rowTop.className = "story-row";
      const typeBadge = document.createElement("span");
      typeBadge.className = "badge";
      typeBadge.textContent = typeLabel || "-";
      if (rawType) {
        typeBadge.dataset.leaveType = rawType;
      }
      const dateSpan = document.createElement("span");
      dateSpan.className = "story-date";
      dateSpan.textContent = range;
      rowTop.append(typeBadge, dateSpan);

      const rowBottom = document.createElement("div");
      rowBottom.className = "story-row";
      const statusBadge = document.createElement("span");
      statusBadge.className = `badge ${statusClass}`;
      statusBadge.textContent = status;
      const meta = document.createElement("span");
      meta.className = "meta";
      meta.textContent = "Tap untuk detail";
      rowBottom.append(statusBadge, meta);

      item.append(rowTop, rowBottom);
      leaveStory.appendChild(item);
    });
  } catch (err) {
    showToast("error", "Gagal memuat data", { target: leaveToast });
  }
}

btnLeave?.addEventListener("click", async () => {
  if (!leaveFrom.value || !leaveTo.value) {
    showToast("error", "Tanggal mulai dan akhir wajib diisi.", { target: leaveToast });
    return;
  }
  const parsedFrom = parseIsoDate(leaveFrom.value);
  const parsedTo = parseIsoDate(leaveTo.value);
  if (!parsedFrom || !parsedTo) {
    showToast("error", "Tanggal tidak valid.", { target: leaveToast });
    return;
  }
  if (parsedTo.date < parsedFrom.date) {
    showToast("error", "Tanggal akhir harus setelah tanggal mulai.", { target: leaveToast });
    return;
  }
  if (leaveReason.value.trim().length < 5) {
    showToast("error", "Alasan minimal 5 karakter.", { target: leaveToast });
    return;
  }
  const file = leaveAttachment?.files?.[0];
  if (file) {
    const maxSize = 2 * 1024 * 1024;
    if (file.size > maxSize) {
      showToast("error", "Lampiran maksimal 2MB.", { target: leaveToast });
      return;
    }
    const isImage = file.type.startsWith("image/");
    const isPdf = file.type === "application/pdf";
    if (!isImage && !isPdf) {
      showToast("error", "Lampiran harus gambar atau PDF.", { target: leaveToast });
      return;
    }
  }
  const formData = new FormData();
  appendCsrf(formData);
  formData.append("type", leaveType.value);
  formData.append("date_from", parsedFrom.iso);
  formData.append("date_to", parsedTo.iso);
  formData.append("reason", leaveReason.value.trim());
  if (file) {
    formData.append("attachment", file);
  }
  const result = await safeFetch("/api/leave/request", {
    method: "POST",
    body: formData,
  });
  showToast(result.ok ? "success" : "error", result.message || "Selesai.", { target: leaveToast });
  if (result.ok) {
    leaveReason.value = "";
    leaveAttachment.value = "";
    closeLeaveSheet();
    loadLeaveStory();
  }
});

function initStatusLabels(){
  if (checkinStatus) checkinStatus.dataset.label = "Check-in";
  if (checkoutStatus) checkoutStatus.dataset.label = "Check-out";
}

function setMethod(value){
  if (!attMethod) return;
  attMethod.value = value;
  const label = getMethodLabel(value);
  modeChips.forEach((chip) => {
    const isActive = chip.dataset.mode === value;
    chip.classList.toggle("active", isActive);
    chip.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
  const chipsContainer = document.getElementById("attendanceModeChips");
  if (chipsContainer) {
    chipsContainer.dataset.activeMode = value;
  }
  if (selfieBlock) selfieBlock.classList.toggle("is-hidden", value !== "gps_selfie");
  if (qrBlock) qrBlock.classList.toggle("is-hidden", value !== "qr");
  if (value !== "qr") {
    stopScan();
    if (qrVideo) qrVideo.style.display = "none";
  }
  if (presenceMethodLabel) {
    presenceMethodLabel.textContent = `Metode ${label}`;
  }
  refreshAbsentKpi();
  // Update presence readiness status when method changes
  updatePresenceReadiness();
}

function isAttendanceModeEnabled(mode){
  const key = attendanceModeStorage[mode];
  if (!key) return true;
  const stored = localStorage.getItem(key);
  return stored === null ? true : stored === "1";
}

function getEnabledAttendanceModes(){
  const modes = [];
  if (isAttendanceModeEnabled("gps_selfie")) modes.push("gps_selfie");
  if (isAttendanceModeEnabled("gps")) modes.push("gps");
  if (isAttendanceModeEnabled("qr")) modes.push("qr");
  if (!modes.length) {
    modes.push("gps_selfie");
  }
  return modes;
}

function applyAttendanceModes(){
  if (!attMethod) return;
  const enabled = getEnabledAttendanceModes();
  const current = attMethod.value || enabled[0];
  const next = enabled.includes(current) ? current : enabled[0];
  setMethod(next);
}

function initMethodChips(){
  if (!attMethod || !modeChips.length) return;
  setMethod(attMethod.value || "gps_selfie");
  
  // Disable method toggle - chips are for display only now
  modeChips.forEach((chip) => {
    chip.style.pointerEvents = "none";
    chip.style.opacity = "0.6";
    chip.removeEventListener("click", null); // Remove any previous click handlers
    chip.setAttribute("disabled", "true");
    chip.setAttribute("aria-disabled", "true");
  });
  
  // Also disable attMethod input
  if (attMethod) {
    attMethod.disabled = true;
    attMethod.style.opacity = "0.6";
  }
}

function updateOnlineStatus(){
  isOnline = navigator.onLine;
  refreshNetworkBadge();
  updatePresenceReadiness();
}

function initHelpModal(){
  if (!helpModal || !btnHelp || !btnHelpClose) return;
  btnHelp.addEventListener("click", () => {
    helpModal.classList.add("active");
    helpModal.setAttribute("aria-hidden", "false");
  });
  btnHelpClose.addEventListener("click", () => {
    helpModal.classList.remove("active");
    helpModal.setAttribute("aria-hidden", "true");
  });
  helpModal.addEventListener("click", (e) => {
    if (e.target === helpModal) {
      helpModal.classList.remove("active");
      helpModal.setAttribute("aria-hidden", "true");
    }
  });
}

function openLeaveSheet(type){
  if (!leaveSheet || !leaveType) return;
  leaveType.value = type;
  if (leaveTypeLabel) {
    leaveTypeLabel.textContent = type.charAt(0).toUpperCase() + type.slice(1);
  }
  leaveSheet.classList.add("leave-sheet-open");
  leaveSheet.setAttribute("aria-hidden", "false");
  leaveSheet.scrollIntoView({ behavior: "smooth", block: "start" });
}

function closeLeaveSheet(){
  if (!leaveSheet) return;
  leaveSheet.classList.remove("leave-sheet-open");
  leaveSheet.setAttribute("aria-hidden", "true");
}

function initLeaveActions(){
  leaveActionButtons.forEach((btn) => {
    btn.addEventListener("click", () => openLeaveSheet(btn.dataset.type || "izin"));
  });
  btnLeaveRefresh?.addEventListener("click", () => loadLeaveStory());
  leaveSheetClose?.addEventListener("click", () => closeLeaveSheet());
}

function openLeaveDetail(item){
  if (!leaveDetailModal) return;
  if (leaveDetailType) {
    const rawType = item.dataset.typeRaw || "";
    const label = rawType === "izin" ? "Izin" : (item.dataset.type || "-");
    leaveDetailType.textContent = label;
    if (rawType) {
      leaveDetailType.dataset.leaveType = rawType;
    } else {
      delete leaveDetailType.dataset.leaveType;
    }
  }
  if (leaveDetailRange) leaveDetailRange.textContent = item.dataset.range || "-";
  if (leaveDetailReason) leaveDetailReason.textContent = item.dataset.reason || "-";
  if (leaveDetailNote) leaveDetailNote.textContent = item.dataset.note || "-";
  leaveDetailModal.classList.add("active");
  leaveDetailModal.setAttribute("aria-hidden", "false");
}

function closeLeaveDetail(){
  if (!leaveDetailModal) return;
  leaveDetailModal.classList.remove("active");
  leaveDetailModal.setAttribute("aria-hidden", "true");
}

function initLeaveDetail(){
  leaveStory?.addEventListener("click", (e) => {
    const target = e.target.closest(".story-item");
    if (!target) return;
    openLeaveDetail(target);
  });
  leaveDetailClose?.addEventListener("click", closeLeaveDetail);
  leaveDetailModal?.addEventListener("click", (e) => {
    if (e.target === leaveDetailModal) closeLeaveDetail();
  });
}

let clockTimer = null;
function startClock(){
  if (clockTimer) window.clearInterval(clockTimer);
  tickClock();
  clockTimer = window.setInterval(tickClock, 1000);
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initProfile();
  startClock();
  initSwipe();
  initNavPosition();
  initNavDrag();
  initStatusLabels();
  initMethodChips();
  applyAttendanceModes();
  initHelpModal();
  updateOnlineStatus();
  checkLocationStatus();
  hasLocation = Boolean(latEl?.value && lonEl?.value);

  // Load persistent checkin state dari server SEBELUM update readiness
  restoreAttendanceState();

  // SETELAH restore state, baru update readiness
  updatePresenceReadiness();
  initLeaveActions();
  initLeaveDetail();
  loadLeaveStory();
  loadMonthlySummary();
  loadDailyReport();
  initPatrol();

  go(0);
  refreshLocationKpi();
  refreshLocationCoords();
  refreshMasukKpi();
  refreshAbsentKpi();
});

let navResizeTimer = null;
window.addEventListener("resize", () => {
  if (navResizeTimer) window.clearTimeout(navResizeTimer);
  navResizeTimer = window.setTimeout(initNavPosition, 150);
});
window.addEventListener("online", updateOnlineStatus);
window.addEventListener("offline", updateOnlineStatus);
window.addEventListener("pagehide", () => {
  stopScan();
  stopPatrolQrScan();
});
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopScan();
    stopPatrolQrScan();
    if (clockTimer) window.clearInterval(clockTimer);
  } else {
    startClock();
  }
});
