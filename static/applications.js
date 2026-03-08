const STORAGE_KEY = "applymate_applications_v1";

const listEl = document.getElementById("list");
const searchEl = document.getElementById("search");
const clearAllBtn = document.getElementById("clearAllBtn");

function loadApps() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

function saveApps(apps) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(apps));
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function fmtDate(ts) {
  if (!ts) return "";
  try { return new Date(ts).toLocaleString(); }
  catch { return ""; }
}

function render() {
  const q = (searchEl.value || "").trim().toLowerCase();
  const apps = loadApps();

  const filtered = apps.filter(a => {
    const t = `${a.job_title || ""} ${a.company_name || ""}`.toLowerCase();
    return !q || t.includes(q);
  });

  if (filtered.length === 0) {
    listEl.innerHTML = `
      <div class="empty">
        No saved applications yet.<br/>
        Create one in <a href="/static/resume.html">Resume Tailor</a>.
      </div>
    `;
    return;
  }

  listEl.innerHTML = filtered.map(a => {
    const title = a.job_title || "(job title not set)";
    const company = a.company_name || "(company not set)";
    const id = a.application_id || "";
    const created = fmtDate(a.created_at);

    return `
      <div class="historyItem">
        <div class="historyMain">
          <div class="historyTitle">
            ${escapeHtml(title)} <span class="muted"> @ ${escapeHtml(company)}</span>
          </div>
          <div class="muted small">${escapeHtml(created)}</div>
        </div>

        <div class="historyActions">
          <a class="miniBtn" href="/static/email.html?app=${encodeURIComponent(id)}">Use for Email</a>
          <button class="miniBtn danger" data-del="${escapeHtml(id)}" type="button">Delete</button>
        </div>
      </div>
    `;
  }).join("");

  document.querySelectorAll("button[data-del]").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-del");
      const apps2 = loadApps().filter(a => a.application_id !== id);
      saveApps(apps2);
      render();
    });
  });
}

searchEl.addEventListener("input", render);

clearAllBtn.addEventListener("click", () => {
  if (!confirm("Clear all saved applications on this browser?")) return;
  saveApps([]);
  render();
});

render();