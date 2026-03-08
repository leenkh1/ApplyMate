// ===== Email Reply Page Logic =====

const STORAGE_KEY = "applymate_applications_v1";

// Cache appId validation per browser session (so we don't probe repeatedly)
const SESSION_VALID_KEY = "applymate_valid_appids_v1"; // JSON: { [appId]: true|false }

const appSelectEl = document.getElementById("appSelect");
const noAppsEl = document.getElementById("noApps");

const emailSubjectEl = document.getElementById("emailSubject");
const emailTextEl = document.getElementById("emailText");
const promptEl = document.getElementById("prompt");

const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");
const statusEl = document.getElementById("status");

const finalEl = document.getElementById("finalResponse");
const stepsEl = document.getElementById("steps");

const copyFinalBtn = document.getElementById("copyFinalBtn");
const expandAllBtn = document.getElementById("expandAllBtn");
const collapseAllBtn = document.getElementById("collapseAllBtn");

// ----- Storage helpers -----
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

function loadSessionValidationMap() {
  try {
    const raw = sessionStorage.getItem(SESSION_VALID_KEY);
    if (!raw) return {};
    const obj = JSON.parse(raw);
    return (obj && typeof obj === "object") ? obj : {};
  } catch {
    return {};
  }
}

function saveSessionValidationMap(map) {
  try {
    sessionStorage.setItem(SESSION_VALID_KEY, JSON.stringify(map || {}));
  } catch {}
}

// ----- UI helpers -----
function setStatus(text, kind = "info") {
  statusEl.className = `status ${kind}`;
  statusEl.textContent = text || "";
}

