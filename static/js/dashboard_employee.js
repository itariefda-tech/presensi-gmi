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
  el.textContent = msg;
  el.style.color = ok ? "#22c55e" : "#fb7185";
}

btnLocation?.addEventListener("click", () => {
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
  const method = attMethod.value;
  const lat = latEl.value;
  const lon = lonEl.value;
  const payload = { method, lat, lon };

  if (!lat || !lon) {
    setToast(attToast, "Lokasi GPS wajib diisi.", false);
    return;
  }
  if (method === "gps_selfie") {
    if (!selfieData) {
      setToast(attToast, "Selfie wajib untuk GPS + selfie.", false);
      return;
    }
    payload.selfie = selfieData;
  }
  if (method === "qr") {
    if (!qrData.value.trim()) {
      setToast(attToast, "QR code wajib di-scan.", false);
      return;
    }
    payload.qr_data = qrData.value.trim();
  }

  const res = await fetch("/api/attendance/checkin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  setToast(attToast, data.message || "Selesai.", res.ok);
});

btnLeave?.addEventListener("click", async () => {
  const payload = {
    type: leaveType.value,
    date_from: leaveFrom.value,
    date_to: leaveTo.value,
    reason: leaveReason.value.trim(),
    attachment: leaveAttachment.files?.[0]?.name || "",
  };
  const res = await fetch("/api/leave/request", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  setToast(leaveToast, data.message || "Selesai.", res.ok);
  if (res.ok) {
    leaveReason.value = "";
    leaveAttachment.value = "";
    loadLeaveHistory();
  }
});

async function loadLeaveHistory(){
  const res = await fetch("/api/leave/my");
  const data = await res.json();
  const rows = data.data || [];
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
