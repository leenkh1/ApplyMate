import re
from typing import Dict, Any, List

from app.core.trace import Trace
from app.llm.llmod_client import LLModClient
from app.storage.role_skills import retrieve_common_role_skills
from app.modules.planner import plan
from app.storage.supabase_store import create_application

from app.modules.reflect import reflect
from app.modules.resume_replan import replan

from app.storage.goodcv_rag import get_best_resume_text_for_jd


OPENING_SENTENCE = "Thank you for providing the relevant information. Below is the analysis explanation:"
STRENGTHS_LINE = "Here are the strengths between your CV and the job description:"
TIPS_LINE = "Here are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:"
COMMON_SKILLS_LINE = "Here are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:"
NOT_AVAILABLE_LINE = "Common skills for this role is Not available"
CV_LINE = "Here is a candidate of a good CV that matches the job description you provided:"

SYSTEM = (
    "You tailor resumes to a job description.\n"
    "Hard rules:\n"
    "1) Use ONLY facts found in the CV text. Do NOT invent companies, dates, skills, projects, or metrics.\n"
    "2) Do NOT ask questions and do NOT offer follow-up help.\n"
    "3) Do NOT add any extra section titles, summaries, checklists, examples, or closing remarks.\n"
    "4) Your answer must end immediately after the common-skills section content (bullets or the Not available line). "
    "The server will append APPLICATION_ID.\n"
    "5) MARKET_COMMON_SKILLS is awareness-only. Never claim the candidate has a skill unless it appears in the CV.\n"
    "6) If MARKET_COMMON_SKILLS is missing, '(Not available)', or if the retrieved skills_list clearly does NOT match the "
    "JOB_TITLE domain (for example: JOB_TITLE is empty or nonsensical, or the top_match role/skills are "
    "for a very different profession), you MUST output the common-skills section as:\n"
    f"{COMMON_SKILLS_LINE}\n"
    f"{NOT_AVAILABLE_LINE}\n"
    "and then STOP.\n\n"
    "OUTPUT FORMAT (MUST FOLLOW EXACTLY):\n"
    f"{OPENING_SENTENCE}\n"
    "\n"
    "Match score: <0-100>/100 - <short explanation>\n"
    "\n"
    f"{STRENGTHS_LINE}\n"
    "- <one or more bullets>\n"
    "- Strengths bullets MUST be direct overlaps with the JD (requirements or nice-to-have).\n"
    "- Each bullet must mention a JD keyword/requirement AND the matching CV fact.\n"
    "- Do NOT list general CV facts (e.g., education, Excel, PowerPoint) unless the JD explicitly asks for them.\n"
    "- If there are zero direct overlaps, output exactly ONE bullet in this section:\n"
    "- No direct strengths were identified between your CV and the job description based on the provided CV text.\n"
    "\n"
    f"{TIPS_LINE}\n"
    "<a prioritized numbered list with as many strong tips as needed>\n"
    "\n"
    f"{COMMON_SKILLS_LINE}\n"
    "- <zero or more skills>\n"
    "\n"
    "Additional constraints:\n"
    "- Strengths must be JD-aligned matches only (CV ∩ JD). If none, use the single 'No direct strengths...' bullet.\n"
    "- The only section headers allowed are EXACTLY these three lines:\n"
    f"  {STRENGTHS_LINE}\n"
    f"  {TIPS_LINE}\n"
    f"  {COMMON_SKILLS_LINE}\n"
    "- For the common-skills bullets: when MARKET_COMMON_SKILLS is valid and clearly in-domain, you may select ONLY those "
    "skill names from MARKET_COMMON_SKILLS.skills_list that are reasonably relevant to the JOB_TITLE and/or JOB_DESCRIPTION "
    "domain (even if they do not appear explicitly in the CV or JD) and skip clearly unrelated or overly niche items. "
    "Do NOT add any skills that are not from MARKET_COMMON_SKILLS.skills_list and do NOT rename skill names.\n"
    "In the tips section, you may briefly suggest de-emphasizing or removing CV items that are clearly unrelated to the"
    " JD (e.g., unrelated hobbies), but only if those items explicitly appear in the CV text."
    "- If REVISION_INSTRUCTIONS is provided, revise your previous output accordingly while keeping this exact structure.\n"
)


def _compact(s: str, max_chars: int = 900) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s[:max_chars] + ("…" if len(s) > max_chars else "")


def _build_market_block(pine: Dict[str, Any]) -> str:
    if not pine.get("matches"):
        return "\n\nMARKET_COMMON_SKILLS:\n(Not available)\n"

    seen = set()
    market: List[str] = []
    for match in pine["matches"]:
        for s in (match.get("skills_top", "") or "").split(","):
            t = s.strip()
            if not t:
                continue
            k = t.lower()
            if k not in seen:
                seen.add(k)
                market.append(t)
            if len(market) >= 25:
                break
        if len(market) >= 25:
            break

    top = pine["matches"][0]
    return (
        "\n\nMARKET_COMMON_SKILLS:\n"
        f"- query_title: {pine.get('query_title','')}\n"
        f"- top_match: {top.get('job_title')} (score={top.get('score'):.3f}, n_posts={top.get('n_posts')})\n"
        f"- skills_list: {', '.join(market)}\n"
    )


