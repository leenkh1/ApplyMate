// ===== Resume Tailor Page Logic (Premium UI v2) =====

const companyNameEl = document.getElementById("companyName");
const jobTitleEl = document.getElementById("jobTitle");
const cvTextEl = document.getElementById("cvText");
const jdTextEl = document.getElementById("jdText");

const promptEl = document.getElementById("prompt");

const runBtn = document.getElementById("runBtn");
const clearBtn = document.getElementById("clearBtn");
const sampleBtn = document.getElementById("sampleBtn");
const statusEl = document.getElementById("status");

const finalEl = document.getElementById("finalResponse");
const stepsEl = document.getElementById("steps");

const copyFinalBtn = document.getElementById("copyFinalBtn");
const expandAllBtn = document.getElementById("expandAllBtn");
const collapseAllBtn = document.getElementById("collapseAllBtn");

const appSavedBanner = document.getElementById("appSavedBanner");
const savedAppMeta = document.getElementById("savedAppMeta");

// ----- Storage helpers -----
const STORAGE_KEY = "applymate_applications_v1";

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

function upsertApp(app) {
  const apps = loadApps();
  const idx = apps.findIndex(a => a.application_id === app.application_id);
  if (idx >= 0) apps[idx] = { ...apps[idx], ...app };
  else apps.push(app);

  apps.sort((a, b) => (b.created_at || 0) - (a.created_at || 0));
  saveApps(apps);
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

function buildResumePrompt() {
  const jobTitle = (jobTitleEl.value || "").trim();
  const cv = (cvTextEl.value || "").trim();
  const jd = (jdTextEl.value || "").trim();

  return (
`TASK: RESUME_TAILOR
JOB_TITLE: ${jobTitle}
CV:
<<<
${cv}
>>>
JOB_DESCRIPTION:
<<<
${jd}
>>>`
  ).trim();
}

function syncPromptFromFields() {
  if (!promptEl) return;
  promptEl.value = buildResumePrompt();
}

function extractApplicationId(text) {
  const m = String(text).match(/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/);
  return m ? m[0] : null;
}

// Steps renderer (course requirement)
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

    card.querySelector('button[data-copy="prompt"]')
      ?.addEventListener("click", () => copyText(promptJson));
    card.querySelector('button[data-copy="response"]')
      ?.addEventListener("click", () => copyText(responseJson));

    stepsEl.appendChild(card);
  });
}

async function runAgent() {
  const company = (companyNameEl.value || "").trim();
  const jobTitle = (jobTitleEl.value || "").trim();
  const prompt = (promptEl?.value || "").trim();

  if (!jobTitle) {
    setStatus("Please enter a job title.", "error");
    return;
  }
  if (!prompt) {
    setStatus("Please fill CV and job description.", "error");
    return;
  }

  runBtn.disabled = true;
  appSavedBanner.classList.add("hidden");
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

    const appId = extractApplicationId(data.response || "");
    if (appId) {
      upsertApp({
        application_id: appId,
        company_name: company || "(company not set)",
        job_title: jobTitle,
        created_at: Date.now()
      });

      savedAppMeta.textContent = ` • ${jobTitle} @ ${company || "(company not set)"} • ${appId}`;
      appSavedBanner.classList.remove("hidden");
    } else {
      setStatus("Done. (No APPLICATION_ID found — cannot reuse context for email.)", "info");
    }

  } catch (e) {
    setStatus(`Request failed: ${e}`, "error");
  } finally {
    runBtn.disabled = false;
  }
}

function useSample() {
  companyNameEl.value = "ExampleCo";
  jobTitleEl.value = "Data Analyst Intern";
  cvTextEl.value =
`Data Science Student (Technion)
- Built ApplyMate: an AI agent that tailors resumes to JDs and analyzes recruiter emails (intent, actions, deadlines).
- Implemented retrieval + structured prompting with full step tracing for transparency.
Skills: Python, SQL, Pandas, basic Spark, Git, stats`;

  jdTextEl.value =
`Responsibilities: SQL analysis, dashboards, A/B testing, metrics, stakeholder communication.
Requirements: strong SQL, Python (Pandas), BI tools (Tableau/Looker) a plus; ETL experience; bonus Spark/dbt.`;

  syncPromptFromFields();
  setStatus("Loaded sample CV/JD.", "ok");
}

function clearAll() {
  companyNameEl.value = "";
  jobTitleEl.value = "";
  cvTextEl.value = "";
  jdTextEl.value = "";
  if (promptEl) promptEl.value = "";

  finalEl.textContent = "";
  stepsEl.innerHTML = "";
  appSavedBanner.classList.add("hidden");
  setStatus("");

  syncPromptFromFields();
}

// ----- Events -----
[companyNameEl, jobTitleEl, cvTextEl, jdTextEl].forEach(el => {
  el.addEventListener("input", syncPromptFromFields);
});

runBtn.addEventListener("click", runAgent);
clearBtn.addEventListener("click", clearAll);
sampleBtn?.addEventListener("click", useSample);

copyFinalBtn.addEventListener("click", () => copyText(finalEl.textContent || ""));

expandAllBtn.addEventListener("click", () => {
  document.querySelectorAll("#steps details.stepDetails").forEach(d => d.open = true);
});
collapseAllBtn.addEventListener("click", () => {
  document.querySelectorAll("#steps details.stepDetails").forEach(d => d.open = false);
});

// Ctrl/Cmd+Enter runs
document.addEventListener("keydown", (e) => {
  const isRun = (e.ctrlKey || e.metaKey) && e.key === "Enter";
  if (!isRun) return;

  const tag = (document.activeElement?.tagName || "").toLowerCase();
  if (tag === "textarea" || tag === "input") {
    e.preventDefault();
    runAgent();
  }
});

// Init
syncPromptFromFields();