const avatarInput = document.getElementById("avatarInput");
const avatarEl = document.getElementById("userAvatar");
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
const defaultAvatarUrl = "/static/img/gmi_logo.gif";

function normalizeAvatarPath(path){
  return String(path || "").replace(/^url\((['"]?)(.*?)\1\)$/i, "$2").trim();
}

function setAvatarBackground(path){
  if (!avatarEl || !path) return;
  avatarEl.style.backgroundImage = `url('${path}')`;
}

function ensureAvatarBackground(){
  if (!avatarEl) return;
  const rawImage = normalizeAvatarPath(avatarEl.style.backgroundImage);
  const image = new Image();
  image.onerror = () => setAvatarBackground(defaultAvatarUrl);
  image.src = rawImage || defaultAvatarUrl;
}

async function uploadProfilePhoto(file){
  const formData = new FormData();
  if (csrfToken) {
    formData.append("csrf_token", csrfToken);
  }
  formData.append("avatar", file);
  const res = await fetch("/api/user/profile_photo", {
    method: "POST",
    body: formData,
  });
  let data = null;
  try {
    data = await res.json();
  } catch (err) {
    data = null;
  }
  if (!res.ok || !data?.ok) {
    const msg = data?.message || "Upload gagal.";
    throw new Error(msg);
  }
  return data;
}

avatarInput?.addEventListener("change", async (e) => {
  const file = e.target?.files?.[0];
  if (!file) return;
  avatarEl?.classList.add("is-uploading");
  try {
    const result = await uploadProfilePhoto(file);
    if (avatarEl && result?.path) {
      setAvatarBackground(result.path);
    }
  } catch (err) {
    window.alert(err.message || "Upload gagal.");
  } finally {
    avatarEl?.classList.remove("is-uploading");
    avatarInput.value = "";
  }
});

ensureAvatarBackground();
