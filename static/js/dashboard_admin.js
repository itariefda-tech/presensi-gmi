const tabButtons = Array.from(document.querySelectorAll(".tab-btn"));
const tabPanels = Array.from(document.querySelectorAll(".tab-panel"));
const leaveRows = document.getElementById("leaveRows");
const canApproveLeave = leaveRows?.dataset?.canApproveLeave === "1";
const pendingLimit = Number(leaveRows?.dataset?.limit || 0) || 0;
const approvalAlert = document.getElementById("approvalAlert");
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

function setActiveTab(name){
  tabButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === name));
  tabPanels.forEach((panel) => panel.classList.toggle("active", panel.id === `tab-${name}`));
}

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => setActiveTab(btn.dataset.tab));
});

async function safeFetch(url, options = {}){
  let res = null;
  try {
    if (csrfToken) {
      options.headers = options.headers || {};
      options.headers["X-CSRF-Token"] = csrfToken;
    }
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

function showToast(type, message, opts = {}){
  if (!approvalAlert) return;
  approvalAlert.textContent = message;
  approvalAlert.classList.remove("error", "success", "info");
  approvalAlert.classList.add(type);
  approvalAlert.style.display = "block";
  if (!opts.persist) {
    window.setTimeout(() => {
      approvalAlert.style.display = "none";
    }, opts.timeoutMs || 3200);
  }
}

function renderLeave(rows){
  if (!rows.length) {
    const colspan = canApproveLeave ? 7 : 6;
    leaveRows.innerHTML = `<tr><td colspan="${colspan}" class="muted">Tidak ada pending.</td></tr>`;
    return;
  }
  leaveRows.innerHTML = rows.map((r) => {
    const range = `${r.date_from} s/d ${r.date_to}`;
    const reason = r.reason || "-";
    const shortReason = reason.length > 60 ? `${reason.slice(0, 57)}...` : reason;
    return `<tr>
      <td>${r.created_at || "-"}</td>
      <td>${r.employee_email}</td>
      <td><span class="badge">${r.type}</span></td>
      <td>${range}</td>
      <td>${shortReason}</td>
      <td><span class="badge pending">pending</span></td>
      ${canApproveLeave ? `<td>
        <div class="inline approval-actions">
          <button class="btn primary" data-approve-leave="${r.id}">Approve</button>
          <button class="btn secondary" data-reject-leave="${r.id}">Reject</button>
        </div>
      </td>` : ""}
    </tr>`;
  }).join("");
  if (!canApproveLeave) return;
  leaveRows.querySelectorAll("[data-approve-leave]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const note = window.prompt("Catatan approval (opsional):", "") || "";
      const result = await safeFetch("/api/leave/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: btn.dataset.approveLeave, action: "approve", note }),
      });
      showToast(result.ok ? "success" : "error", result.message || "Selesai.");
      if (result.ok) loadApprovals();
    });
  });
  leaveRows.querySelectorAll("[data-reject-leave]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const note = window.prompt("Alasan penolakan (wajib):", "") || "";
      if (!note.trim()) {
        showToast("error", "Alasan penolakan wajib diisi.");
        return;
      }
      const result = await safeFetch("/api/leave/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: btn.dataset.rejectLeave, action: "reject", note }),
      });
      showToast(result.ok ? "success" : "error", result.message || "Selesai.");
      if (result.ok) loadApprovals();
    });
  });
}

async function loadApprovals(){
  if (!leaveRows) return;
  const limitQuery = pendingLimit > 0 ? `?limit=${pendingLimit}` : "";
  const result = await safeFetch(`/api/leave/pending${limitQuery}`);
  if (!result.ok) {
    showToast("error", result.message || "Gagal memuat data.");
    const colspan = canApproveLeave ? 7 : 6;
    leaveRows.innerHTML = `<tr><td colspan="${colspan}" class="muted">Gagal memuat data.</td></tr>`;
    return;
  }
  renderLeave(result.data?.data || []);
  if (pendingLimit > 0 && result.data?.data?.length >= pendingLimit) {
    showToast("info", `Menampilkan terbaru ${pendingLimit} pengajuan.`);
  }
}

if (leaveRows) {
  loadApprovals();
}
