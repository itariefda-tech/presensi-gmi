const clientSelect = document.getElementById("qrClientSelect");
const siteSelect = document.getElementById("qrSiteSelect");
const statusEl = document.getElementById("qrStatus");
const expiryEl = document.getElementById("qrExpiry");
const remainingEl = document.getElementById("qrRemaining");
const qrImage = document.getElementById("qrCanvas");
const copyBtn = document.getElementById("btnCopyQr");
const refreshBtn = document.getElementById("btnRefreshQr");
const actionButtons = Array.from(document.querySelectorAll("[data-qr-action]"));

let payloads = { IN: "", OUT: "" };
let payloadImages = { IN: "", OUT: "" };
let activeAction = "IN";
let windowEnd = 0;
let serverOffset = 0;
let tickTimer = null;
let isFetching = false;

function setStatus(message, isError = false){
  if (!statusEl) return;
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#fb7185" : "";
}

function clearQr(message, isError = true){
  payloads = { IN: "", OUT: "" };
  payloadImages = { IN: "", OUT: "" };
  windowEnd = 0;
  if (qrImage) qrImage.removeAttribute("src");
  if (expiryEl) expiryEl.textContent = "-";
  if (remainingEl) remainingEl.textContent = "-";
  setStatus(message, isError);
}

function setOptionVisibility(option, visible){
  option.hidden = !visible;
  option.disabled = !visible;
}

function updateSiteOptions(resetSite = false){
  if (!siteSelect) return;
  const clientId = clientSelect?.value || "";
  Array.from(siteSelect.options).forEach((option) => {
    if (!option.value) {
      setOptionVisibility(option, true);
      return;
    }
    setOptionVisibility(option, !clientId || option.dataset.clientId === clientId);
  });
  const selectedOption = siteSelect.selectedOptions[0];
  if (resetSite || (selectedOption && selectedOption.disabled)) {
    siteSelect.value = "";
  }
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
  const imageData = payloadImages[activeAction];
  if (!qrImage) return;
  if (!imageData) {
    qrImage.removeAttribute("src");
    setStatus("QR belum siap.", true);
    return;
  }
  qrImage.src = `data:image/png;base64,${imageData}`;
  setStatus("QR siap untuk dipindai.");
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
  if (!clientSelect || isFetching) return;
  const clientId = clientSelect.value;
  const siteId = siteSelect?.value || "";
  if (!clientId) {
    clearQr("Pilih client untuk membuat QR.");
    return;
  }
  if (!siteId) {
    clearQr("Pilih site untuk membuat QR.");
    return;
  }
  isFetching = true;
  if (refreshBtn) refreshBtn.disabled = true;
  setStatus("Memuat QR...");
  try {
    const params = new URLSearchParams({ client_id: clientId, site_id: siteId });
    const res = await fetch(`/dashboard/admin/qr/payload?${params.toString()}`);
    const data = await res.json();
    if (!res.ok || !data.ok) {
      setStatus(data?.message || "Gagal memuat QR.", true);
      return;
    }
    payloads = { IN: data.data.payload_in, OUT: data.data.payload_out };
    payloadImages = { IN: data.data.image_in, OUT: data.data.image_out };
    windowEnd = data.data.window_end;
    serverOffset = data.data.server_ts - Math.floor(Date.now() / 1000);
    if (expiryEl) {
      expiryEl.textContent = formatLocal(windowEnd);
    }
    renderQr();
    updateCountdown();
  } catch (err) {
    setStatus("Gagal memuat QR.", true);
  } finally {
    isFetching = false;
    if (refreshBtn) refreshBtn.disabled = false;
  }
}

actionButtons.forEach((btn) => {
  btn.addEventListener("click", () => setActiveAction(btn.dataset.qrAction));
});

clientSelect?.addEventListener("change", () => {
  updateSiteOptions(true);
  clearQr("Pilih site untuk membuat QR.");
});

siteSelect?.addEventListener("change", () => {
  fetchPayload();
});

refreshBtn?.addEventListener("click", () => {
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
  updateSiteOptions(false);
  fetchPayload();
}
