/* Guard browser BACK on dashboard pages: keep user inside dashboard and route to dashboard home. */
(function () {
  "use strict";

  var body = document.body;
  if (!body || !window.history || typeof window.history.pushState !== "function") {
    return;
  }

  var homeUrl = body.getAttribute("data-dashboard-home");
  if (!homeUrl) {
    return;
  }

  var markerKey = "__dashboard_back_guard__";
  var lockKey = "gmi_dashboard_back_lock";
  var homeKey = "gmi_dashboard_home_url";
  var suppressNextPop = false;

  function isObject(value) {
    return value !== null && typeof value === "object";
  }

  function cloneState(state) {
    return isObject(state) ? Object.assign({}, state) : {};
  }

  function absoluteHomeUrl() {
    return new URL(homeUrl, window.location.origin);
  }

  function isAtHome() {
    var target = absoluteHomeUrl();
    return (
      window.location.pathname === target.pathname &&
      window.location.search === target.search &&
      window.location.hash === target.hash
    );
  }

  function hasTabNavigation() {
    return !!document.querySelector(".nav-btn[data-tab]");
  }

  function isTabHomeActive() {
    var activeTab = document.querySelector(".nav-btn.active[data-tab]");
    if (!activeTab) {
      return true;
    }
    return (activeTab.getAttribute("data-tab") || "") === "0";
  }

  function goTabHome() {
    var homeTabBtn = document.querySelector(".nav-btn[data-tab='0']");
    if (!homeTabBtn) {
      return false;
    }
    homeTabBtn.click();
    return true;
  }

  function armCurrentEntry() {
    var current = cloneState(window.history.state);
    if (!current[markerKey]) {
      current[markerKey] = true;
      window.history.replaceState(current, "", window.location.href);
    }
  }

  function pushBufferEntry() {
    try {
      window.history.pushState(
        {
          __dashboard_back_buffer__: true,
          __dashboard_back_ts__: Date.now(),
        },
        "",
        window.location.href
      );
      return true;
    } catch (e) {
      return false;
    }
  }

  function seedBuffer(count) {
    for (var i = 0; i < count; i += 1) {
      if (!pushBufferEntry()) {
        break;
      }
    }
  }

  function saveLock() {
    try {
      var target = absoluteHomeUrl();
      window.localStorage.setItem(lockKey, "1");
      window.localStorage.setItem(
        homeKey,
        target.pathname + target.search + target.hash
      );
    } catch (e) {}
  }

  function clearLock() {
    try {
      window.localStorage.removeItem(lockKey);
      window.localStorage.removeItem(homeKey);
    } catch (e) {}
  }

  function bindLogoutIntent() {
    var forms = document.querySelectorAll("form[action]");
    forms.forEach(function (form) {
      var action = form.getAttribute("action") || "";
      if (!/\/logout\/?$/.test(action)) {
        return;
      }
      form.addEventListener("submit", function () {
        clearLock();
      });
    });
  }

  saveLock();
  bindLogoutIntent();
  armCurrentEntry();
  seedBuffer(2);

  window.addEventListener("pageshow", function (event) {
    // Re-arm only when restored from BFCache (common on mobile browsers).
    if (!event || event.persisted !== true) {
      return;
    }
    armCurrentEntry();
    seedBuffer(2);
  });

  window.addEventListener("popstate", function () {
    if (suppressNextPop) {
      suppressNextPop = false;
      return;
    }

    if (!isAtHome()) {
      var target = absoluteHomeUrl();
      window.location.replace(target.pathname + target.search + target.hash);
      return;
    }

    if (hasTabNavigation() && !isTabHomeActive()) {
      if (goTabHome()) {
        seedBuffer(2);
      }
      return;
    }

    suppressNextPop = true;
    try {
      window.history.go(1);
    } catch (e) {}
    seedBuffer(2);
  });
})();
