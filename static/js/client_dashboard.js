(function(){
  const swipeTrack = document.getElementById("swipeTrack");
  const swipeViewport = document.querySelector(".swipe-viewport");
  const navButtons = Array.from(document.querySelectorAll(".nav-btn"));
  const headerButtons = Array.from(document.querySelectorAll(".header-action-btn[data-tab]"));
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  let swipeIndex = 0;
  const tabStorageKey = "client_active_tab";
  const patrolState = {
    payload: null,
    pollingHandle: null,
    lastSyncAt: 0,
    dragCheckpointId: null,
    loading: false,
    initialized: false,
  };

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
    const max = 6;
    swipeIndex = Math.max(0, Math.min(max, index));
    if (swipeTrack) {
      swipeTrack.style.transform = `translateX(-${swipeIndex * 100}%)`;
    }
    navButtons.forEach((btn) => {
      const tab = parseInt(btn.dataset.tab || "", 10);
      if (Number.isNaN(tab)) return;
      btn.classList.toggle("active", tab === swipeIndex);
    });
    try {
      localStorage.setItem(tabStorageKey, String(swipeIndex));
    } catch (e) {}
    scrollToTop();
    patrolHandleTabChange();
  }

  navButtons.forEach((btn) => {
    if (!btn.dataset.tab) return;
    btn.addEventListener("click", () => {
      go(parseInt(btn.dataset.tab, 10));
    });
  });

  headerButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = parseInt(btn.dataset.tab || "", 10);
      if (!Number.isNaN(tab)) {
        go(tab);
      }
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

  function initAttendanceDate(){
    const dateWrapper = document.querySelector(".attendance-date");
    const dateValue = document.getElementById("attendanceDateValue");
    if (!dateWrapper || !dateValue) return;
    const raw = (dateWrapper.dataset.rawDate || "").trim();
    const parts = raw.split("-");
    if (parts.length !== 3) {
      dateValue.textContent = raw;
      return;
    }
    const day = parts[0].padStart(2, "0");
    const monthIndex = Number(parts[1]) - 1;
    const months = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
    const month = months[monthIndex] || parts[1];
    const year = parts[2];
    dateValue.textContent = `${day} ${month} ${year}`;
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

  function initAttendancePresenceToggle(){
    const radios = Array.from(document.querySelectorAll("input[name='attendance_presence']"));
    const presentTable = document.getElementById("attendance-present-table");
    const presentPager = document.getElementById("attendance-pagination");
    const absentBlock = document.getElementById("attendance-absent-block");
    if (!radios.length || !presentTable || !absentBlock) return;
    const setMode = (mode) => {
      const showPresent = mode === "present";
      presentTable.classList.toggle("is-hidden", !showPresent);
      if (presentPager) {
        presentPager.classList.toggle("is-hidden", !showPresent);
      }
      absentBlock.classList.toggle("is-hidden", showPresent);
    };
    radios.forEach((radio) => {
      radio.addEventListener("change", () => {
        if (radio.checked) {
          setMode(radio.value);
        }
      });
    });
    const initial = document.querySelector("input[name='attendance_presence']:checked")?.value || "present";
    setMode(initial);
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
    const initPager = (tableId, pagerId) => {
      const table = document.getElementById(tableId);
      const pager = document.getElementById(pagerId);
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
    };

    initPager("employee-table", "employee-pagination");
    initPager("employee-inactive-table", "employee-inactive-pagination");
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

      const formatRangeDate = (value) => {
        if (!value) return "-";
        const raw = String(value).trim();
        if (!raw) return "-";
        const isoMatch = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
        if (isoMatch) {
          return `${isoMatch[3]}-${isoMatch[2]}`;
        }
        const slashMatch = raw.match(/^(\d{2})[\/-](\d{2})[\/-](\d{4})/);
        if (slashMatch) {
          return `${slashMatch[1]}-${slashMatch[2]}`;
        }
        return raw;
      };

      const mapMethodLabel = (value) => {
        const normalized = (value || "").toString().trim().toLowerCase();
        if (normalized === "gps_selfie" || normalized === "gps+selfie") return "GPSLF";
        if (normalized === "gps") return "GPS";
        if (normalized === "qr") return "QR";
        return value || "-";
      };

      const renderRow = (row) => {
        const tr = document.createElement("tr");
        const checkInValue = row.check_in || "-";
        const checkOutValue = row.check_out || "-";
        const cells = [
          row.employee || "-",
          formatRangeDate(row.date),
          `${checkInValue} - ${checkOutValue}`,
          mapMethodLabel(row.method),
        ];
      cells.forEach((value, idx) => {
        const td = document.createElement("td");
        td.textContent = value;
        if (idx === 2) {
          td.classList.add("check-cell");
        }
        tr.appendChild(td);
      });
      return tr;
    };

    const renderTable = () => {
      tbody.innerHTML = "";
      if (!currentRows.length) {
        const emptyRow = document.createElement("tr");
        emptyRow.innerHTML = "<td colspan='4' class='empty-row'>Tidak ada data pada rentang ini.</td>";
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

  function escapeHtml(value){
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function patrolPane(){
    return document.getElementById("patrolAdminPane");
  }

  function patrolCanManage(){
    return patrolPane()?.dataset.canManage === "1";
  }

  function patrolSetFeedback(message, type = "muted"){
    const el = document.getElementById("patrolFeedbackMessage");
    if (!el) return;
    el.textContent = message || "";
    el.classList.toggle("is-error", type === "error");
    el.classList.toggle("is-success", type === "success");
    el.classList.toggle("is-muted", type === "muted");
  }

  function patrolFormatDate(value){
    const raw = (value || "").toString().trim();
    if (!raw) return "-";
    const date = new Date(`${raw}T00:00:00`);
    if (Number.isNaN(date.getTime())) return raw;
    return date.toLocaleDateString("id-ID", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  function patrolFormatDateTime(value){
    const raw = (value || "").toString().trim();
    if (!raw) return "-";
    const iso = raw.includes("T") ? raw : raw.replace(" ", "T");
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return raw;
    return date.toLocaleString("id-ID", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function patrolStatusLabel(status){
    const normalized = (status || "").toString().trim().toLowerCase();
    if (normalized === "ongoing") return "Sedang berjalan";
    if (normalized === "completed") return "Selesai";
    if (normalized === "invalid") return "Invalid";
    return "Terhenti";
  }

  function patrolStatusClass(status){
    const normalized = (status || "").toString().trim().toLowerCase();
    if (normalized === "ongoing") return "is-ongoing";
    if (normalized === "completed") return "is-completed";
    return "is-stopped";
  }

  function patrolProgressPercent(done, total){
    const doneValue = Number(done || 0);
    const totalValue = Number(total || 0);
    if (!totalValue || totalValue <= 0) return 0;
    const percent = Math.round((doneValue / totalValue) * 100);
    return Math.max(0, Math.min(100, percent));
  }

  async function patrolApi(path, options = {}){
    const method = (options.method || "GET").toUpperCase();
    const headers = {
      Accept: "application/json",
    };
    const fetchOptions = {
      method,
      headers,
    };
    if (method !== "GET") {
      headers["Content-Type"] = "application/json";
      headers["X-CSRF-Token"] = csrfToken;
      const payload = options.body && typeof options.body === "object"
        ? { ...options.body, csrf_token: csrfToken }
        : { csrf_token: csrfToken };
      fetchOptions.body = JSON.stringify(payload);
    }
    const response = await fetch(path, fetchOptions);
    const payload = await response.json().catch(() => null);
    if (!response.ok || !payload?.ok) {
      throw new Error(payload?.message || "Permintaan Guard Tour gagal diproses.");
    }
    return payload;
  }

  function patrolRenderHero(payload){
    const setup = payload?.setup || {};
    const route = setup.route || {};
    const monitoring = payload?.monitoring || {};
    const counts = monitoring.counts || {};
    const checkpointCount = Number(setup.checkpoint_count || 0);
    const checkpointLimit = Number(setup.checkpoint_limit || 30);
    const checkpointEl = document.getElementById("patrolHeroCheckpointCount");
    const routeNameEl = document.getElementById("patrolHeroRouteName");
    const ongoingEl = document.getElementById("patrolHeroOngoing");
    const completedEl = document.getElementById("patrolHeroCompleted");
    const stoppedEl = document.getElementById("patrolHeroStopped");
    const timeEl = document.getElementById("patrolLiveTimestamp");
    if (checkpointEl) checkpointEl.textContent = `${checkpointCount}/${checkpointLimit}`;
    if (routeNameEl) routeNameEl.textContent = route.name || "Guard Tour Route";
    if (ongoingEl) ongoingEl.textContent = String(Number(counts.ongoing || 0));
    if (completedEl) completedEl.textContent = String(Number(counts.completed || 0));
    if (stoppedEl) stoppedEl.textContent = String(Number(counts.stopped || 0));
    if (timeEl) {
      const now = new Date();
      timeEl.textContent = `Sinkron terakhir ${now.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
    }
  }

  function patrolRenderSetup(payload){
    const canManage = patrolCanManage();
    const setup = payload?.setup || {};
    const route = setup.route || {};
    const checkpoints = Array.isArray(setup.checkpoints) ? setup.checkpoints : [];
    const count = Number(setup.checkpoint_count || checkpoints.length || 0);
    const limit = Number(setup.checkpoint_limit || 30);
    const limitReached = Boolean(setup.limit_reached);
    const routeNameInput = document.getElementById("patrol-route-name");
    const intervalInput = document.getElementById("patrol-min-interval");
    const strictInput = document.getElementById("patrol-route-strict");
    const selfieInput = document.getElementById("patrol-route-selfie");
    const gpsInput = document.getElementById("patrol-route-gps");
    const badge = document.getElementById("patrolCheckpointBadge");
    const heroCount = document.getElementById("patrolHeroCheckpointCount");
    const submitBtn = document.getElementById("patrolCheckpointSubmitBtn");
    const limitMessage = document.getElementById("patrolLimitMessage");
    const list = document.getElementById("patrolCheckpointList");
    const empty = document.getElementById("patrolCheckpointEmpty");

    if (routeNameInput) routeNameInput.value = route.name || "Guard Tour Route";
    if (intervalInput) intervalInput.value = String(route.min_scan_interval_seconds ?? 45);
    if (strictInput) strictInput.checked = Boolean(route.strict_mode);
    if (selfieInput) selfieInput.checked = Boolean(route.require_selfie);
    if (gpsInput) gpsInput.checked = Boolean(route.require_gps ?? true);
    if (badge) badge.textContent = `${count}/${limit}`;
    if (heroCount) heroCount.textContent = `${count}/${limit}`;

    if (submitBtn) {
      submitBtn.disabled = !canManage || limitReached;
      submitBtn.textContent = limitReached ? "Upgrade ke Pro+" : "Tambah Checkpoint";
    }

    if (limitMessage) {
      const customMessage = setup.upgrade_message || "";
      if (customMessage || limitReached) {
        limitMessage.textContent = customMessage || "Checkpoint maksimal 30 titik. Upgrade ke Pro+ untuk menambah kapasitas.";
        limitMessage.classList.add("is-warning");
      } else {
        limitMessage.textContent = "";
        limitMessage.classList.remove("is-warning");
      }
    }

    if (!list || !empty) return;
    if (!checkpoints.length) {
      list.innerHTML = "";
      empty.classList.remove("is-hidden");
      return;
    }

    empty.classList.add("is-hidden");
    list.innerHTML = checkpoints.map((checkpoint) => {
      const checkpointId = Number(checkpoint.id || 0);
      const name = escapeHtml(checkpoint.nama || "-");
      const sequence = Number(checkpoint.urutan || 0);
      const qrCode = escapeHtml(checkpoint.qr_code || "");
      const nfcTag = escapeHtml(checkpoint.nfc_tag || "");
      const latitude = checkpoint.latitude ?? "";
      const longitude = checkpoint.longitude ?? "";
      const radiusMeters = checkpoint.radius_meters ?? "";
      return `
        <article class="patrol-cp-item" data-checkpoint-id="${checkpointId}" draggable="${canManage ? "true" : "false"}">
          <div class="patrol-cp-top">
            <div class="patrol-cp-seq">#${sequence}</div>
            <div class="patrol-cp-main">
              <div class="patrol-cp-name">${name}</div>
              <div class="patrol-cp-meta">QR: ${qrCode || "-"} | NFC: ${nfcTag || "-"}</div>
            </div>
            ${canManage ? `
            <div class="patrol-cp-actions">
              <button class="btn ghost patrol-cp-btn" type="button" data-action="edit-toggle" data-id="${checkpointId}">Edit</button>
              <button class="btn danger patrol-cp-btn" type="button" data-action="delete" data-id="${checkpointId}">Hapus</button>
            </div>
            ` : ""}
          </div>
          ${canManage ? `
          <form class="patrol-cp-edit-form is-hidden" data-edit-form="1" data-id="${checkpointId}">
            <div class="form-grid">
              <div class="form-row full">
                <label class="label">Nama Checkpoint</label>
                <input class="input" name="name" type="text" value="${name}" required />
              </div>
              <div class="form-row">
                <label class="label">QR / Barcode ID</label>
                <input class="input" name="qr_code" type="text" value="${qrCode}" />
              </div>
              <div class="form-row">
                <label class="label">NFC Tag</label>
                <input class="input" name="nfc_tag" type="text" value="${nfcTag}" />
              </div>
              <div class="form-row">
                <label class="label">Latitude</label>
                <input class="input" name="latitude" type="text" value="${escapeHtml(latitude)}" placeholder="-6.200000" />
              </div>
              <div class="form-row">
                <label class="label">Longitude</label>
                <input class="input" name="longitude" type="text" value="${escapeHtml(longitude)}" placeholder="106.816666" />
              </div>
              <div class="form-row">
                <label class="label">Radius (meter)</label>
                <input class="input" name="radius_meters" type="number" min="1" placeholder="35" value="${escapeHtml(radiusMeters)}" />
              </div>
            </div>
            <div class="patrol-cp-edit-actions">
              <button class="btn primary" type="submit">Simpan</button>
              <button class="btn ghost" type="button" data-action="edit-cancel" data-id="${checkpointId}">Batal</button>
            </div>
          </form>
          ` : ""}
        </article>
      `;
    }).join("");

    patrolBindCheckpointDrag(canManage);
  }

  function patrolRenderMonitoring(payload){
    const monitoring = payload?.monitoring || {};
    const rows = Array.isArray(monitoring.rows) ? monitoring.rows : [];
    const list = document.getElementById("patrolMonitoringList");
    const empty = document.getElementById("patrolMonitoringEmpty");
    if (!list || !empty) return;
    if (!rows.length) {
      list.innerHTML = "";
      empty.classList.remove("is-hidden");
      return;
    }
    empty.classList.add("is-hidden");
    list.innerHTML = rows.map((row) => {
      const done = Number(row.progress_done || 0);
      const total = Number(row.progress_total || 0);
      const percent = patrolProgressPercent(done, total);
      const employee = escapeHtml(row.employee_name || row.employee_email || "-");
      const email = escapeHtml(row.employee_email || "-");
      const status = (row.status || "").toString();
      return `
        <article class="patrol-monitor-item">
          <div class="patrol-monitor-top">
            <div class="patrol-monitor-name">${employee}</div>
            <span class="patrol-state-badge ${patrolStatusClass(status)}">${patrolStatusLabel(status)}</span>
          </div>
          <div class="patrol-monitor-email">${email}</div>
          <div class="patrol-progress-track">
            <span style="width:${percent}%"></span>
          </div>
          <div class="patrol-monitor-meta">
            <span>Progress ${done}/${total}</span>
            <span>Mulai ${patrolFormatDateTime(row.started_at)}</span>
          </div>
        </article>
      `;
    }).join("");
  }

  function patrolRenderRecap(payload){
    const rekap = payload?.rekap || {};
    const rows = Array.isArray(rekap.rows) ? rekap.rows : [];
    const total = Number(rekap.total || rows.length || 0);
    const totalEl = document.getElementById("patrolRecapTotal");
    const list = document.getElementById("patrolRecapList");
    const empty = document.getElementById("patrolRecapEmpty");
    if (totalEl) totalEl.textContent = `${total} sesi`;
    if (!list || !empty) return;
    if (!rows.length) {
      list.innerHTML = "";
      empty.classList.remove("is-hidden");
      return;
    }
    empty.classList.add("is-hidden");
    list.innerHTML = rows.map((row) => {
      const employee = escapeHtml(row.employee_name || row.employee_email || "-");
      const progressLabel = `${Number(row.checkpoint_tercapai || 0)} tercapai`;
      const missedLabel = `${Number(row.checkpoint_terlewat || 0)} terlewat`;
      const status = (row.status || "").toString();
      return `
        <article class="patrol-recap-item">
          <div class="patrol-recap-top">
            <div class="patrol-recap-name">${employee}</div>
            <span class="patrol-state-badge ${patrolStatusClass(status)}">${patrolStatusLabel(status)}</span>
          </div>
          <div class="patrol-recap-meta">${patrolFormatDate(row.tanggal_patroli)}</div>
          <div class="patrol-recap-stats">
            <span>${progressLabel}</span>
            <span>${missedLabel}</span>
          </div>
          <div class="patrol-recap-time">
            <span>Mulai: ${patrolFormatDateTime(row.waktu_mulai)}</span>
            <span>Selesai: ${patrolFormatDateTime(row.waktu_selesai)}</span>
          </div>
        </article>
      `;
    }).join("");
  }

  function patrolRenderStructure(payload){
    const dataStructure = payload?.data_structure || {};
    const preview = document.getElementById("patrolStructurePreview");
    if (!preview) return;
    const checkpoints = Array.isArray(dataStructure.checkpoints) ? dataStructure.checkpoints.slice(0, 30) : [];
    const sessions = Array.isArray(dataStructure.patrol_sessions) ? dataStructure.patrol_sessions.slice(0, 80) : [];
    const logs = Array.isArray(dataStructure.patrol_logs) ? dataStructure.patrol_logs.slice(-120) : [];
    preview.textContent = JSON.stringify(
      {
        checkpoints,
        patrol_sessions: sessions,
        patrol_logs: logs,
      },
      null,
      2
    );
  }

  function patrolApplyPayload(payload){
    patrolState.payload = payload || {};
    patrolState.lastSyncAt = Date.now();
    patrolRenderHero(patrolState.payload);
    patrolRenderSetup(patrolState.payload);
    patrolRenderMonitoring(patrolState.payload);
    patrolRenderRecap(patrolState.payload);
    patrolRenderStructure(patrolState.payload);
  }

  function patrolToggleCheckpointEditor(checkpointId, shouldOpen){
    const list = document.getElementById("patrolCheckpointList");
    if (!list) return;
    list.querySelectorAll(".patrol-cp-edit-form").forEach((form) => {
      const currentId = Number(form.dataset.id || 0);
      const mustOpen = shouldOpen && currentId === checkpointId;
      form.classList.toggle("is-hidden", !mustOpen);
    });
  }

  async function patrolLoadDashboard({ silent = false } = {}){
    if (!patrolPane()) return;
    if (patrolState.loading) return;
    patrolState.loading = true;
    if (!silent) {
      patrolSetFeedback("Memuat data Guard Tour...", "muted");
    }
    try {
      const response = await patrolApi("/api/client/patrol/dashboard");
      patrolApplyPayload(response.data || {});
      if (!silent) {
        patrolSetFeedback("Data Guard Tour berhasil dimuat.", "success");
      }
    } catch (error) {
      patrolSetFeedback(error.message || "Gagal memuat data Guard Tour.", "error");
    } finally {
      patrolState.loading = false;
    }
  }

  async function patrolSubmitRouteForm(form){
    if (!form) return;
    const submitBtn = form.querySelector("button[type='submit']");
    const payload = {
      route_name: (form.querySelector("[name='route_name']")?.value || "").trim(),
      min_scan_interval_seconds: (form.querySelector("[name='min_scan_interval_seconds']")?.value || "").trim(),
      strict_mode: form.querySelector("[name='strict_mode']")?.checked ? 1 : 0,
      require_selfie: form.querySelector("[name='require_selfie']")?.checked ? 1 : 0,
      require_gps: form.querySelector("[name='require_gps']")?.checked ? 1 : 0,
    };
    if (submitBtn) submitBtn.disabled = true;
    patrolSetFeedback("Menyimpan setup patrol...", "muted");
    try {
      const response = await patrolApi("/api/client/patrol/route", {
        method: "POST",
        body: payload,
      });
      patrolApplyPayload(response.data || {});
      patrolSetFeedback(response.message || "Setup patroli tersimpan.", "success");
    } catch (error) {
      patrolSetFeedback(error.message || "Gagal menyimpan setup patroli.", "error");
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  async function patrolSubmitCheckpointForm(form){
    if (!form) return;
    const submitBtn = form.querySelector("button[type='submit']");
    const payload = {
      name: (form.querySelector("[name='name']")?.value || "").trim(),
      qr_code: (form.querySelector("[name='qr_code']")?.value || "").trim(),
      nfc_tag: (form.querySelector("[name='nfc_tag']")?.value || "").trim(),
      latitude: (form.querySelector("[name='latitude']")?.value || "").trim(),
      longitude: (form.querySelector("[name='longitude']")?.value || "").trim(),
      radius_meters: (form.querySelector("[name='radius_meters']")?.value || "").trim(),
    };
    if (!payload.name) {
      patrolSetFeedback("Nama checkpoint wajib diisi.", "error");
      return;
    }
    if (submitBtn) submitBtn.disabled = true;
    patrolSetFeedback("Menambahkan checkpoint...", "muted");
    try {
      const response = await patrolApi("/api/client/patrol/checkpoints/create", {
        method: "POST",
        body: payload,
      });
      form.reset();
      patrolApplyPayload(response.data || {});
      patrolSetFeedback(response.message || "Checkpoint berhasil ditambahkan.", "success");
    } catch (error) {
      patrolSetFeedback(error.message || "Gagal menambahkan checkpoint.", "error");
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  async function patrolSubmitCheckpointEditForm(form){
    if (!form) return;
    const checkpointId = Number(form.dataset.id || 0);
    if (!checkpointId) return;
    const submitBtn = form.querySelector("button[type='submit']");
    const payload = {
      name: (form.querySelector("[name='name']")?.value || "").trim(),
      qr_code: (form.querySelector("[name='qr_code']")?.value || "").trim(),
      nfc_tag: (form.querySelector("[name='nfc_tag']")?.value || "").trim(),
      latitude: (form.querySelector("[name='latitude']")?.value || "").trim(),
      longitude: (form.querySelector("[name='longitude']")?.value || "").trim(),
      radius_meters: (form.querySelector("[name='radius_meters']")?.value || "").trim(),
    };
    if (!payload.name) {
      patrolSetFeedback("Nama checkpoint wajib diisi.", "error");
      return;
    }
    if (submitBtn) submitBtn.disabled = true;
    patrolSetFeedback("Menyimpan perubahan checkpoint...", "muted");
    try {
      const response = await patrolApi(`/api/client/patrol/checkpoints/${checkpointId}/update`, {
        method: "POST",
        body: payload,
      });
      patrolApplyPayload(response.data || {});
      patrolSetFeedback(response.message || "Checkpoint berhasil diperbarui.", "success");
    } catch (error) {
      patrolSetFeedback(error.message || "Gagal memperbarui checkpoint.", "error");
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  }

  async function patrolDeleteCheckpoint(checkpointId){
    if (!checkpointId) return;
    if (!window.confirm("Hapus checkpoint ini dari route patroli?")) return;
    patrolSetFeedback("Menghapus checkpoint...", "muted");
    try {
      const response = await patrolApi(`/api/client/patrol/checkpoints/${checkpointId}/delete`, {
        method: "POST",
      });
      patrolApplyPayload(response.data || {});
      patrolSetFeedback(response.message || "Checkpoint berhasil dihapus.", "success");
    } catch (error) {
      patrolSetFeedback(error.message || "Gagal menghapus checkpoint.", "error");
    }
  }

  async function patrolPersistCheckpointOrder(){
    const list = document.getElementById("patrolCheckpointList");
    if (!list) return;
    const orderedIds = Array.from(list.querySelectorAll(".patrol-cp-item"))
      .map((item) => Number(item.dataset.checkpointId || 0))
      .filter((value) => value > 0);
    if (!orderedIds.length) return;
    patrolSetFeedback("Menyimpan urutan checkpoint...", "muted");
    try {
      const response = await patrolApi("/api/client/patrol/checkpoints/reorder", {
        method: "POST",
        body: { checkpoint_ids: orderedIds },
      });
      patrolApplyPayload(response.data || {});
      patrolSetFeedback(response.message || "Urutan checkpoint berhasil diperbarui.", "success");
    } catch (error) {
      patrolSetFeedback(error.message || "Gagal menyimpan urutan checkpoint.", "error");
      patrolLoadDashboard({ silent: true });
    }
  }

  function patrolBindCheckpointDrag(canManage){
    const list = document.getElementById("patrolCheckpointList");
    if (!list) return;
    const items = Array.from(list.querySelectorAll(".patrol-cp-item"));
    items.forEach((item) => {
      if (!canManage) {
        item.draggable = false;
        return;
      }
      item.draggable = true;
      item.addEventListener("dragstart", () => {
        patrolState.dragCheckpointId = Number(item.dataset.checkpointId || 0);
        item.classList.add("is-dragging");
      });
      item.addEventListener("dragend", () => {
        patrolState.dragCheckpointId = null;
        item.classList.remove("is-dragging");
        items.forEach((target) => target.classList.remove("is-dragover"));
      });
      item.addEventListener("dragover", (event) => {
        event.preventDefault();
        item.classList.add("is-dragover");
      });
      item.addEventListener("dragleave", () => {
        item.classList.remove("is-dragover");
      });
      item.addEventListener("drop", async (event) => {
        event.preventDefault();
        item.classList.remove("is-dragover");
        const dragId = patrolState.dragCheckpointId;
        const targetId = Number(item.dataset.checkpointId || 0);
        if (!dragId || !targetId || dragId === targetId) return;
        const dragged = list.querySelector(`.patrol-cp-item[data-checkpoint-id="${dragId}"]`);
        if (!dragged) return;
        const rect = item.getBoundingClientRect();
        const shouldInsertBefore = event.clientY < rect.top + rect.height / 2;
        if (shouldInsertBefore) {
          list.insertBefore(dragged, item);
        } else {
          list.insertBefore(dragged, item.nextSibling);
        }
        await patrolPersistCheckpointOrder();
      });
    });
  }

  function patrolStartPolling(){
    if (patrolState.pollingHandle) return;
    patrolState.pollingHandle = window.setInterval(() => {
      if (swipeIndex !== 4) return;
      if (document.hidden) return;
      patrolLoadDashboard({ silent: true });
    }, 15000);
  }

  function patrolStopPolling(){
    if (!patrolState.pollingHandle) return;
    window.clearInterval(patrolState.pollingHandle);
    patrolState.pollingHandle = null;
  }

  function patrolHandleTabChange(){
    if (!patrolPane()) return;
    if (swipeIndex === 4) {
      patrolStartPolling();
      patrolLoadDashboard({ silent: true });
    } else {
      patrolStopPolling();
    }
  }

  function initPatrolDashboard(){
    const root = patrolPane();
    if (!root || patrolState.initialized) return;
    patrolState.initialized = true;
    const routeForm = document.getElementById("patrolRouteForm");
    const checkpointForm = document.getElementById("patrolCheckpointForm");
    const checkpointList = document.getElementById("patrolCheckpointList");
    const refreshBtn = document.getElementById("patrolRefreshBtn");

    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        patrolLoadDashboard({ silent: false });
      });
    }

    if (routeForm) {
      routeForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await patrolSubmitRouteForm(routeForm);
      });
    }

    if (checkpointForm) {
      checkpointForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        await patrolSubmitCheckpointForm(checkpointForm);
      });
    }

    if (checkpointList) {
      checkpointList.addEventListener("click", async (event) => {
        const button = event.target.closest("button[data-action]");
        if (!button) return;
        const action = button.dataset.action || "";
        const checkpointId = Number(button.dataset.id || 0);
        if (action === "edit-toggle") {
          patrolToggleCheckpointEditor(checkpointId, true);
          return;
        }
        if (action === "edit-cancel") {
          patrolToggleCheckpointEditor(0, false);
          return;
        }
        if (action === "delete") {
          await patrolDeleteCheckpoint(checkpointId);
        }
      });

      checkpointList.addEventListener("submit", async (event) => {
        const form = event.target.closest("form[data-edit-form='1']");
        if (!form) return;
        event.preventDefault();
        await patrolSubmitCheckpointEditForm(form);
      });
    }

    document.addEventListener("visibilitychange", () => {
      if (document.hidden) return;
      if (swipeIndex === 4) {
        patrolLoadDashboard({ silent: true });
      }
    });

    window.addEventListener("beforeunload", patrolStopPolling);
  }

  function initEmployeeActionMenus(){
    const menus = Array.from(document.querySelectorAll(".employee-actions"));
    if (!menus.length) return;
    const profileModal = document.getElementById("employeeProfileModal");
    const profileSubtitle = profileModal?.querySelector("#employeeProfileSubtitle");
    const profileFields = profileModal ? Array.from(profileModal.querySelectorAll("[data-employee-profile]")) : [];
    const editModal = document.getElementById("employeeEditModal");
    const editSubtitle = editModal?.querySelector("#employeeEditSubtitle");
    const editForm = document.getElementById("employeeEditForm");
    const deleteForm = document.getElementById("employeeDeleteForm");
    const deleteEmail = deleteForm?.querySelector("input[name='email']");
    const editInputs = {
      nik: editForm?.querySelector("#employeeEditNik"),
      name: editForm?.querySelector("#employeeEditName"),
      email: editForm?.querySelector("#employeeEditEmail"),
      noHp: editForm?.querySelector("#employeeEditPhone"),
      address: editForm?.querySelector("#employeeEditAddress"),
      gender: editForm?.querySelector("#employeeEditGender"),
      statusNikah: editForm?.querySelector("#employeeEditMarital"),
      status: editForm?.querySelector("#employeeEditStatus"),
      notes: editForm?.querySelector("#employeeEditNotes"),
    };
    const datasetKey = (key) => `employee${key.charAt(0).toUpperCase()}${key.slice(1)}`;
    const datasetValue = (menu, key) => (menu?.dataset[datasetKey(key)] || "").trim();
    const panelOrigins = new Map();
    const menuPanels = new Map();
    const formatProfileValue = (key, value) => {
      if (!value) return "-";
      if (key === "status") {
        return value === "1" ? "Aktif" : "Nonaktif";
      }
      return value;
    };
    const getPanelForMenu = (menu) => {
      if (!menu) return null;
      const cached = menuPanels.get(menu);
      if (cached) return cached;
      const found = menu.querySelector(".employee-menu");
      if (found) {
        menuPanels.set(menu, found);
        return found;
      }
      return null;
    };
    const restorePanel = (menu) => {
      const panel = getPanelForMenu(menu);
      if (!panel) return;
      const origin = panelOrigins.get(panel);
      if (origin && panel.parentElement !== origin) {
        origin.appendChild(panel);
      }
      panel.classList.remove("is-open", "is-floating");
      panel.style.position = "";
      panel.style.top = "";
      panel.style.left = "";
      panel.style.right = "";
      panel.style.bottom = "";
      panel.style.minWidth = "";
    };
    const closeAllMenus = () => {
      menus.forEach((menu) => {
        menu.classList.remove("is-open");
        const toggle = menu.querySelector(".employee-menu-toggle");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
        restorePanel(menu);
      });
    };
    const positionFloatingPanel = (panel, anchorRect) => {
      if (!panel || !anchorRect) return;
      panel.style.position = "fixed";
      panel.style.top = "0px";
      panel.style.left = "0px";
      panel.style.right = "auto";
      panel.style.bottom = "auto";
      panel.style.minWidth = `${Math.max(180, anchorRect.width)}px`;
      const panelWidth = panel.offsetWidth || 220;
      const panelHeight = panel.offsetHeight || 120;
      const margin = 8;
      let left = anchorRect.right - panelWidth;
      if (left < margin) left = margin;
      if (left + panelWidth > window.innerWidth - margin) {
        left = Math.max(margin, window.innerWidth - panelWidth - margin);
      }
      let top = anchorRect.bottom + margin;
      if (top + panelHeight > window.innerHeight - margin) {
        top = anchorRect.top - panelHeight - margin;
      }
      if (top < margin) top = margin;
      panel.style.left = `${Math.round(left)}px`;
      panel.style.top = `${Math.round(top)}px`;
    };
    const openFloatingMenu = (menu) => {
      const toggle = menu.querySelector(".employee-menu-toggle");
      const panel = getPanelForMenu(menu);
      if (!toggle || !panel) return;
      const isOpen = panel.classList.contains("is-open");
      closeAllMenus();
      if (isOpen) return;
      if (!panelOrigins.has(panel)) {
        panelOrigins.set(panel, menu);
      }
      menu.classList.add("is-open");
      toggle.setAttribute("aria-expanded", "true");
      panel.classList.add("is-open", "is-floating");
      if (panel.parentElement !== document.body) {
        document.body.appendChild(panel);
      }
      const anchorRect = toggle.getBoundingClientRect();
      positionFloatingPanel(panel, anchorRect);
    };
    const fillProfileModal = (menu) => {
      if (!profileModal) return;
      const name = datasetValue(menu, "name") || "-";
      const email = datasetValue(menu, "email") || "-";
      if (profileSubtitle) {
        profileSubtitle.textContent = `${name} • ${email}`;
      }
      profileFields.forEach((field) => {
        const key = field.dataset.employeeProfile || "";
        const rawValue = key === "status" ? datasetValue(menu, "isActive") : datasetValue(menu, key);
        field.textContent = formatProfileValue(key, rawValue);
      });
    };
    const fillEditForm = (menu) => {
      if (!editForm) return;
      const employeeId = datasetValue(menu, "id");
      const name = datasetValue(menu, "name") || "-";
      const email = datasetValue(menu, "email") || "-";
      editForm.action = `/client/employees/${employeeId}/update`;
      editInputs.nik && (editInputs.nik.value = datasetValue(menu, "nik"));
      editInputs.name && (editInputs.name.value = datasetValue(menu, "name"));
      editInputs.email && (editInputs.email.value = datasetValue(menu, "email"));
      editInputs.noHp && (editInputs.noHp.value = datasetValue(menu, "noHp"));
      editInputs.address && (editInputs.address.value = datasetValue(menu, "address"));
      editInputs.gender && (editInputs.gender.value = datasetValue(menu, "gender") || "");
      editInputs.statusNikah && (editInputs.statusNikah.value = datasetValue(menu, "statusNikah") || "");
      editInputs.notes && (editInputs.notes.value = datasetValue(menu, "notes"));
      if (editInputs.status) {
        const statusValue = datasetValue(menu, "isActive");
        editInputs.status.value = statusValue === "0" ? "0" : "1";
      }
      if (deleteEmail) {
        deleteEmail.value = datasetValue(menu, "email");
      }
      if (editSubtitle) {
        editSubtitle.textContent = `${name} • ${email}`;
      }
    };
    menus.forEach((menu) => {
      const toggle = menu.querySelector(".employee-menu-toggle");
      const panel = getPanelForMenu(menu);
      toggle?.addEventListener("click", (event) => {
        event.stopPropagation();
        openFloatingMenu(menu);
      });
      menu.addEventListener("click", (event) => event.stopPropagation());
      panel?.addEventListener("click", (event) => event.stopPropagation());
      menu.querySelectorAll("[data-employee-action]").forEach((button) => {
        button.addEventListener("click", () => {
          const action = button.dataset.employeeAction;
          if (action === "profile") {
            fillProfileModal(menu);
          } else if (action === "edit") {
            fillEditForm(menu);
          }
          closeAllMenus();
        });
      });
    });
    document.addEventListener("click", closeAllMenus);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeAllMenus();
      }
    });
    window.addEventListener("resize", closeAllMenus);
    document.addEventListener("scroll", closeAllMenus, true);
  }

  document.addEventListener("DOMContentLoaded", () => {
    initSwipe();
    initGps();
    initSiteLocationPicker();
    initHeaderClock();
    initHeaderDate();
    initAttendanceDate();
    initDatePickers();
    initAttendancePresenceToggle();
    initChangePassword();
    initEmployeeAssignmentForm();
    initEmployeeActionMenus();
    initModals();
    initCollapsiblePanels();
    initEmployeeTablePagination();
    initAttendanceTablePagination();
    initAttendanceReportToggle();
    initAttendanceRangeReport();
    initPatrolDashboard();
    try {
      localStorage.removeItem(tabStorageKey);
    } catch (e) {}
    go(0);
  });
})();
