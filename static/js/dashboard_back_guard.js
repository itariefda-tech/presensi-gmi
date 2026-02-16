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
  var navGuardBusy = false;

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
      window.location.search === target.search
    );
  }

  function armCurrentEntry() {
    var current = cloneState(window.history.state);
    if (!current[markerKey]) {
      current[markerKey] = true;
      window.history.replaceState(current, "", window.location.href);
    }
  }

  function pushBufferEntry() {
    window.history.pushState(
      {
        __dashboard_back_buffer__: true,
        __dashboard_back_ts__: Date.now(),
      },
      "",
      window.location.href
    );
  }

  armCurrentEntry();
  pushBufferEntry();

  window.addEventListener("popstate", function () {
    if (navGuardBusy) {
      return;
    }

    navGuardBusy = true;

    if (!isAtHome()) {
      var target = absoluteHomeUrl();
      window.location.replace(target.pathname + target.search + target.hash);
      return;
    }

    pushBufferEntry();
    window.setTimeout(function () {
      navGuardBusy = false;
    }, 0);
  });
})();
