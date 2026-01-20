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
const modeChips = Array.from(document.querySelectorAll(".chip"));
const btnLocation = document.getElementById("btnLocation");
const locStatus = document.getElementById("locStatus");
const latEl = document.getElementById("lat");
const lonEl = document.getElementById("lon");
const presenceStatusTitle = document.getElementById("presenceStatusTitle");
const presenceStatusSub = document.getElementById("presenceStatusSub");
const presenceLocationIcon = document.getElementById("presenceLocationIcon");
const selfieFile = document.getElementById("selfieFile");
const selfiePreview = document.getElementById("selfiePreview");
const btnSelfieReset = document.getElementById("btnSelfieReset");
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
const netStatus = document.getElementById("netStatus");
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
const attendanceModeStorage = {
  gps_selfie: "gmi_att_mode_gps_selfie",
  gps: "gmi_att_mode_gps",
  qr: "gmi_att_mode_qr",
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
  if (!presenceStatusTitle) return;
  const ready = isOnline && locationActive && hasLocation;
  presenceStatusTitle.textContent = ready ? "Siap Absen" : "Belum siap Absen";
  if (btnLocation) {
    btnLocation.classList.toggle("is-warning", !hasLocation);
  }
  if (btnCheckin) {
    btnCheckin.disabled = !ready;
    btnCheckin.setAttribute("aria-disabled", ready ? "false" : "true");
  }
  if (btnCheckout) {
    const canCheckout = ready && hasCheckedIn;
    btnCheckout.disabled = !canCheckout;
    btnCheckout.setAttribute("aria-disabled", canCheckout ? "false" : "true");
  }
}

function setLocationStatus(active, message){
  if (!presenceStatusSub) return;
  locationActive = active;
  const nextMessage = message || (active
    ? "Lokasi aktif"
    : "Lokasi tidak aktif, mohon aktifkan lokasi di pengaturan.");
  presenceStatusSub.textContent = nextMessage;
  if (presenceLocationIcon) {
    presenceLocationIcon.classList.toggle("status-icon-ok", active);
    presenceLocationIcon.classList.toggle("status-icon-warning", !active);
  }
  updatePresenceReadiness();
}

async function checkLocationStatus(){
  if (!presenceStatusSub) return;
  if (!navigator.geolocation) {
    setLocationStatus(false);
    return;
  }
  if (navigator.permissions && navigator.permissions.query) {
    try {
      const perm = await navigator.permissions.query({ name: "geolocation" });
      const applyState = () => {
        if (perm.state === "granted") {
          setLocationStatus(true);
        } else {
          setLocationStatus(false);
        }
      };
      applyState();
      perm.onchange = applyState;
      return;
    } catch (err) {
      setLocationStatus(false);
      return;
    }
  }
  setLocationStatus(false);
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

function go(index){
  const max = 2;
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

function getLocation(){
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      setLocationStatus(false);
      reject(new Error("Browser tidak mendukung GPS."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocationStatus(true);
        hasLocation = true;
        updatePresenceReadiness();
        resolve(pos);
      },
      (err) => {
        setLocationStatus(false);
        hasLocation = Boolean(latEl?.value && lonEl?.value);
        updatePresenceReadiness();
        reject(err);
      },
      { enableHighAccuracy: true, timeout: 12000 }
    );
  });
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
    locStatus.textContent = "Mengambil lokasi...";
    const pos = await getLocation();
    latEl.value = pos.coords.latitude.toFixed(6);
    lonEl.value = pos.coords.longitude.toFixed(6);
    lastAccuracy = String(pos.coords.accuracy || "");
    lastDeviceTime = new Date().toISOString();
    hasLocation = true;
    locStatus.textContent = `${latEl.value}, ${lonEl.value}`;
    locStatus.classList.add("loc-centered");
    btnLocation?.classList.add("is-ready");
    updatePresenceReadiness();
  } catch (err) {
    locStatus.textContent = "Gagal ambil lokasi.";
    locStatus.classList.remove("loc-centered");
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
    const selfiePick = document.querySelector(".selfie-pick");
    selfiePick?.classList.remove("is-ready");
    selfiePreview.style.display = "none";
    btnSelfieReset?.classList.add("is-hidden");
    return;
  }
  const selfiePick = document.querySelector(".selfie-pick");
  selfiePick?.classList.add("is-ready");
  const reader = new FileReader();
  reader.onload = () => {
    selfiePreview.src = reader.result || "";
    selfiePreview.style.display = "block";
    btnSelfieReset?.classList.remove("is-hidden");
  };
  reader.readAsDataURL(file);
});

