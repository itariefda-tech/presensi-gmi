const clientSelect = document.getElementById("qrClientSelect");
const statusEl = document.getElementById("qrStatus");
const expiryEl = document.getElementById("qrExpiry");
const remainingEl = document.getElementById("qrRemaining");
const canvas = document.getElementById("qrCanvas");
const copyBtn = document.getElementById("btnCopyQr");
const actionButtons = Array.from(document.querySelectorAll("[data-qr-action]"));

let payloads = { IN: "", OUT: "" };
let activeAction = "IN";
let windowEnd = 0;
let serverOffset = 0;
let tickTimer = null;
let qrLibPromise = null;

function ensureQrLib(){
  if (window.QRCode) return Promise.resolve(true);
  if (qrLibPromise) return qrLibPromise;
  const sources = [
    "/static/js/vendor/qrcode.min.js",
    "https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js",
    "https://unpkg.com/qrcode@1.5.3/build/qrcode.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/qrcode/1.5.3/qrcode.min.js",
  ];
  qrLibPromise = new Promise((resolve) => {
    const tryNext = (idx) => {
      if (window.QRCode) {
        resolve(true);
        return;
      }
      if (idx >= sources.length) {
        resolve(false);
        return;
      }
      const src = sources[idx];
      const script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.onload = () => resolve(!!window.QRCode);
      script.onerror = () => tryNext(idx + 1);
      document.head.appendChild(script);
    };
    tryNext(0);
  });
  return qrLibPromise;
}

function setStatus(message, isError = false){
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#fb7185" : "";
}

function setActiveAction(action){
  activeAction = action;
  actionButtons.forEach((btn) => {
    const isActive = btn.dataset.qrAction === action;
    btn.classList.toggle("active", isActive);
    btn.setAttribute("aria-pressed", String(isActive));
  });
  renderQr();
}

function renderQr(){
  if (!canvas) return;
  const payload = payloads[activeAction] || "";
  if (!payload) {
    setStatus("QR belum siap.", true);
    return;
  }
  if (!window.QRCode) {
    setStatus("Library QR belum tersedia. Coba muat ulang halaman.", true);
    return;
  }
  QRCode.toCanvas(
    canvas,
    payload,
    { width: 260, margin: 1 },
    (err) => {
      if (err) {
        setStatus("Gagal membuat QR.", true);
      } else {
        setStatus("QR siap untuk dipindai.");
      }
    }
  );
}

function formatLocal(ts){
  const date = new Date(ts * 1000);
  return date.toLocaleString("id-ID");
}

function updateCountdown(){
  if (!windowEnd || !remainingEl) return;
  const now = Math.floor(Date.now() / 1000) + serverOffset;
  const remaining = Math.max(0, windowEnd - now);
  const hours = Math.floor(remaining / 3600);
  const minutes = Math.floor((remaining % 3600) / 60);
  remainingEl.textContent = `Sisa ${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
  if (remaining <= 0) {
    fetchPayload();
  }
}

async function fetchPayload(){
  if (!clientSelect) return;
  const clientId = clientSelect.value;
  if (!clientId) {
    setStatus("Pilih client untuk membuat QR.", true);
    return;
  }
  setStatus("Memuat QR...");
  try {
    const res = await fetch(`/dashboard/admin/qr/payload?client_id=${encodeURIComponent(clientId)}`);
    const data = await res.json();
    if (!res.ok || !data.ok) {
      setStatus(data?.message || "Gagal memuat QR.", true);
      return;
    }
    payloads = { IN: data.data.payload_in, OUT: data.data.payload_out };
    windowEnd = data.data.window_end;
    serverOffset = data.data.server_ts - Math.floor(Date.now() / 1000);
    if (expiryEl) {
      expiryEl.textContent = formatLocal(windowEnd);
    }
    const libReady = await ensureQrLib();
    if (!libReady) {
      setStatus("Library QR belum tersedia. Periksa koneksi internet.", true);
      return;
    }
    renderQr();
    updateCountdown();
  } catch (err) {
    setStatus("Gagal memuat QR.", true);
  }
}

actionButtons.forEach((btn) => {
  btn.addEventListener("click", () => setActiveAction(btn.dataset.qrAction));
});

clientSelect?.addEventListener("change", () => {
  fetchPayload();
});

copyBtn?.addEventListener("click", async () => {
  const payload = payloads[activeAction] || "";
  if (!payload) {
    setStatus("QR belum siap.", true);
    return;
  }
  try {
    await navigator.clipboard.writeText(payload);
    setStatus("Kode QR disalin.");
  } catch (err) {
    setStatus("Gagal menyalin kode.", true);
  }
});

if (tickTimer) clearInterval(tickTimer);
tickTimer = window.setInterval(updateCountdown, 1000 * 30);

if (clientSelect) {
  fetchPayload();
}
