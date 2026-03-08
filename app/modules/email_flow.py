# app/modules/email_flow.py
import re
from typing import List
from app.core.trace import Trace
from app.llm.llmod_client import LLModClient
from app.modules.planner import plan
from app.modules.reflect import reflect
from app.modules.email_replan import replan
from app.storage.role_skills import retrieve_common_role_skills, parse_skills_top
from app.storage.supabase_store import get_application, add_email
from app.storage.interview_links import match_prep_links
from app.storage.hr_rag import retrieve_hr_questions

REJ_L1 = "We are sorry to hear that you got rejected."
SUG_L2 = (
    "Confirm if you have the following commonly requested skills for this role "
    "(or consider developing them for future applications):"
)
SUG_NEXT = "Here are the next steps:"
SUG_REPLY = "Here is an example reply you can adapt:"

SYSTEM = (
    "You analyze recruiter emails within a single job-application context.\n"
    "You will be given JOB_TITLE, CV, JOB_DESCRIPTION, EMAIL, and sometimes extra retrieval blocks.\n\n"
    "First, detect email_intent as one of: rejection | Interview invitation | Request for info | Follow up | Other.\n"
    "Then follow EXACTLY ONE format below.\n\n"
    "FORMAT 1 — Non-rejection only:\n"
    "Use this format ONLY if email_intent is Interview invitation, Request for info, Follow up, or Other.\n"
    "Return EXACTLY these sections in this EXACT order:\n"
    "1) Email Intent:\n"
    "\n"
    "2) Required Actions:\n"
    "   - bullets only\n"
    "\n"
    f"3) {SUG_NEXT} (bullets; context-aware using JD+CV, but do not invent facts)\n"
    "   - Provide bullets.\n"
    "\n"
    f"4) {SUG_REPLY}\n"
    "   - short and professional\n"
    "   - this is an example reply the user can adapt\n"
    "   - Do not include Application ID\n"
    "   - must directly address the recruiter’s request when possible\n"
    "   - if the recruiter asks for availability, you may include a short illustrative availability reply with plausible sample time slots\n"
        
    "IMPORTANT NOTE: If email_intent is Interview invitation, apply these rules inside next_steps only:\n"
    "- Use INTERVIEW_TYPE provided in the prompt (technical | hr | unclear). Do not guess a different type.\n"
    "- If INTERVIEW_TYPE is technical and TECH_PREP_LINKS is provided, include those links as bullet points.\n"
    "- If INTERVIEW_TYPE is hr and HR_SCREENING_RAG is provided, include 3-5 likely HR questions with brief answer guidance as bullet points.\n"
    "- If INTERVIEW_TYPE is unclear, focus first on clarifying the interview format, duration, platform, and expectations; keep any prep advice broad and role-relevant.\n"
    
    "FORMAT 2 — Rejection:\n"
    "Use this format ONLY if email_intent is rejection.\n"
    "Return EXACTLY these sections in this EXACT order:\n"
    f"A) {REJ_L1}\n\n"
    "B) If MARKET_COMMON_SKILLS is provided and MARKET_COMMON_SKILLS.skills_list is non-empty, then output exactly this line:\n"
    f"{SUG_L2}\n"
    "C) Only if line B is shown, list the skills as bullets (skill names only).\n"
    "   - Use only skill names from MARKET_COMMON_SKILLS.skills_list.\n"
    "   - You may include only the skills that are reasonably relevant to the JOB_TITLE and/or JOB_DESCRIPTION domain, and skip unrelated or overly niche items.\n"
    "   - Do not add, expand, normalize, or rename skills, and do not claim the candidate lacks them.\n"
    "   - If MARKET_COMMON_SKILLS is missing, empty, or skills_list is empty, omit both line B and the skill bullets entirely.\n\n"
    f"D) {SUG_NEXT}\n"
    "   - Provide bullets.\n\n"
    f"E) {SUG_REPLY}\n"
    "   - Provide the reply text.\n"
    "   - Do not include Application ID\n"
    "Do NOT output Email Intent, Required Actions, numbering, or any extra label.\n\n"
)

