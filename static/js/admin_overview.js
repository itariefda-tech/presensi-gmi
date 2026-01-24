(function(){
  const valueEl = document.getElementById("kpiCoordsValue");
  const metaEl = document.getElementById("kpiCoordsMeta");
  const refreshBtn = document.getElementById("kpiCoordsRefresh");
  if (!valueEl || !metaEl || !refreshBtn) return;

  const setMeta = (text) => {
    metaEl.textContent = text;
  };

  const setLoading = (isLoading) => {
    refreshBtn.disabled = isLoading;
    if (isLoading) {
      setMeta("Mengambil lokasi...");
    }
  };

  const updateCoords = (pos) => {
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
    valueEl.textContent = "Belum ada koordinat.";
    let msg = "Gagal mengambil lokasi.";
    if (err && err.code === 1) {
      msg = "Izin lokasi ditolak.";
    } else if (err && err.code === 2) {
      msg = "Lokasi tidak tersedia.";
    } else if (err && err.code === 3) {
      msg = "Permintaan lokasi timeout.";
    }
    setMeta(msg);
  };

  const requestLocation = () => {
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
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  refreshBtn.addEventListener("click", requestLocation);
  requestLocation();
})();
