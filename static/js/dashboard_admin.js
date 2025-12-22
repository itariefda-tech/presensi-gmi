const tabButtons = Array.from(document.querySelectorAll(".tab-btn"));
const tabPanels = Array.from(document.querySelectorAll(".tab-panel"));
const leaveRows = document.getElementById("leaveRows");
const approvalAlert = document.getElementById("approvalAlert");

function setActiveTab(name){
  tabButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.tab === name));
  tabPanels.forEach((panel) => panel.classList.toggle("active", panel.id === `tab-${name}`));
}

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => setActiveTab(btn.dataset.tab));
});

async function fetchJSON(url){
  const res = await fetch(url);
  return res.json();
}

function showAlert(type, message){
  if (!approvalAlert) return;
  approvalAlert.textContent = message;
  approvalAlert.classList.remove("error", "success", "info");
  approvalAlert.classList.add(type);
  approvalAlert.style.display = "block";
  window.setTimeout(() => {
    approvalAlert.style.display = "none";
  }, 2400);
}

function renderLeave(rows){
  if (!rows.length) {
    leaveRows.innerHTML = '<tr><td colspan="7" class="muted">Tidak ada pending.</td></tr>';
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
      <td>
        <div class="inline">
          <button class="btn primary" data-approve-leave="${r.id}">Approve</button>
          <button class="btn secondary" data-reject-leave="${r.id}">Reject</button>
        </div>
      </td>
    </tr>`;
  }).join("");
  leaveRows.querySelectorAll("[data-approve-leave]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const note = window.prompt("Catatan approval (opsional):", "") || "";
      const res = await fetch("/api/leave/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: btn.dataset.approveLeave, action: "approve", note }),
      });
      const data = await res.json();
      showAlert(res.ok ? "success" : "error", data.message || "Selesai.");
      if (res.ok) loadApprovals();
    });
  });
  leaveRows.querySelectorAll("[data-reject-leave]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const note = window.prompt("Alasan penolakan (wajib):", "") || "";
      if (!note.trim()) {
        showAlert("error", "Alasan penolakan wajib diisi.");
        return;
      }
      const res = await fetch("/api/leave/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: btn.dataset.rejectLeave, action: "reject", note }),
      });
      const data = await res.json();
      showAlert(res.ok ? "success" : "error", data.message || "Selesai.");
      if (res.ok) loadApprovals();
    });
  });
}

async function loadApprovals(){
  if (!leaveRows) return;
  const leave = await fetchJSON("/api/leave/pending");
  renderLeave(leave.data || []);
}

if (leaveRows) {
  loadApprovals();
}