REJECTION_MARKERS = [
    "unfortunately",
    "we regret",
    "not moving forward",
    "not to move forward",
    "move forward with other candidates",
    "proceed with other candidates",
    "proceeding with other candidates",
    "not selected",
    "position has been filled",
    "we won't be moving forward",
    "we will not be moving forward",
]

INVITE_MARKERS = [
    "interview invitation",
    "invite you to interview",
    "invite you for an interview",
    "schedule an interview",
    "interview next",
    "phone screen",
    "screening call",
    "interview call",
]

TECH_MARKERS = [
    "technical", "coding", "leetcode", "hackerrank", "codility", "take-home", "take home",
    "assignment", "pair programming", "system design", "live coding",
]

HR_MARKERS = [
    "hr", "recruiter screen", "talent acquisition", "people team", "behavioral", "culture",
    "values", "non-technical", "introduction call",
]


def looks_like_rejection(email_text: str) -> bool:
    t = (email_text or "").lower()
    return any(m in t for m in REJECTION_MARKERS)


def looks_like_invite(email_text: str) -> bool:
    t = (email_text or "").lower()
    return any(m in t for m in INVITE_MARKERS) or ("interview" in t and "invite" in t)


def detect_interview_type(email_text: str) -> str:
    t = (email_text or "").lower()
    tech = sum(1 for m in TECH_MARKERS if m in t)
    hr = sum(1 for m in HR_MARKERS if m in t)
    if tech > hr and tech > 0:
        return "technical"
    if hr > tech and hr > 0:
        return "hr"
    return "unclear"