function pretty(x) {
  try { return JSON.stringify(x, null, 2); }
  catch { return String(x); }
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function copyText(text) {
  const t = (text || "").trim();
  if (!t) return;
  try {
    await navigator.clipboard.writeText(t);
    setStatus("Copied.", "ok");
  } catch {
    setStatus("Copy failed (browser permission).", "error");
  }
}

// Steps renderer
function renderSteps(steps) {
  stepsEl.innerHTML = "";

  if (!steps || steps.length === 0) {
    stepsEl.innerHTML = `<div class="empty">No steps for this run.</div>`;
    return;
  }

  steps.forEach((s, idx) => {
    const module = s.module ?? "";
    const promptJson = pretty(s.prompt ?? {});
    const responseJson = pretty(s.response ?? {});

    const card = document.createElement("div");
    card.className = "stepCard";
    card.innerHTML = `
      <details class="stepDetails">
        <summary class="stepSummary">
          <div class="stepLeft">
            <span class="pill">Step ${idx + 1}</span>
            <span class="module">${escapeHtml(module)}</span>
          </div>
          <span class="chev">Details</span>
        </summary>

        <div class="stepBody">
          <details class="tech">
            <summary>Prompt / Response (JSON)</summary>
            <div class="twoCol">
              <div class="panel">
                <div class="panelHead">
                  <div class="panelTitle">Prompt</div>
                  <button class="mini secondary" type="button" data-copy="prompt">Copy</button>
                </div>
                <pre class="code">${escapeHtml(promptJson)}</pre>
              </div>

              <div class="panel">
                <div class="panelHead">
                  <div class="panelTitle">Response</div>
                  <button class="mini secondary" type="button" data-copy="response">Copy</button>
                </div>
                <pre class="code">${escapeHtml(responseJson)}</pre>
              </div>
            </div>
          </details>
        </div>
      </details>
    `;

    const copyPromptBtn = card.querySelector('button[data-copy="prompt"]');
    const copyRespBtn = card.querySelector('button[data-copy="response"]');
    copyPromptBtn?.addEventListener("click", () => copyText(promptJson));
    copyRespBtn?.addEventListener("click", () => copyText(responseJson));

    stepsEl.appendChild(card);
  });
}

function populateDropdown(apps) {
  appSelectEl.innerHTML = "";

  if (!apps || apps.length === 0) {
    noAppsEl.classList.remove("hidden");
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No applications saved";
    appSelectEl.appendChild(opt);
    appSelectEl.disabled = true;
    return;
  }

  noAppsEl.classList.add("hidden");
  appSelectEl.disabled = false;

  const opt0 = document.createElement("option");
  opt0.value = "";
  opt0.textContent = "Select an application…";
  appSelectEl.appendChild(opt0);

  for (const a of apps) {
    const id = (a.application_id || "").trim();
    const title = a.job_title || "(job title)";
    const company = a.company_name || "(company)";
    const when = a.created_at ? new Date(a.created_at).toLocaleDateString() : "";

    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = `${title} @ ${company}${when ? " • " + when : ""}`;
    appSelectEl.appendChild(opt);
  }
}

function getSelectedAppId() {
  return (appSelectEl.value || "").trim();
}

function buildEmailPrompt(appId) {
  const subject = (emailSubjectEl.value || "").trim();
  const email = (emailTextEl.value || "").trim();

  const fullEmail = subject ? `Subject: ${subject}\n\n${email}` : email;

  return (
`TASK: EMAIL_ANALYZE
APPLICATION_ID: ${appId}
EMAIL:
<<<
${fullEmail}
>>>`
  ).trim();
}

function syncPrompt() {
  if (!promptEl) return;
  const appId = getSelectedAppId();
  promptEl.value = appId ? buildEmailPrompt(appId) : "";
}

// ----- Validation: ensure backend loads CV/JD for this APPLICATION_ID -----
function detectEmptyCvJdFromSteps(steps) {
  // We look at the logged JSON (steps include the payload sent to the LLM).
  // In email_flow.py the user payload contains:
  // CV:\n<<<\n{cv_text}\n>>>\n
  // JOB_DESCRIPTION:\n<<<\n{jd_text}\n>>>\n
  // Empty values will show as <<<\n\n>>> patterns.
  const joined = JSON.stringify(steps || []).toLowerCase();

  const cvEmpty =
    joined.includes("cv:\\n<<<\\n\\n>>>") ||
    joined.includes("cv:\\n<<<\\n>>>");

  const jdEmpty =
    joined.includes("job_description:\\n<<<\\n\\n>>>") ||
    joined.includes("job_description:\\n<<<\\n>>>");

  // If either is empty, it's not safe.
  return (cvEmpty || jdEmpty);
}

async function probeApplicationHasContext(appId) {
  // One-time probe that asks the backend to run EMAIL_ANALYZE with a tiny email.
  // If CV/JD can't be loaded from Supabase, they appear empty in steps trace.
  const probePrompt =
`TASK: EMAIL_ANALYZE
APPLICATION_ID: ${appId}
EMAIL:
<<<
probe
>>>`.trim();

  const res = await fetch("/api/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: probePrompt })
  });

  const raw = await res.text();
  let data;
  try { data = JSON.parse(raw); }
  catch { return { ok: false, reason: "Server returned non-JSON response" }; }

  if (data.status !== "ok") {
    return { ok: false, reason: data.error || "Unknown backend error" };
  }

  const steps = Array.isArray(data.steps) ? data.steps : [];
  const empty = detectEmptyCvJdFromSteps(steps);

  if (empty) {
    return {
      ok: false,
      reason: "CV/JD were not loaded for this APPLICATION_ID (stale ID or missing Supabase data)."
    };
  }

  return { ok: true };
}

async function ensureValidApplication(appId) {
  const map = loadSessionValidationMap();
  if (map[appId] === true) return { ok: true };
  if (map[appId] === false) {
    return { ok: false, reason: "Previously detected missing CV/JD for this ID in this session." };
  }

  setStatus("Validating application context (CV/JD)…", "info");
  const v = await probeApplicationHasContext(appId);

  map[appId] = !!v.ok;
  saveSessionValidationMap(map);

  return v;
}

