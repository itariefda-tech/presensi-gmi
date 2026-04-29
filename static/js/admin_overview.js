(function () {
  const valueEl = document.getElementById("kpiCoordsValue");
  const metaEl = document.getElementById("kpiCoordsMeta");
  const refreshBtn = document.getElementById("kpiCoordsRefresh");

  const setMeta = (text) => {
    if (metaEl) metaEl.textContent = text;
  };

  const setLoading = (isLoading) => {
    if (!refreshBtn) return;
    refreshBtn.disabled = isLoading;
    if (isLoading) setMeta("Mengambil lokasi...");
  };

  const updateCoords = (pos) => {
    if (!valueEl) return;
    const lat = Number(pos.coords.latitude);
    const lon = Number(pos.coords.longitude);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      valueEl.textContent = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
    } else {
      valueEl.textContent = "Belum ada koordinat.";
    }
    const accuracy = Number(pos.coords.accuracy);
    if (Number.isFinite(accuracy)) {
      setMeta(`Akurasi +/- ${Math.round(accuracy)} m`);
    } else {
      setMeta("Latitude · Longitude");
    }
  };

  const handleError = (err) => {
    if (valueEl) valueEl.textContent = "Belum ada koordinat.";
    let msg = "Gagal mengambil lokasi.";
    if (err && err.code === 1) msg = "Izin lokasi ditolak.";
    else if (err && err.code === 2) msg = "Lokasi tidak tersedia.";
    else if (err && err.code === 3) msg = "Permintaan lokasi timeout.";
    setMeta(msg);
  };

  const requestLocation = () => {
    if (!refreshBtn || !valueEl || !metaEl) return;
    if (!navigator.geolocation) {
      setMeta("Geolocation tidak didukung.");
      refreshBtn.disabled = true;
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLoading(false);
        updateCoords(pos);
      },
      (err) => {
        setLoading(false);
        handleError(err);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  if (refreshBtn && valueEl && metaEl) {
    refreshBtn.addEventListener("click", requestLocation);
    requestLocation();
  }

  const graphicsRoot = document.getElementById("overviewGraphics");
  const donutCanvas = document.getElementById("overviewDonutChart");
  const donutLegend = document.getElementById("overviewDonutLegend");
  const lineCanvas = document.getElementById("overviewTopClientsLine");
  const lineLegend = document.getElementById("overviewTopClientsLegend");

  if (!graphicsRoot || !donutCanvas || !donutLegend || !lineCanvas || !lineLegend) return;

  let clientSummaries = [];
  try {
    const raw = graphicsRoot.getAttribute("data-client-summaries") || "[]";
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) clientSummaries = parsed;
  } catch (e) {
    clientSummaries = [];
  }

  const toNumber = (v) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  };

  const aggregated = clientSummaries.reduce(
    (acc, item) => {
      acc.late += toNumber(item.late_count);
      acc.absent += toNumber(item.absent_count);
      acc.leave += toNumber(item.leave_pending_count);
      return acc;
    },
    { late: 0, absent: 0, leave: 0 }
  );

  const donutData = [
    { key: "late", label: "Telat", value: aggregated.late, color: "#f59e0b" },
    { key: "absent", label: "Absen", value: aggregated.absent, color: "#ef4444" },
    { key: "leave", label: "Leave Pending", value: aggregated.leave, color: "#6366f1" },
  ];

  const donutTotal = donutData.reduce((s, d) => s + d.value, 0);
  const ctx = donutCanvas.getContext("2d");

  const drawDonut = () => {
    if (!ctx) return;
    const width = donutCanvas.width;
    const height = donutCanvas.height;
    ctx.clearRect(0, 0, width, height);

    const cx = width / 2;
    const cy = height / 2;
    const outer = Math.min(width, height) * 0.42;
    const inner = outer * 0.58;

    if (donutTotal <= 0) {
      ctx.beginPath();
      ctx.arc(cx, cy, outer, 0, Math.PI * 2);
      ctx.arc(cx, cy, inner, 0, Math.PI * 2, true);
      ctx.closePath();
      ctx.fillStyle = "rgba(148,163,184,.25)";
      ctx.fill();

      ctx.fillStyle = "rgba(148,163,184,.85)";
      ctx.font = "600 14px Segoe UI, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Belum ada data", cx, cy + 5);
      return;
    }

    let start = -Math.PI / 2;
    donutData.forEach((item) => {
      if (item.value <= 0) return;
      const slice = (item.value / donutTotal) * Math.PI * 2;
      const end = start + slice;

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, outer, start, end);
      ctx.closePath();
      ctx.fillStyle = item.color;
      ctx.fill();

      start = end;
    });

    ctx.globalCompositeOperation = "destination-out";
    ctx.beginPath();
    ctx.arc(cx, cy, inner, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalCompositeOperation = "source-over";

    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--text") || "#e7ecf6";
    ctx.font = "700 26px Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(String(donutTotal), cx, cy - 2);

    ctx.fillStyle = "rgba(148,163,184,.95)";
    ctx.font = "600 12px Segoe UI, sans-serif";
    ctx.fillText("Total Issue", cx, cy + 18);
  };

  donutLegend.innerHTML = donutData
    .map((item) => {
      const percent = donutTotal > 0 ? Math.round((item.value / donutTotal) * 100) : 0;
      return `
        <div class="overview-legend-item">
          <div class="overview-legend-item-left">
            <span class="overview-legend-dot" style="background:${item.color}"></span>
            <span>${item.label}</span>
          </div>
          <strong>${item.value} (${percent}%)</strong>
        </div>
      `;
    })
    .join("");

  drawDonut();

  const topClients = clientSummaries
    .map((item) => {
      const totalIssue = toNumber(item.late_count) + toNumber(item.absent_count) + toNumber(item.leave_pending_count);
      return {
        name: item.client_name || "-",
        totalIssue,
      };
    })
    .sort((a, b) => b.totalIssue - a.totalIssue)
    .slice(0, 5);

  const lineCtx = lineCanvas.getContext("2d");

  const drawLineChart = () => {
    if (!lineCtx) return;
    const w = lineCanvas.width;
    const h = lineCanvas.height;
    lineCtx.clearRect(0, 0, w, h);

    if (!topClients.length || topClients.every((i) => i.totalIssue <= 0)) {
      lineCtx.fillStyle = "rgba(148,163,184,.85)";
      lineCtx.font = "600 14px Segoe UI, sans-serif";
      lineCtx.textAlign = "center";
      lineCtx.fillText("Belum ada data issue per client.", w / 2, h / 2);
      return;
    }

    const pad = { top: 20, right: 28, bottom: 46, left: 34 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;
    const maxVal = Math.max(...topClients.map((i) => i.totalIssue), 1);

    lineCtx.strokeStyle = "rgba(148,163,184,.28)";
    lineCtx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (chartH / 4) * i;
      lineCtx.beginPath();
      lineCtx.moveTo(pad.left, y);
      lineCtx.lineTo(w - pad.right, y);
      lineCtx.stroke();
    }

    const points = topClients.map((item, idx) => {
      const x =
        pad.left +
        (topClients.length === 1 ? chartW / 2 : (chartW / (topClients.length - 1)) * idx);
      const y = pad.top + chartH - (item.totalIssue / maxVal) * chartH;
      return { x, y, value: item.totalIssue, name: item.name };
    });

    lineCtx.beginPath();
    points.forEach((p, idx) => {
      if (idx === 0) lineCtx.moveTo(p.x, p.y);
      else lineCtx.lineTo(p.x, p.y);
    });
    lineCtx.strokeStyle = "#38bdf8";
    lineCtx.lineWidth = 2.5;
    lineCtx.shadowColor = "rgba(56,189,248,.35)";
    lineCtx.shadowBlur = 10;
    lineCtx.stroke();
    lineCtx.shadowBlur = 0;

    points.forEach((p) => {
      lineCtx.beginPath();
      lineCtx.arc(p.x, p.y, 4.5, 0, Math.PI * 2);
      lineCtx.fillStyle = "#6366f1";
      lineCtx.fill();
      lineCtx.strokeStyle = "#c4b5fd";
      lineCtx.lineWidth = 1.2;
      lineCtx.stroke();
    });

    lineCtx.fillStyle = "rgba(148,163,184,.95)";
    lineCtx.font = "11px Segoe UI, sans-serif";
    lineCtx.textAlign = "center";
    points.forEach((p, idx) => {
      const shortName = (p.name || "-").length > 12 ? `${p.name.slice(0, 12)}…` : p.name;
      lineCtx.fillText(shortName, p.x, h - 18);
      lineCtx.fillText(`#${idx + 1}`, p.x, h - 5);
    });
  };

  lineLegend.innerHTML = topClients.length
    ? topClients
        .map(
          (item, idx) => `
      <div class="overview-line-legend-item">
        <div class="overview-line-legend-left">
          <span class="overview-line-dot" style="background:${idx % 2 === 0 ? "#38bdf8" : "#6366f1"}"></span>
          <span>#${idx + 1} ${item.name}</span>
        </div>
        <strong>${item.totalIssue}</strong>
      </div>
    `
        )
        .join("")
    : '<div class="overview-empty">Belum ada data issue per client.</div>';

  drawLineChart();
})();