def _compact(s: str, max_chars: int = 260) -> str:
    s = (s or "").strip().replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_chars] + ("…" if len(s) > max_chars else "")


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

    application_id = (p.get("application_id") or "").strip()
    job_title = (p.get("job_title") or "").strip()
    cv_text = (p.get("cv_text") or "").strip()
    jd_text = (p.get("jd_text") or "").strip()
    email_text = (p.get("email_text") or "").strip()

    if not email_text:
        email_text = prompt.strip()

    # If application_id provided, fetch stored context and fill missing fields
    if application_id:
        try:
            ctx = await get_application(application_id=application_id)
            if ctx:
                job_title = job_title or (ctx.get("job_title") or "").strip()
                cv_text = cv_text or (ctx.get("cv_text") or "").strip()
                jd_text = jd_text or (ctx.get("jd_text") or "").strip()
        except Exception:
            pass

        try:
            await add_email(application_id=application_id, email_text=email_text)
        except Exception:
            pass

    # --- Rejection: add market skills block (prompt-only, not shown as a section) ---
    market_block = ""
    expect_rejection_special = False
    market_hint_block = ""
    if looks_like_rejection(email_text) and job_title:
        try:
            market = await retrieve_common_role_skills(job_title, top_k=3)
            top = (market.get("matches") or [None])[0]
            if top and top.get("skills_top"):
                skills_list = parse_skills_top(top["skills_top"], limit=25)
                market_block = (
                    "\nMARKET_COMMON_SKILLS:\n"
                    f"- query_title: {market.get('query_title', '')}\n"
                    f"- top_match: {top.get('job_title', '')} "
                    f"(score={top.get('score', 0):.3f}, n_posts={top.get('n_posts', 0)})\n"
                    f"- skills_list: {', '.join(skills_list)}\n"
                )
                market_hint_block = (
                    "MARKET_COMMON_SKILLS:\n"
                    f"- skills_list: {', '.join(skills_list)}\n"
                )
                expect_rejection_special = True
        except Exception:
            market_block = ""
            market_hint_block = ""
            expect_rejection_special = False

    # --- Interview invitation: determine type + attach resources blocks ---
    interview_type = "unclear"
    tech_links_block = ""
    hr_rag_block = ""

    if looks_like_invite(email_text) and not looks_like_rejection(email_text):
        interview_type = detect_interview_type(email_text)

        if interview_type == "technical":
            links = await match_prep_links(job_title, max_links=3)
            if links:
                tech_links_block = "\nTECH_PREP_LINKS:\n" + "\n".join([f"- {u}" for u in links]) + "\n"

        elif interview_type == "hr":
            try:
                hr_hits = await retrieve_hr_questions(job_title, top_k=5)
                if hr_hits:
                    lines = ["\nHR_SCREENING_RAG:"]
                    for h in hr_hits[:5]:
                        q = _compact(h.get("question", ""), 220)
                        a = _compact(h.get("ideal_answer", ""), 260)
                        lines.append(f"- Q: {q}")
                        lines.append(f"  Guidance: {a}")
                    hr_rag_block = "\n".join(lines) + "\n"
            except Exception:
                hr_rag_block = ""

    user_payload = (
        "TASK: EMAIL_ANALYZE\n"
        + (f"APPLICATION_ID: {application_id}\n" if application_id else "")
        + f"JOB_TITLE: {job_title}\n"
        f"INTERVIEW_TYPE: {interview_type}\n"
        "CV:\n<<<\n" + cv_text + "\n>>>\n"
        "JOB_DESCRIPTION:\n<<<\n" + jd_text + "\n>>>\n"
        "EMAIL:\n<<<\n" + email_text + "\n>>>\n"
        + market_block
        + tech_links_block
        + hr_rag_block
    )

    has_tech_links = bool(tech_links_block.strip())
    has_hr_rag = bool(hr_rag_block.strip())

    links_for_hint = ""
    if tech_links_block.strip():
        links_for_hint = tech_links_block.strip()

    context_hint = (
            f"APPLICATION_ID: {application_id}\n"
            f"JOB_TITLE: {job_title}\n"
            f"INTERVIEW_TYPE: {interview_type}\n"
            f"HAS_TECH_PREP_LINKS: {has_tech_links}\n"
            f"HAS_HR_SCREENING_RAG: {has_hr_rag}\n"
            f"TECH_PREP_LINKS_BLOCK:\n{links_for_hint}\n"
            f"CV_SNIPPET: {_compact(cv_text, 500)}\n"
            f"JD_SNIPPET: {_compact(jd_text, 500)}\n"
            f"EMAIL_SNIPPET: {_compact(email_text, 500)}\n"
            f"EXPECT_REJECTION_SPECIAL: {expect_rejection_special}\n"
            + (market_hint_block if market_hint_block else "")
            + "SUGGESTED_REPLY_IS_EXAMPLE: True\n"
    )

    llm = LLModClient()

    # 1) Executor draft
    draft = await llm.chat(
        module="Executor LLM",
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_payload}],
        trace=trace,
    )
    draft = (draft or "").strip()

    # 2) Replan judge+decide
    rp1 = await replan(
        task_kind="EMAIL_ANALYZE",
        context_hint=context_hint,
        draft=draft,
        reflection=None,
        trace=trace,
    )
    if rp1.get("is_solved") and (rp1.get("final_response") or "").strip():
        return (rp1.get("final_response") or "").strip()

    # 3) Repair path (max one iteration)
    if rp1.get("needs_reflect"):
        refl = await reflect(
            task_kind="EMAIL_ANALYZE",
            context_hint=context_hint,
            draft=draft,
            trace=trace,
        )
        rp2 = await replan(
            task_kind="EMAIL_ANALYZE",
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
    repaired = (repaired or "").strip()

    # 4) Finalize
    rp_final = await replan(
        task_kind="EMAIL_ANALYZE",
        context_hint=context_hint,
        draft=repaired,
        reflection=None,
        trace=trace,
    )
    return (rp_final.get("final_response") or "").strip() or repaired