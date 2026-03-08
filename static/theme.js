// /static/theme.js
(() => {
  const KEY = "applymate_theme_v1";
  const root = document.documentElement;

  function applyTheme(t) {
    root.dataset.theme = (t === "light") ? "light" : "dark";
    const btn = document.getElementById("themeToggle");
    if (btn) btn.textContent = (root.dataset.theme === "dark") ? "☾" : "☀";
  }

  const stored = localStorage.getItem(KEY);
  const prefersDark = window.matchMedia?.("(prefers-color-scheme: dark)")?.matches;
  applyTheme(stored || (prefersDark ? "dark" : "light"));

  function toggle() {
    const next = (root.dataset.theme === "dark") ? "light" : "dark";
    localStorage.setItem(KEY, next);
    applyTheme(next);
  }

  document.addEventListener("click", (e) => {
    const t = e.target?.closest?.("#themeToggle");
    if (t) toggle();
  });

  // Expose (optional) for debugging
  window.ApplyMateTheme = { applyTheme, toggle };
})();