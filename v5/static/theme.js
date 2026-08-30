(() => {
  "use strict";

  const STORAGE_KEY = "buteomai:theme";
  const root = document.documentElement;
  const toggle = document.getElementById("theme-toggle");
  const label = document.getElementById("theme-toggle-label");
  const favicon = document.getElementById("theme-favicon");
  const themeColor = document.querySelector('meta[name="theme-color"]');
  const systemPreference = window.matchMedia("(prefers-color-scheme: dark)");

  function savedTheme() {
    try {
      const value = window.localStorage.getItem(STORAGE_KEY);
      return value === "light" || value === "dark" ? value : null;
    } catch {
      return null;
    }
  }

  function storeTheme(theme) {
    try { window.localStorage.setItem(STORAGE_KEY, theme); } catch { /* Theme persistence is best-effort. */ }
  }

  function refreshThemeDependentGraphics() {
    window.requestAnimationFrame(() => {
      if (typeof window.renderCharts === "function") window.renderCharts();
      else if (typeof renderCharts === "function") renderCharts();
    });
  }

  function applyTheme(theme, persist = false) {
    const isDark = theme === "dark";
    const nextThemeLabel = isDark ? "화이트모드" : "다크모드";
    root.dataset.theme = isDark ? "dark" : "light";
    root.style.colorScheme = isDark ? "dark" : "light";
    if (toggle) {
      toggle.dataset.theme = root.dataset.theme;
      toggle.setAttribute("aria-pressed", String(isDark));
      toggle.setAttribute("aria-label", `현재 ${isDark ? "다크모드" : "화이트모드"}. ${nextThemeLabel}로 변경`);
      toggle.title = `${nextThemeLabel}로 변경`;
    }
    if (label) label.textContent = nextThemeLabel;
    if (favicon) favicon.href = `/static/brand/${isDark ? "buteomai-mark-dark" : "buteomai-mark"}.svg?v=brand-001`;
    if (themeColor) themeColor.content = isDark ? "#0d130f" : "#f3f7f4";
    if (persist) storeTheme(root.dataset.theme);
    refreshThemeDependentGraphics();
  }

  applyTheme(root.dataset.theme === "dark" ? "dark" : "light");
  toggle?.addEventListener("click", () => applyTheme(root.dataset.theme === "dark" ? "light" : "dark", true));
  systemPreference.addEventListener?.("change", (event) => {
    if (!savedTheme()) applyTheme(event.matches ? "dark" : "light");
  });
})();