def _cut_followup_offers(text: str) -> str:
    t = text or ""
    patterns = [
        r"\nIf you['’]d like.*\Z",
        r"\nIf you['’]d want.*\Z",
        r"\nIf you want.*\Z",
    ]
    for pat in patterns:
        t = re.sub(pat, "", t, flags=re.IGNORECASE | re.DOTALL)
    return t.strip()


def _build_revision_instructions(*, executor_instructions: str, preserve: List[str]) -> str:
    lines: List[str] = []
    if preserve:
        lines.append("PRESERVE:")
        lines.extend([f"- {p}" for p in preserve[:5]])
    if executor_instructions.strip():
        lines.append(executor_instructions.strip())
    return "\n".join(lines).strip()


async def run(prompt: str, trace: Trace) -> str:
    p = await plan(prompt, trace)

    job_title = (p.get("job_title") or "").strip()
    cv_text = (p.get("cv_text") or "").strip()
    jd_text = (p.get("jd_text") or "").strip()
    task_list = p.get("task_list") or []

    if not job_title:
        return (
            "Missing JOB_TITLE.\n"
            "Please add a line like:\n"
            "JOB_TITLE: Data Scientist\n"
            "Then include CV and JOB_DESCRIPTION."
        )
    if not cv_text or not jd_text:
        return (
            "Missing CV or JOB_DESCRIPTION.\n"
            "Please provide:\n"
            "CV: <<< ... >>>\n"
            "JOB_DESCRIPTION: <<< ... >>>"
        )

    pine = await retrieve_common_role_skills(job_title, top_k=5)
    market_block = _build_market_block(pine)

    task_block = ""
    if task_list:
        task_block = "TASK_LIST:\n" + "\n".join([f"- {t}" for t in task_list[:7]]) + "\n\n"

    user_payload = (
        "TASK: RESUME_TAILOR\n"
        + task_block
        + f"JOB_TITLE: {job_title}\n"
        "CV:\n<<<\n" + cv_text + "\n>>>\n"
        "JOB_DESCRIPTION:\n<<<\n" + jd_text + "\n>>>\n"
        + market_block
    )

    context_hint = (
        f"JOB_TITLE: {job_title}\n"
        f"CV_SNIPPET: {_compact(cv_text, 500)}\n"
        f"JD_SNIPPET: {_compact(jd_text, 500)}\n"
        "FORMAT_REMINDER: Use the fixed headers/lines exactly; end after common skills.\n"
    )

    llm = LLModClient()

    # 1) Executor draft
    draft = await llm.chat(
        module="Executor LLM",
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_payload}],
        trace=trace,
    )
    draft = _cut_followup_offers(draft)

    # 2) Replan judge+decide
    rp1 = await replan(
        task_kind="RESUME_TAILOR",
        context_hint=context_hint,
        draft=draft,
        reflection=None,
        trace=trace,
    )
    if rp1.get("is_solved") and (rp1.get("final_response") or "").strip():
        final_text = _cut_followup_offers(rp1["final_response"])
    else:
        # Repair path (max one iteration)
        if rp1.get("needs_reflect"):
            refl = await reflect(
                task_kind="RESUME_TAILOR",
                context_hint=context_hint,
                draft=draft,
                trace=trace,
            )
            rp2 = await replan(
                task_kind="RESUME_TAILOR",
                context_hint=context_hint,
                draft=draft,
                reflection=refl,
                trace=trace,
            )
            rev = _build_revision_instructions(
                executor_instructions=rp2.get("executor_instructions", ""),
                preserve=rp2.get("preserve", []) or [],
            )
        else:
            rev = _build_revision_instructions(
                executor_instructions=rp1.get("executor_instructions", ""),
                preserve=rp1.get("preserve", []) or [],
            )
        if not rev.strip():
            rev = "Revise the draft to satisfy the SYSTEM rules and required format exactly."

        revised_payload = user_payload + "\nREVISION_INSTRUCTIONS:\n<<<\n" + rev + "\n>>>\n"
        repaired = await llm.chat(
            module="Executor LLM",
            messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": revised_payload}],
            trace=trace,
        )
        repaired = _cut_followup_offers(repaired)

        # Finalize, stop
        rp_final = await replan(
            task_kind="RESUME_TAILOR",
            context_hint=context_hint,
            draft=repaired,
            reflection=None,
            trace=trace,
        )
        final_text = _cut_followup_offers((rp_final.get("final_response") or "").strip()) or repaired.strip()

    # Retrieve best-matching example CV via RAG on GoodCV namespace
    example_block = ""
    try:
        best_cv_text = await get_best_resume_text_for_jd(jd_text, job_title=job_title)
        if best_cv_text:
            example_block = (
                f"\n\n{CV_LINE}\n"
                "<<<\n"
                f"{best_cv_text}\n"
                ">>>\n"
            )
    except Exception:
        # Fail silently; do not break main flow if RAG fails
        example_block = ""

    # Store context in Supabase and append application_id into the response string,
    # then separate the example CV with a dashed line if present.
    try:
        app_id = await create_application(job_title=job_title, jd_text=jd_text, cv_text=cv_text)
        base = f"{final_text}\n\nAPPLICATION_ID: {app_id}"
        if example_block:
            base += "\n---------------------------------------------------------------------------------------------------------------" + example_block
        return base
    except Exception as e:
        base = f"{final_text}\n\nAPPLICATION_ID: not_created\nSUPABASE_ERROR: {str(e)}"
        if example_block:
            base += "\n---------------------------------------------------------------------------------------------------------------" + example_block
        return base