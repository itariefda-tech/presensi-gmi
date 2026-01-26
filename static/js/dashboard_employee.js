const attMethod = document.getElementById("attMethod");
const btnLocation = document.getElementById("btnLocation");
const locStatus = document.getElementById("locStatus");
const latEl = document.getElementById("lat");
const lonEl = document.getElementById("lon");
const selfieFile = document.getElementById("selfieFile");
const selfiePreview = document.getElementById("selfiePreview");
const btnScan = document.getElementById("btnScan");
const qrStatus = document.getElementById("qrStatus");
const qrVideo = document.getElementById("qrVideo");
const qrData = document.getElementById("qrData");
const btnCheckin = document.getElementById("btnCheckin");
const attToast = document.getElementById("attToast");
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
const kpiMasukValue = document.getElementById("kpiMasukValue");
const kpiMasukMeta = document.getElementById("kpiMasukMeta");

const leaveType = document.getElementById("leaveType");
const leaveFrom = document.getElementById("leaveFrom");
const leaveTo = document.getElementById("leaveTo");
const leaveReason = document.getElementById("leaveReason");
const leaveAttachment = document.getElementById("leaveAttachment");
const btnLeave = document.getElementById("btnLeave");
const leaveToast = document.getElementById("leaveToast");
const leaveHistory = document.getElementById("leaveHistory");

let selfieData = "";
let qrStream = null;
let qrDetector = null;
let qrActive = false;

