// /static/demo.js
(() => {
  const cvEl = document.getElementById("demoCv");
  const jdEl = document.getElementById("demoJd");
  const runBtn = document.getElementById("demoRun");
  const sampleBtn = document.getElementById("demoSample");
  const statusEl = document.getElementById("demoStatus");

  const tabsWrap = document.getElementById("demoTabs");
  const tabCv = document.getElementById("tab_cv");
  const tabSkills = document.getElementById("tab_skills");
  const tabPlan = document.getElementById("tab_plan");
  const tabInterview = document.getElementById("tab_interview");

  const cvOutEl = document.getElementById("demoCvOut");
  const covPctEl = document.getElementById("covPct");
  const marketPctEl = document.getElementById("marketPct");
  const covFill = document.getElementById("covFill");
  const marketFill = document.getElementById("marketFill");
  const chipsEl = document.getElementById("missingChips");
  const planOutEl = document.getElementById("planOut");
  const interviewOutEl = document.getElementById("interviewOut");

  const traceList = document.getElementById("traceList");
  const traceRaw = document.getElementById("traceRaw");

  if (!cvEl || !jdEl || !runBtn || !sampleBtn) return;

  const SAMPLE_CV =
`Ameer Kashkoush
Technion — Data Science Student

Experience
- Built an AI job-application agent (ApplyMate) that tailors resumes to specific job descriptions and analyzes recruiter emails for intent + next steps.
- Implemented RAG retrieval with vector search and persisted per-application context for repeatable runs.
- Built data pipelines using Python and SQL; worked with large-scale processing concepts (ETL, validation, dashboards).

Skills
Python, SQL, Pandas, basic Spark, Git, REST APIs, statistics, machine learning fundamentals`;

  const SAMPLE_JD =
`Data Analyst Intern — Responsibilities
- Analyze product and marketing data; build dashboards and insights for decision making.
- Write clean SQL and Python to transform and validate data.
- Define metrics, run A/B test analysis, and communicate results to stakeholders.
- Work with data pipelines (ETL) and documentation.

Requirements
- Strong SQL; Python for analytics (Pandas).
- Experience with BI tools (Tableau/Looker) is a plus.
- Familiarity with experimentation, statistics, and clear communication.
- Bonus: Spark, dbt, data modeling`;

  const SKILL_MAP = [
    "sql","python","pandas","spark","tableau","looker","etl","dbt","data modeling",
    "a/b test","experimentation","statistics","dashboards","metrics","stakeholders","git","api"
  ];

  function setStatus(t, kind="muted") {
    statusEl.textContent = t || "";
    statusEl.style.color =
      kind === "ok" ? "var(--ok)" :
      kind === "err" ? "var(--err)" :
      kind === "warn" ? "var(--warn)" : "var(--muted)";
  }

  function esc(s) {
    return String(s || "")
      .replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
  }

  function switchTab(name) {
    const allTabs = tabsWrap.querySelectorAll(".tab");
    allTabs.forEach(b => b.classList.toggle("isActive", b.dataset.tab === name));
    [tabCv, tabSkills, tabPlan, tabInterview].forEach(el => el.classList.add("hidden"));

    if (name === "cv") tabCv.classList.remove("hidden");
    if (name === "skills") tabSkills.classList.remove("hidden");
    if (name === "plan") tabPlan.classList.remove("hidden");
    if (name === "interview") tabInterview.classList.remove("hidden");
  }

  tabsWrap.addEventListener("click", (e) => {
    const btn = e.target.closest(".tab");
    if (!btn) return;
    switchTab(btn.dataset.tab);
  });

  function normalize(s) {
    return String(s || "").toLowerCase();
  }

  function skillScore(cv, jd) {
    const cvN = normalize(cv);
    const jdN = normalize(jd);

    const inJd = SKILL_MAP.filter(k => jdN.includes(k));
    const matched = inJd.filter(k => cvN.includes(k));
    const missing = inJd.filter(k => !cvN.includes(k));

    const coverage = inJd.length ? Math.round((matched.length / inJd.length) * 100) : 0;

    // “Market expectation match” is a slightly different lens:
    // treat the whole map as market expectations and measure CV coverage.
    const marketMatched = SKILL_MAP.filter(k => cvN.includes(k));
    const marketPct = Math.round((marketMatched.length / SKILL_MAP.length) * 100);

    return { coverage, marketPct, missing: missing.slice(0, 10) };
  }

  function renderChips(missing) {
    chipsEl.innerHTML = "";
    if (!missing || missing.length === 0) {
      chipsEl.innerHTML = `<span class="chip">No obvious gaps detected</span>`;
      return;
    }
    missing.forEach(m => {
      const chip = document.createElement("span");
      chip.className = "chip missing";
      chip.textContent = m;
      chipsEl.appendChild(chip);
    });
  }

  function renderPlan(missing) {
    const lines = [
      "• Tighten bullet wording to mirror the JD (metrics, dashboards, stakeholders).",
      "• Add 1–2 impact bullets that mention SQL transformations + validation.",
      "• Include an A/B testing bullet: hypothesis → metric → result.",
    ];

    if (missing.includes("tableau") || missing.includes("looker")) {
      lines.push("• Add a short dashboard project (Tableau/Looker) and mention the KPI you designed.");
    }
    if (missing.includes("dbt")) {
      lines.push("• If relevant: add a small dbt model + tests (even a mini project).");
    }
    if (missing.includes("data modeling")) {
      lines.push("• Add a line about schema design (star schema / normalized tables) if you have it.");
    }

    lines.push("• Outcome loop: if rejected → adjust keywords + add missing-skill evidence → re-apply.");
    planOutEl.innerHTML = lines.map(x => esc(x)).join("<br/>");
  }

  function renderInterviewPrep() {
    const qa = [
      ["Tell me about a data project you built end-to-end.", "Focus on problem → data → method → result → impact."],
      ["How do you validate data pipelines?", "Mention checks: nulls, ranges, schema, row counts, duplicates, sampling."],
      ["How would you analyze an A/B test?", "Define metric + hypothesis, check sample ratio mismatch, compute uplift + CI, communicate tradeoffs."],
      ["Explain a dashboard you built.", "KPI definition, filters, stakeholder needs, iteration cycle."]
    ];

    interviewOutEl.innerHTML =
      qa.map(([q,a]) => `<div style="margin-bottom:12px;"><b>Q:</b> ${esc(q)}<br/><span class="muted"><b>A:</b> ${esc(a)}</span></div>`).join("");
  }

  function renderTrace(steps) {
    traceList.innerHTML = "";
    const fallback = [
      { t:"Analyze", d:"Parse CV + JD, extract role intent and constraints.", m:"~0.6s • low cost" },
      { t:"Retrieve", d:"Pull market-level expectations for the job title.", m:"~1.2s • vector search" },
      { t:"Draft", d:"Rewrite bullets with ATS-aligned wording and measurable impact.", m:"~2.0s • LLM" },
      { t:"Verify", d:"Check keyword coverage + consistency, reduce hallucinations.", m:"~0.9s • LLM" },
      { t:"Finalize", d:"Return tailored CV + action plan.", m:"~0.4s" },
    ];

    const items = (Array.isArray(steps) && steps.length)
      ? steps.slice(0, 8).map((s) => ({
          t: s.module || "Step",
          d: "Executed module with traceable inputs/outputs.",
          m: "logged"
        }))
      : fallback;

    items.forEach(it => {
      const div = document.createElement("div");
      div.className = "traceItem";
      div.innerHTML = `
        <div class="traceItemTop">
          <div class="traceItemTitle">${esc(it.t)}</div>
          <div class="traceItemMeta">${esc(it.m)}</div>
        </div>
        <div class="traceItemDesc">${esc(it.d)}</div>
      `;
      traceList.appendChild(div);
    });

    traceRaw.textContent = Array.isArray(steps) ? JSON.stringify(steps, null, 2) : "";
  }

  async function runDemo() {
    const cv = (cvEl.value || "").trim();
    const jd = (jdEl.value || "").trim();

    if (!cv || !jd) {
      setStatus("Paste CV + JD (or click Use Sample).", "warn");
      return;
    }

    runBtn.disabled = true;
    setStatus("Running…", "muted");

    // Build a RESUME_TAILOR prompt (same format you already use)
    const prompt =
`TASK: RESUME_TAILOR
JOB_TITLE: Data Analyst Intern
CV:
<<<
${cv}
>>>
JOB_DESCRIPTION:
<<<
${jd}
>>>`.trim();

    try {
      const res = await fetch("/api/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
      });

      const raw = await res.text();
      let data;
      try { data = JSON.parse(raw); } catch { data = null; }

      if (!data || data.status !== "ok") {
        setStatus("Backend unavailable — showing polished fallback output.", "warn");
        cvOutEl.innerHTML =
          esc(`• Updated bullets with ATS-aligned phrasing and measurable outcomes.\n• Added SQL + A/B testing evidence.\n• Highlighted dashboards + stakeholder communication.\n\n(Connect backend to see real output.)`);
        renderTrace(null);
      } else {
        setStatus("Done.", "ok");
        cvOutEl.textContent = data.response || "";
        renderTrace(data.steps || []);
      }

      // Render skills / plan / interview regardless (visual demo value)
      const { coverage, marketPct, missing } = skillScore(cv, jd);
      covPctEl.textContent = `${coverage}%`;
      marketPctEl.textContent = `${marketPct}%`;
      covFill.style.width = `${coverage}%`;
      marketFill.style.width = `${marketPct}%`;

      renderChips(missing);
      renderPlan(missing);
      renderInterviewPrep();

    } catch (e) {
      setStatus("Request failed — showing fallback output.", "warn");
      cvOutEl.innerHTML = esc(String(e));
      renderTrace(null);
    } finally {
      runBtn.disabled = false;
    }
  }

  function useSample() {
    cvEl.value = SAMPLE_CV;
    jdEl.value = SAMPLE_JD;
    setStatus("Loaded sample CV/JD.", "ok");
  }

  sampleBtn.addEventListener("click", useSample);
  runBtn.addEventListener("click", runDemo);

  // Init: pretty trace + empty panels
  renderTrace(null);
  renderInterviewPrep();
})();