btnSelfieReset?.addEventListener("click", () => {
  if (selfieFile) selfieFile.value = "";
  if (selfiePreview) {
    selfiePreview.src = "";
    selfiePreview.style.display = "none";
  }
  const selfiePick = document.querySelector(".selfie-pick");
  selfiePick?.classList.remove("is-ready");
  btnSelfieReset?.classList.add("is-hidden");
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
}

async function ensureLocation(){
  const lat = latEl.value;
  const lon = lonEl.value;
  if (lat && lon) {
    setLocationStatus(true);
    hasLocation = true;
    btnLocation?.classList.add("is-ready");
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
  locStatus.textContent = `${nextLat}, ${nextLon}`;
  locStatus.classList.add("loc-centered");
  hasLocation = true;
  setLocationStatus(true);
  btnLocation?.classList.add("is-ready");
  updatePresenceReadiness();
  return { lat: nextLat, lon: nextLon, accuracy: lastAccuracy, deviceTime: lastDeviceTime };
}

async function submitAttendance(url, labelEl){
  let locationData = null;
  try {
    locationData = await ensureLocation();
  } catch (err) {
    showToast("error", "Lokasi GPS wajib diisi.", { target: attToast });
    return { ok: false };
  }

  applyAttendanceModes();
  const enabledModes = getEnabledAttendanceModes();
  let method = attMethod?.value || "gps_selfie";
  if (!enabledModes.includes(method)) {
    method = enabledModes[0];
    if (attMethod) attMethod.value = method;
  }
  const file = selfieFile?.files?.[0];
  if (method === "gps_selfie" && !file) {
    showToast("error", "Selfie wajib untuk presensi.", { target: attToast });
    return { ok: false };
  }
  if (method === "qr" && !qrData?.value?.trim()) {
    showToast("error", "QR code wajib di-scan.", { target: attToast });
    return { ok: false };
  }
  if (method === "qr") {
    const validation = validateQrPayload(qrData?.value || "");
    if (!validation.ok) {
      showToast("error", validation.message, { target: attToast });
      return { ok: false };
    }
  }

  const formData = new FormData();
  appendCsrf(formData);
  formData.append("method", method);
  formData.append("lat", locationData.lat);
  formData.append("lng", locationData.lon);
  formData.append("accuracy", locationData.accuracy || "");
  formData.append("device_time", locationData.deviceTime || new Date().toISOString());
  if (file) {
    formData.append("selfie", file);
  }
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
  }
}

btnCheckin?.addEventListener("click", () => handleAttendance("checkin"));
btnCheckout?.addEventListener("click", () => handleAttendance("checkout"));

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
  modeChips.forEach((chip) => chip.classList.toggle("active", chip.dataset.mode === value));
  if (selfieBlock) selfieBlock.classList.toggle("is-hidden", value !== "gps_selfie");
  if (qrBlock) qrBlock.classList.toggle("is-hidden", value !== "qr");
  if (value !== "qr") {
    stopScan();
    if (qrVideo) qrVideo.style.display = "none";
  }
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
  modeChips.forEach((chip) => {
    chip.addEventListener("click", () => setMethod(chip.dataset.mode));
  });
  attMethod.addEventListener("change", () => setMethod(attMethod.value));
}

function updateOnlineStatus(){
  if (!netStatus) return;
  isOnline = navigator.onLine;
  netStatus.textContent = isOnline ? "Online" : "Offline";
  netStatus.classList.toggle("online", isOnline);
  netStatus.classList.toggle("offline", !isOnline);
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
updatePresenceReadiness();
initLeaveActions();
initLeaveDetail();
loadLeaveStory();
go(0);

let navResizeTimer = null;
window.addEventListener("resize", () => {
  if (navResizeTimer) window.clearTimeout(navResizeTimer);
  navResizeTimer = window.setTimeout(initNavPosition, 150);
});
window.addEventListener("online", updateOnlineStatus);
window.addEventListener("offline", updateOnlineStatus);
window.addEventListener("pagehide", stopScan);
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopScan();
    if (clockTimer) window.clearInterval(clockTimer);
  } else {
    startClock();
  }
});