function setToast(el, msg, ok = true){
  if (!el) return;
  el.textContent = msg;
  el.style.color = ok ? "#22c55e" : "#fb7185";
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

function appendCsrf(formData){
  if (!formData || !csrfToken) return;
  formData.append("csrf_token", csrfToken);
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

btnLocation?.addEventListener("click", () => {
  if (!locStatus || !latEl || !lonEl) return;
  if (!navigator.geolocation) {
    locStatus.textContent = "Browser tidak mendukung GPS.";
    return;
  }
  locStatus.textContent = "Mengambil lokasi...";
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      latEl.value = pos.coords.latitude.toFixed(6);
      lonEl.value = pos.coords.longitude.toFixed(6);
      locStatus.textContent = `${latEl.value}, ${lonEl.value}`;
    },
    () => {
      locStatus.textContent = "Gagal ambil lokasi.";
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
});

if (btnLocation) {
  window.addEventListener("load", () => {
    btnLocation.click();
  });
}

selfieFile?.addEventListener("change", (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    selfieData = reader.result || "";
    selfiePreview.src = selfieData;
    selfiePreview.style.display = "block";
  };
  reader.readAsDataURL(file);
});

async function startScan(){
  if (!qrStatus || !qrVideo || !qrData) return;
  if (!("mediaDevices" in navigator) || !navigator.mediaDevices.getUserMedia) {
    qrStatus.textContent = "Kamera tidak tersedia.";
    return;
  }
  if (!("BarcodeDetector" in window)) {
    qrStatus.textContent = "Browser tidak mendukung scan QR.";
    return;
  }
  qrDetector = new BarcodeDetector({ formats: ["qr_code", "code_128", "code_39"] });
  qrStatus.textContent = "Memulai kamera...";
  qrStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
  qrVideo.srcObject = qrStream;
  qrVideo.style.display = "block";
  qrActive = true;
  scanLoop();
}

async function scanLoop(){
  if (!qrStatus || !qrVideo || !qrData) return;
  if (!qrActive || !qrDetector) return;
  try {
    const barcodes = await qrDetector.detect(qrVideo);
    if (barcodes.length) {
      qrData.value = barcodes[0].rawValue || "";
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

btnCheckin?.addEventListener("click", async () => {
  if (!attMethod || !latEl || !lonEl || !attToast) return;
  const method = attMethod.value;
  const lat = latEl.value;
  const lon = lonEl.value;

  if (!lat || !lon) {
    setToast(attToast, "Lokasi GPS wajib diisi.", false);
    return;
  }
  if (method === "gps_selfie") {
    const file = selfieFile?.files?.[0];
    if (!file) {
      setToast(attToast, "Selfie wajib untuk GPS + selfie.", false);
      return;
    }
  }
  if (method === "qr") {
    if (!qrData.value.trim()) {
      setToast(attToast, "QR code wajib di-scan.", false);
      return;
    }
  }

  const formData = new FormData();
  appendCsrf(formData);
  formData.append("method", method);
  formData.append("lat", lat);
  formData.append("lng", lon);
  if (method === "gps_selfie") {
    formData.append("selfie", selfieFile.files[0]);
  }
  if (method === "qr") {
    formData.append("qr_data", qrData.value.trim());
  }
  // Tambah class loading sebelum submit
  btnCheckin.classList.add("is-loading");
  
  const result = await safeFetch("/api/attendance/checkin", {
    method: "POST",
    body: formData,
  });
  
  setToast(attToast, result.message || "Selesai.", result.ok);
  
  // Jika checkin berhasil
  if (result.ok) {
    // Ubah warna button ke success state
    btnCheckin.classList.add("is-success");
    btnCheckin.classList.remove("is-loading");
    
    // Ubah text button
    const btnLabel = btnCheckin.querySelector(".btn-label");
    if (btnLabel) {
      btnLabel.textContent = "✓ Sudah Masuk";
    }
    
    // Disable button checkin
    btnCheckin.disabled = true;
    
    // Update status badge
    const presenceStatus = document.getElementById("presenceStatusTitle");
    if (presenceStatus) {
      presenceStatus.textContent = "✓ Checkin Berhasil";
      presenceStatus.classList.remove("is-ready");
      presenceStatus.classList.add("is-done");
    }
    
    // Update KPI Card dengan jam checkin
    if (kpiMasukValue || kpiMasukMeta) {
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
  } else {
    // Jika gagal, hilangkan loading state
    btnCheckin.classList.remove("is-loading");
  }
});

btnLeave?.addEventListener("click", async () => {
  if (!leaveType || !leaveFrom || !leaveTo || !leaveReason || !leaveToast) return;
  const file = leaveAttachment?.files?.[0];
  if (file) {
    const maxSize = 2 * 1024 * 1024;
    if (file.size > maxSize) {
      setToast(leaveToast, "Lampiran maksimal 2MB.", false);
      return;
    }
  }
  const fromIso = toIsoDate(leaveFrom.value);
  const toIso = toIsoDate(leaveTo.value);
  const formData = new FormData();
  appendCsrf(formData);
  formData.append("type", leaveType.value);
  formData.append("date_from", fromIso);
  formData.append("date_to", toIso);
  formData.append("reason", leaveReason.value.trim());
  if (file) {
    formData.append("attachment", file);
  }
  const result = await safeFetch("/api/leave/request", {
    method: "POST",
    body: formData,
  });
  setToast(leaveToast, result.message || "Selesai.", result.ok);
  if (result.ok) {
    leaveReason.value = "";
    leaveAttachment.value = "";
    loadLeaveHistory();
  }
});

async function loadLeaveHistory(){
  if (!leaveHistory) return;
  const result = await safeFetch("/api/leave/my");
  if (!result.ok) {
    leaveHistory.innerHTML = '<tr><td colspan="5" class="muted">Gagal memuat data.</td></tr>';
    return;
  }
  const rows = result.data?.data || [];
  if (!rows.length) {
    leaveHistory.innerHTML = '<tr><td colspan="5" class="muted">Belum ada pengajuan.</td></tr>';
    return;
  }
  leaveHistory.innerHTML = rows.map((r) => {
    const range = `${r.date_from} s/d ${r.date_to}`;
    const note = r.note || "-";
    return `<tr>
      <td>${r.id}</td>
      <td>${r.type}</td>
      <td>${range}</td>
      <td><span class="badge">${r.status}</span></td>
      <td>${note}</td>
    </tr>`;
  }).join("");
}

loadLeaveHistory();

/**
 * Restore attendance state dari server setelah login
 * Fitur: Jika user sudah checkin, state tetap persisted meskipun logout
 */
async function restoreAttendanceState(){
  try {
    const response = await fetch("/api/attendance/today");
    if (!response.ok) return;
    
    const data = await response.json();
    const records = (data && data.data) || [];
    if (records.length === 0) return;
    
    // Sort by created_at ascending untuk proper sequence check
    records.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    
    // Cek sequence: checkin diikuti checkout atau belum
    let hasCheckinToday = false;
    let lastCheckinTime = null;
    let hasCheckoutToday = false;
    let checkinFound = false;
    
    for (const record of records) {
      if (record.action === "checkin") {
        hasCheckinToday = true;
        checkinFound = true;
        lastCheckinTime = record.time;
        hasCheckoutToday = false; // Reset checkout flag untuk checkin baru
      }
      if (record.action === "checkout" && checkinFound) {
        // Checkout hanya valid jika sebelumnya ada checkin
        hasCheckoutToday = true;
      }
    }
    
    // Restore button state jika sudah checkin
    if (hasCheckinToday && !hasCheckoutToday) {
      // User sudah checkin, button masuk harus disabled + success state
      if (btnCheckin) {
        btnCheckin.classList.add("is-success");
        btnCheckin.disabled = true;
        const btnLabel = btnCheckin.querySelector(".btn-label");
        if (btnLabel) {
          btnLabel.textContent = "✓ Sudah Masuk";
        }
      }
      
      // Update status badge
      const presenceStatus = document.getElementById("presenceStatusTitle");
      if (presenceStatus) {
        presenceStatus.textContent = "Siap Absen Pulang";
        presenceStatus.classList.remove("is-ready");
        presenceStatus.classList.add("is-done");
      }
      
      // Update KPI card dengan waktu checkin
      if (lastCheckinTime && (kpiMasukValue || kpiMasukMeta)) {
        if (kpiMasukValue) {
          kpiMasukValue.textContent = lastCheckinTime;
        }
        if (kpiMasukMeta) {
          kpiMasukMeta.textContent = `Status: ✓ Sudah Checkin (${lastCheckinTime})`;
        }
        
        const kpiCard = document.querySelector('[data-card="masuk"]');
        if (kpiCard) {
          kpiCard.classList.add("is-success");
        }
      }
    }
  } catch (err) {
    console.warn("[RESTORE STATE] Error loading attendance:", err);
  }
}

// Load persistent state saat page load
restoreAttendanceState();
