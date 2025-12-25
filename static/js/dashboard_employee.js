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
  formData.append("method", method);
  formData.append("lat", lat);
  formData.append("lng", lon);
  if (method === "gps_selfie") {
    formData.append("selfie", selfieFile.files[0]);
  }
  if (method === "qr") {
    formData.append("qr_data", qrData.value.trim());
  }
  const result = await safeFetch("/api/attendance/checkin", {
    method: "POST",
    body: formData,
  });
  setToast(attToast, result.message || "Selesai.", result.ok);
});

btnLeave?.addEventListener("click", async () => {
  if (!leaveType || !leaveFrom || !leaveTo || !leaveReason || !leaveToast) return;
  const payload = {
    type: leaveType.value,
    date_from: leaveFrom.value,
    date_to: leaveTo.value,
    reason: leaveReason.value.trim(),
    attachment: leaveAttachment.files?.[0]?.name || "",
  };
  const result = await safeFetch("/api/leave/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
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
