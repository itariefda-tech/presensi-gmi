const openBtn = document.getElementById("btnOpenChangePassword");
const closeBtn = document.getElementById("btnCloseChangePassword");
const modal = document.getElementById("changePasswordModal");
const form = document.getElementById("changePasswordForm");
const alertBox = document.getElementById("changePasswordAlert");
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

function setModalOpen(isOpen){
  if (!modal) return;
  modal.setAttribute("aria-hidden", isOpen ? "false" : "true");
  modal.classList.toggle("show", isOpen);
}

function showAlert(type, message){
  if (!alertBox) return;
  alertBox.textContent = message;
  alertBox.classList.remove("error", "success", "info");
  alertBox.classList.add(type);
  alertBox.style.display = "block";
}

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

openBtn?.addEventListener("click", () => {
  if (alertBox) {
    alertBox.style.display = "none";
  }
  setModalOpen(true);
});

closeBtn?.addEventListener("click", () => setModalOpen(false));

modal?.addEventListener("click", (e) => {
  if (e.target === modal) setModalOpen(false);
});

form?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(form);
  const payload = {
    current_password: formData.get("current_password") || "",
    new_password: formData.get("new_password") || "",
    new_password2: formData.get("new_password2") || "",
  };
  const result = await safeFetch("/api/auth/change_password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  showAlert(result.ok ? "success" : "error", result.message || "Selesai.");
  if (result.ok) {
    form.reset();
    window.setTimeout(() => setModalOpen(false), 900);
  }
});