async function runAgent() {
  const appId = getSelectedAppId();

  if (!appId) {
    setStatus("Please choose an application first (create one in Resume Tailor).", "error");
    return;
  }
  if (!emailTextEl.value.trim()) {
    setStatus("Please paste the recruiter email.", "error");
    return;
  }

  // Validate appId has CV/JD available (from Supabase) before running the real request
  runBtn.disabled = true;
  const validation = await ensureValidApplication(appId);
  if (!validation.ok) {
    runBtn.disabled = false;
    setStatus(
      `${validation.reason}\nFix: go to Resume Tailor and run again to generate a fresh APPLICATION_ID.`,
      "error"
    );
    return;
  }

  const prompt = (promptEl?.value || "").trim();
  if (!prompt) {
    runBtn.disabled = false;
    setStatus("Prompt is empty.", "error");
    return;
  }

  setStatus("Running…", "info");
  finalEl.textContent = "";
  stepsEl.innerHTML = "";

  try {
    const res = await fetch("/api/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });

    const raw = await res.text();
    let data;
    try { data = JSON.parse(raw); }
    catch { data = { status: "error", error: raw || `HTTP ${res.status}`, steps: [], response: null }; }

    if (data.status !== "ok") {
      setStatus(data.error || "Unknown error", "error");
      renderSteps(data.steps || []);
      return;
    }

    setStatus("Done.", "ok");
    finalEl.textContent = data.response || "";
    renderSteps(data.steps || []);
  } catch (e) {
    setStatus(`Request failed: ${e}`, "error");
  } finally {
    runBtn.disabled = false;
  }
}

function clearAll() {
  emailSubjectEl.value = "";
  emailTextEl.value = "";
  if (promptEl) promptEl.value = "";

  finalEl.textContent = "";
  stepsEl.innerHTML = "";
  setStatus("");

  syncPrompt();
}

// ----- Events -----
[emailSubjectEl, emailTextEl].forEach(el => {
  el.addEventListener("input", syncPrompt);
});
appSelectEl.addEventListener("change", syncPrompt);

runBtn.addEventListener("click", runAgent);
clearBtn.addEventListener("click", clearAll);

copyFinalBtn.addEventListener("click", () => copyText(finalEl.textContent || ""));

expandAllBtn.addEventListener("click", () => {
  document.querySelectorAll("#steps details.stepDetails").forEach(d => d.open = true);
});
collapseAllBtn.addEventListener("click", () => {
  document.querySelectorAll("#steps details.stepDetails").forEach(d => d.open = false);
});

// Ctrl/Cmd+Enter runs (when focused inside input/textarea)
document.addEventListener("keydown", (e) => {
  const isRun = (e.ctrlKey || e.metaKey) && e.key === "Enter";
  if (!isRun) return;

  const tag = (document.activeElement?.tagName || "").toLowerCase();
  if (tag === "textarea" || tag === "input") {
    e.preventDefault();
    runAgent();
  }
});

// --- Sample email helper ---
const sampleEmailBtn = document.getElementById("sampleEmailBtn");
function useSampleEmail() {
  emailSubjectEl.value = "Interview Invitation — Next Steps";
  emailTextEl.value =
`Hi Ameer,
Thanks for applying. We'd like to invite you to a 30-minute interview this week.
Please share your availability and confirm you can do a short SQL exercise.
Best,
Recruiting Team`;
  syncPrompt();
  setStatus("Loaded sample email.", "ok");
}
sampleEmailBtn?.addEventListener("click", useSampleEmail);


// ----- Init -----
const apps = loadApps();
populateDropdown(apps);

// If opened from applications list: /static/email.html?app=<id>
const params = new URLSearchParams(window.location.search);
const preselect = params.get("app");
if (preselect) {
  appSelectEl.value = preselect;
}

syncPrompt();