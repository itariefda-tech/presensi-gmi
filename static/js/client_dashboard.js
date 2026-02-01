(function(){
  const swipeTrack = document.getElementById("swipeTrack");
  const swipeViewport = document.querySelector(".swipe-viewport");
  const navButtons = Array.from(document.querySelectorAll(".nav-btn"));
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  let swipeIndex = 0;

  function scrollToTop(){
    const root = document.scrollingElement || document.documentElement;
    if (root) {
      root.scrollTop = 0;
    }
    if (window.scrollTo) {
      window.scrollTo(0, 0);
    }
  }

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
    scrollToTop();
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

  function initHeaderClock(){
    const hourEl = document.getElementById("headerClockHour");
    const minuteEl = document.getElementById("headerClockMinute");
    if (!hourEl || !minuteEl) return;
    const pad = (value) => value.toString().padStart(2, "0");
    const update = () => {
      const now = new Date();
      hourEl.textContent = pad(now.getHours());
      minuteEl.textContent = pad(now.getMinutes());
    };
    update();
    setInterval(update, 1000);
  }

  function initHeaderDate(){
    const dateWrapper = document.querySelector(".brand-date");
    const dateValue = document.getElementById("headerDateValue");
    if (!dateWrapper || !dateValue) return;
    const raw = (dateWrapper.dataset.rawDate || "").trim();
    const parts = raw.split("-");
    if (parts.length !== 3) {
      dateValue.textContent = raw;
      return;
    }
    const day = String(Number(parts[0]));
    const monthIndex = Number(parts[1]) - 1;
    const months = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
    const month = months[monthIndex] || parts[1];
    const year = parts[2].slice(-2);
    dateValue.textContent = `${day} ${month}'${year}`;
  }

  function initDatePickers(){
    const formatDateValue = (value, mode) => {
      if (!value) return "";
      const dateValue = mode === "month" ? `${value}-01` : value;
      const date = new Date(dateValue);
      if (Number.isNaN(date)) return value;
      const day = String(date.getDate()).padStart(2, "0");
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const year = date.getFullYear();
      if (mode === "month") {
        return `${month}-${year}`;
      }
      return `${day}-${month}-${year}`;
    };

    const activatePicker = (input) => {
      const mode = input.dataset.dateMode;
      if (!mode) return;
      const targetType = mode === "month" ? "month" : "date";
      input.type = targetType;
      if (typeof input.showPicker === "function") {
        input.showPicker();
      }
      const handleBlur = () => {
        input.type = "text";
        if (input.value) {
          input.value = formatDateValue(input.value, mode);
        }
        input.removeEventListener("blur", handleBlur);
      };
      input.addEventListener("blur", handleBlur);
    };

    document.querySelectorAll(".date-icon").forEach((icon) => {
      icon.addEventListener("click", (event) => {
        event.preventDefault();
        const input = icon.parentElement.querySelector("input");
        if (!input) return;
        activatePicker(input);
      });
    });

    document.querySelectorAll(".date-input input[data-date-mode]").forEach((input) => {
      input.addEventListener("focus", () => {
        activatePicker(input);
      });
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

  function initEmployeeAssignmentForm(){
    const form = document.getElementById("employee-create-form");
    if (!form) return;
    const shiftToggle = document.getElementById("assignment-shift-toggle");
    const shiftSelect = document.getElementById("assignment-shift");
    const statusToggle = document.getElementById("assignment-status-toggle");
    const statusInput = document.getElementById("assignment-status");
    const statusLabel = document.getElementById("assignment-status-label");
    const toIsoDate = (value) => {
      const raw = (value || "").trim();
      if (!raw) return "";
      const match = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
      if (match) {
        return `${match[3]}-${match[2]}-${match[1]}`;
      }
      return raw;
    };
    const syncShift = () => {
      if (!shiftToggle || !shiftSelect) return;
      const enabled = shiftToggle.checked;
      shiftSelect.disabled = !enabled;
      if (!enabled) shiftSelect.value = "";
    };
    const syncStatus = () => {
      if (!statusToggle || !statusInput) return;
      const value = statusToggle.checked ? "ENDED" : "ACTIVE";
      statusInput.value = value;
      if (statusLabel) statusLabel.textContent = value;
    };
    syncShift();
    syncStatus();
    if (shiftToggle) shiftToggle.addEventListener("change", syncShift);
    if (statusToggle) statusToggle.addEventListener("change", syncStatus);
    form.addEventListener("submit", () => {
      const startInput = form.querySelector('input[name="start_date"]');
      const endInput = form.querySelector('input[name="end_date"]');
      if (startInput) startInput.value = toIsoDate(startInput.value);
      if (endInput) endInput.value = toIsoDate(endInput.value);
      syncShift();
      syncStatus();
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

  function initCollapsiblePanels(){
    const toggles = document.querySelectorAll("[data-collapse-toggle]");
    toggles.forEach((btn) => {
      const targetId = btn.getAttribute("data-collapse-toggle");
      const panel = targetId ? document.getElementById(targetId) : null;
      const bodyId = btn.getAttribute("aria-controls");
      const body = bodyId ? document.getElementById(bodyId) : null;
      if (!panel) return;
      const setState = (open) => {
        panel.classList.toggle("is-open", open);
        panel.classList.toggle("is-collapsed", !open);
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        if (body) body.setAttribute("aria-hidden", open ? "false" : "true");
      };
      setState(panel.classList.contains("is-open"));
      btn.addEventListener("click", () => {
        setState(!panel.classList.contains("is-open"));
      });
    });
  }

  function initEmployeeTablePagination(){
    const table = document.getElementById("employee-table");
    const pager = document.getElementById("employee-pagination");
    if (!table || !pager) return;
    const pageSize = parseInt(table.dataset.pageSize || "6", 10);
    const tbody = table.querySelector("tbody");
    if (!tbody) return;
    const allRows = Array.from(tbody.querySelectorAll("tr")).filter((row) => !row.classList.contains("empty-row"));
    if (allRows.length <= pageSize) {
      pager.style.display = "none";
      return;
    }
    let page = 1;
    const totalPages = Math.max(1, Math.ceil(allRows.length / pageSize));
    const info = pager.querySelector("[data-page-info]");
    const prevBtn = pager.querySelector("[data-page='prev']");
    const nextBtn = pager.querySelector("[data-page='next']");
    const render = () => {
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      allRows.forEach((row, idx) => {
        row.style.display = idx >= start && idx < end ? "" : "none";
      });
      if (info) info.textContent = `Page ${page} of ${totalPages}`;
      if (prevBtn) prevBtn.disabled = page <= 1;
      if (nextBtn) nextBtn.disabled = page >= totalPages;
    };
    if (prevBtn) prevBtn.addEventListener("click", () => {
      if (page > 1) {
        page -= 1;
        render();
      }
    });
    if (nextBtn) nextBtn.addEventListener("click", () => {
      if (page < totalPages) {
        page += 1;
        render();
      }
    });
    render();
  }

  function initAttendanceTablePagination(){
    const table = document.getElementById("attendance-table");
    const pager = document.getElementById("attendance-pagination");
    if (!table || !pager) return;
    const pageSize = parseInt(table.dataset.pageSize || "6", 10);
    const tbody = table.querySelector("tbody");
    if (!tbody) return;
    const allRows = Array.from(tbody.querySelectorAll("tr")).filter((row) => !row.classList.contains("empty-row"));
    if (allRows.length <= pageSize) {
      pager.style.display = "none";
      return;
    }
    let page = 1;
    const totalPages = Math.max(1, Math.ceil(allRows.length / pageSize));
    const info = pager.querySelector("[data-page-info]");
    const prevBtn = pager.querySelector("[data-page='prev']");
    const nextBtn = pager.querySelector("[data-page='next']");
    const render = () => {
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      allRows.forEach((row, idx) => {
        row.style.display = idx >= start && idx < end ? "" : "none";
      });
      if (info) info.textContent = `Page ${page} of ${totalPages}`;
      if (prevBtn) prevBtn.disabled = page <= 1;
      if (nextBtn) nextBtn.disabled = page >= totalPages;
    };
    if (prevBtn) prevBtn.addEventListener("click", () => {
      if (page > 1) {
        page -= 1;
        render();
      }
    });
    if (nextBtn) nextBtn.addEventListener("click", () => {
      if (page < totalPages) {
        page += 1;
        render();
      }
    });
    render();
  }

  function initAttendanceReportToggle(){
    const panel = document.getElementById("attendance-report");
    if (!panel) return;
    const radios = panel.querySelectorAll("input[name='mode']");
    const rangeFields = panel.querySelectorAll("[data-attendance-field='range']");
    const monthFields = panel.querySelectorAll("[data-attendance-field='month']");
    const exportGrid = panel.querySelector(".attendance-export-grid");
    const exportActions = panel.querySelector(".export-actions");
    const monthRow = panel.querySelector(".attendance-month-row");
    const setVisible = (nodes, visible) => {
      nodes.forEach((node) => {
        node.style.display = visible ? "" : "none";
        const input = node.querySelector("input");
        if (input) input.disabled = !visible;
      });
    };
    const applyMode = () => {
      const selected = panel.querySelector("input[name='mode']:checked")?.value || "all";
      if (selected === "range") {
        setVisible(rangeFields, true);
        setVisible(monthFields, false);
        moveExportButton("range");
        exportGrid?.classList.add("is-range");
        exportGrid?.classList.remove("is-month");
      } else if (selected === "month") {
        setVisible(rangeFields, false);
        setVisible(monthFields, true);
        moveExportButton("month");
        exportGrid?.classList.remove("is-range");
        exportGrid?.classList.add("is-month");
      } else {
        setVisible(rangeFields, false);
        setVisible(monthFields, false);
        moveExportButton("range");
        exportGrid?.classList.remove("is-range", "is-month");
      }
    };
    const moveExportButton = (mode) => {
      if (!exportActions || !exportGrid) return;
      if (mode === "month" && monthRow) {
        monthRow.appendChild(exportActions);
      } else {
        const monthField = exportGrid.querySelector(".attendance-month-row");
        if (monthField) {
          exportGrid.insertBefore(exportActions, monthField);
        }
      }
    };
    radios.forEach((radio) => {
      radio.addEventListener("change", applyMode);
    });
    applyMode();
  }

  function initAttendanceRangeReport(){
    const form = document.getElementById("attendance-range-form");
    const table = document.getElementById("attendance-range-table");
    const pager = document.getElementById("attendance-range-pagination");
    const messageEl = document.getElementById("attendance-range-message");
    if (!form || !table || !pager) return;
    const tbody = table.querySelector("tbody");
    if (!tbody) return;
    const info = pager.querySelector("[data-page-info]");
    const prevBtn = pager.querySelector("[data-page='prev']");
    const nextBtn = pager.querySelector("[data-page='next']");
    const pageSize = parseInt(table.dataset.pageSize || "6", 10) || 6;
    const submitBtn = form.querySelector("button[type='submit']");
    let currentRows = [];
    let currentPage = 1;

    const flashMessage = (text, type) => {
      if (!messageEl) return;
      messageEl.textContent = text || "";
      messageEl.classList.toggle("is-error", type === "error");
    };

    const prunePager = () => {
      const totalPages = currentRows.length ? Math.ceil(currentRows.length / pageSize) : 0;
      if (totalPages && currentPage > totalPages) {
        currentPage = totalPages;
      }
      const hasData = currentRows.length > 0;
      pager.style.display = hasData ? "flex" : "none";
      if (info) {
        info.textContent = hasData ? `Page ${currentPage} of ${totalPages}` : "Page 0 of 0";
      }
      if (prevBtn) prevBtn.disabled = !hasData || currentPage <= 1;
      if (nextBtn) nextBtn.disabled = !hasData || currentPage >= totalPages;
    };

    const renderRow = (row) => {
      const tr = document.createElement("tr");
      const actionLower = (row.action || "").toLowerCase();
      const isCheckout = actionLower.includes("out");
      const checkInValue = isCheckout ? "-" : row.time || "-";
      const checkOutValue = isCheckout ? row.time || "-" : "-";
      const cells = [
        row.employee || "-",
        row.date || "-",
        checkInValue,
        checkOutValue,
        row.method || "-",
      ];
      cells.forEach((value) => {
        const td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      });
      return tr;
    };

    const renderTable = () => {
      tbody.innerHTML = "";
      if (!currentRows.length) {
        const emptyRow = document.createElement("tr");
        emptyRow.innerHTML = "<td colspan='5' class='empty-row'>Tidak ada data pada rentang ini.</td>";
        tbody.appendChild(emptyRow);
      } else {
        const start = (currentPage - 1) * pageSize;
        const slice = currentRows.slice(start, start + pageSize);
        slice.forEach((row) => {
          tbody.appendChild(renderRow(row));
        });
      }
      prunePager();
    };

    const setLoading = (isLoading) => {
      if (submitBtn) submitBtn.disabled = isLoading;
    };

    const updateRows = (rows) => {
      currentRows = Array.isArray(rows) ? rows : [];
      currentPage = 1;
      renderTable();
    };

    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        if (currentPage > 1) {
          currentPage -= 1;
          renderTable();
        }
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        const totalPages = currentRows.length ? Math.ceil(currentRows.length / pageSize) : 0;
        if (currentPage < totalPages) {
          currentPage += 1;
          renderTable();
        }
      });
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const fromField = form.querySelector("[name='from']");
      const toField = form.querySelector("[name='to']");
      const fromValue = (fromField?.value || "").trim();
      const toValue = (toField?.value || "").trim();
      if (!fromValue || !toValue) {
        flashMessage("Rentang tanggal wajib diisi.", "error");
        updateRows([]);
        return;
      }
      setLoading(true);
      flashMessage("Memuat data...");
      try {
        const params = new URLSearchParams({ from: fromValue, to: toValue });
        const response = await fetch(`/client/attendance/records?${params.toString()}`, {
          headers: { Accept: "application/json" },
        });
        const payload = await response.json().catch(() => null);
        if (!response.ok || !payload?.ok) {
          throw new Error(payload?.message || "Gagal memuat data attendance.");
        }
        const records = Array.isArray(payload.data) ? payload.data : [];
        const count = typeof payload?.total === "number" ? payload.total : records.length;
        flashMessage(count ? `Menampilkan ${count} baris.` : "Tidak ada data untuk rentang ini.");
        updateRows(records);
      } catch (err) {
        flashMessage(err.message || "Gagal memuat data attendance.", "error");
        updateRows([]);
      } finally {
        setLoading(false);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initSwipe();
    initGps();
    initSiteLocationPicker();
    initHeaderClock();
    initHeaderDate();
    initDatePickers();
    initChangePassword();
    initEmployeeAssignmentForm();
    initModals();
    initCollapsiblePanels();
    initEmployeeTablePagination();
    initAttendanceTablePagination();
    initAttendanceReportToggle();
    initAttendanceRangeReport();
    go(0);
  });
})();
