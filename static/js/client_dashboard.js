(function(){
  const swipeTrack = document.getElementById("swipeTrack");
  const swipeViewport = document.querySelector(".swipe-viewport");
  const navButtons = Array.from(document.querySelectorAll(".nav-btn"));
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  let swipeIndex = 0;

  function go(index){
    const max = 5;
    swipeIndex = Math.max(0, Math.min(max, index));
    if (swipeTrack) {
      swipeTrack.style.transform = `translateX(-${swipeIndex * 100}%)`;
    }
    navButtons.forEach((btn) => {
      const tab = parseInt(btn.dataset.tab || "", 10);
      if (Number.isNaN(tab)) return;
      btn.classList.toggle("active", tab === swipeIndex);
    });
  }

  navButtons.forEach((btn) => {
    if (!btn.dataset.tab) return;
    btn.addEventListener("click", () => {
      go(parseInt(btn.dataset.tab, 10));
    });
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

  function initGps(){
    const btn = document.getElementById("refreshGps");
    const coordsEl = document.getElementById("deviceCoords");
    const metaEl = document.getElementById("deviceMeta");
    if (!btn || !coordsEl || !metaEl) return;
    if (!navigator.geolocation) {
      metaEl.textContent = "GPS tidak tersedia.";
      return;
    }
    const setLoading = (isLoading) => {
      btn.disabled = isLoading;
      btn.classList.toggle("is-loading", isLoading);
    };
    btn.addEventListener("click", () => {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude, accuracy } = pos.coords;
          coordsEl.textContent = `${latitude.toFixed(6)} / ${longitude.toFixed(6)}`;
          const stamp = new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
          metaEl.textContent = `Akurasi ±${Math.round(accuracy)}m • ${stamp}`;
          setLoading(false);
        },
        (err) => {
          metaEl.textContent = err.message || "Gagal mengambil lokasi.";
          setLoading(false);
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
      );
    });
  }

  function initSiteLocationPicker(){
    const btn = document.getElementById("sitePickLocation");
    const latInput = document.getElementById("site-latitude");
    const lngInput = document.getElementById("site-longitude");
    if (!btn || !latInput || !lngInput) return;
    if (!navigator.geolocation) {
      btn.textContent = "GPS tidak tersedia";
      btn.disabled = true;
      return;
    }
    const setLoading = (isLoading) => {
      btn.disabled = isLoading;
      btn.classList.toggle("is-loading", isLoading);
      btn.textContent = isLoading ? "Mengambil lokasi..." : "Ambil lokasi sini";
    };
    btn.addEventListener("click", () => {
      setLoading(true);
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          latInput.value = latitude.toFixed(6);
          lngInput.value = longitude.toFixed(6);
          setLoading(false);
        },
        () => {
          setLoading(false);
          btn.textContent = "Gagal ambil lokasi";
          setTimeout(() => {
            if (!btn.disabled) btn.textContent = "Ambil lokasi sini";
          }, 1500);
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
      );
    });
  }

  function initChangePassword(){
    const form = document.getElementById("changePasswordForm");
    const messageEl = document.getElementById("changePasswordMessage");
    if (!form) return;
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const payload = {
        csrf_token: csrfToken,
        current_password: formData.get("current_password") || "",
        new_password: formData.get("new_password") || "",
        new_password2: formData.get("new_password2") || "",
      };
      const submitBtn = form.querySelector("button[type='submit']");
      if (submitBtn) submitBtn.disabled = true;
      if (messageEl) messageEl.textContent = "Memproses...";
      try {
        const res = await fetch("/api/auth/change_password", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
          },
          body: JSON.stringify(payload),
        });
        const data = await res.json().catch(() => null);
        if (!res.ok || !data?.ok) {
          throw new Error(data?.message || "Gagal memperbarui password.");
        }
        if (messageEl) messageEl.textContent = data.message || "Password diperbarui.";
        form.reset();
      } catch (err) {
        if (messageEl) messageEl.textContent = err.message || "Gagal memperbarui password.";
      } finally {
        if (submitBtn) submitBtn.disabled = false;
      }
    });
  }

  function initModals(){
    const openers = Array.from(document.querySelectorAll("[data-modal-open]"));
    const closers = Array.from(document.querySelectorAll("[data-modal-close]"));
    const toggle = (id, isOpen) => {
      const modal = document.getElementById(id);
      if (!modal) return;
      modal.classList.toggle("is-open", isOpen);
      modal.setAttribute("aria-hidden", isOpen ? "false" : "true");
      document.body.classList.toggle("modal-open", isOpen);
    };

    openers.forEach((btn) => {
      const id = btn.getAttribute("data-modal-open");
      if (!id) return;
      btn.addEventListener("click", () => toggle(id, true));
    });

    closers.forEach((btn) => {
      const id = btn.getAttribute("data-modal-close");
      if (!id) return;
      btn.addEventListener("click", () => toggle(id, false));
    });

    document.addEventListener("keydown", (e) => {
      if (e.key !== "Escape") return;
      const modal = document.querySelector(".modal.is-open");
      if (modal) toggle(modal.id, false);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initSwipe();
    initGps();
    initSiteLocationPicker();
    initChangePassword();
    initModals();
    go(0);
  });
})();
