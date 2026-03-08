import json
from typing import Any, Dict, List, Optional

from app.core.trace import Trace
from app.llm.llmod_client import LLModClient


REJ_L1 = "We are sorry to hear that you got rejected."
SUG_L2 = (
    "Confirm if you have the following commonly requested skills for this role "
    "(or consider developing them for future applications):"
)
SUG_NEXT = "Here are the next steps:"
SUG_REPLY = "Here is an example reply you can adapt:"


REPLAN_SYSTEM = (
    "You are the Replan LLM.\n"
    "Decide whether the email-analysis draft can be finalized or must be revised.\n"
    "Return ONLY valid JSON with these keys:\n"
    "{\n"
    '  "is_solved": true|false,\n'
    '  "needs_reflect": true|false,\n'
    '  "rationale": string,\n'
    '  "preserve": [string, ...],\n'
    '  "executor_instructions": string,\n'
    '  "final_response": string\n'
    "}\n\n"
    "Check the draft against EXACTLY ONE expected format.\n\n"
    "FORMAT 1 — Non-rejection:\n"
    "Required sections in this EXACT order:\n"
    "1) Email Intent\n"
    "2) Required Actions\n"
    f"3) {SUG_NEXT}\n"
    f"4) {SUG_REPLY}\n"
    "Rules:\n"
    "- Email Intent must indicate one of: Interview invitation | Request for info | Follow up | Other.\n"
    "- If and ONLY if Email Intent is exactly 'Interview invitation':\n"
    "  - Use INTERVIEW_TYPE from CONTEXT_HINT.\n"
    f"  - If INTERVIEW_TYPE is technical AND CONTEXT_HINT has HAS_TECH_PREP_LINKS: True, then {SUG_NEXT} MUST include the URLs listed in TECH_PREP_LINKS_BLOCK as bullet items.\n"
    "  - If any URL from TECH_PREP_LINKS_BLOCK is missing from next steps, set is_solved=false.\n"
    f"  - If INTERVIEW_TYPE is hr AND CONTEXT_HINT has HAS_HR_SCREENING_RAG: True, then {SUG_NEXT} MUST include 3–5 likely HR questions with brief answer-structure guidance.\n"
    "  - If INTERVIEW_TYPE is unclear, next steps must prioritize clarifying interview format/platform/duration before specific prep.\n"
    "- If Email Intent is 'Request for info', 'Follow up', or 'Other', DO NOT apply any Interview invitation rules.\n"
    "- In particular, for 'Request for info', do NOT require clarifying interview format/platform/duration unless the recruiter email explicitly mentions an interview.\n"
    f"- {SUG_NEXT} should contain bullets.\n"
    f"- {SUG_REPLY} should be short and professional.\n"
    "- Ignore minor punctuation/numbering differences in labels.\n"
    "- No extra top-level sections or closing remarks.\n\n"

    "FORMAT 2 — Rejection:\n"
    "Use only when the draft is a rejection-format draft.\n"
    "Required sections in this order:\n"
    f"1) {REJ_L1}\n"
    f"2) {SUG_L2}\n"
    "3) skill bullets only\n"
    f"4) {SUG_NEXT}\n"
    "5) next-step bullets\n"
    f"6) {SUG_REPLY}\n"
    "7) reply text\n"
    "Rules:\n"
    f"- Show both {SUG_L2} and the skill-bullets section ONLY if MARKET_COMMON_SKILLS.skills_list exists and is non-empty.\n"
    f"- If MARKET_COMMON_SKILLS.skills_list is missing or empty, omit both {SUG_L2} and the skill bullets, and continue directly with {SUG_NEXT}.\n"
    f"- If {SUG_L2} appears, it must be followed only by skill bullets from MARKET_COMMON_SKILLS.skills_list.\n"
    "- The list may include only skills that are reasonably relevant to the JOB_TITLE and/or JOB_DESCRIPTION domain, and skip unrelated or overly niche items.\n"
    "- Do not add, rename, expand, or normalize skills.\n"
    "- Do not add extra prose before, between, or after these parts.\n\n"
    
    "Decision rules:\n"
    "- Use CONTEXT_HINT to know which format is expected.\n"
    "- Judge rejection drafts by FORMAT B.\n"
    "- Judge all other drafts by FORMAT A.\n"
    "- Apply interview-specific validation ONLY when the draft's Email Intent is exactly 'Interview invitation'.\n"
    "- If CONTEXT_HINT includes SUGGESTED_REPLY_IS_EXAMPLE: True, treat suggested_reply as an illustrative sample. Do not mark plausible sample availability slots, dates, greetings, or signatures as hallucinations if they are clearly presented as example content rather than user facts.\n"    "- Treat details as grounded if they are supported by the provided CV, JOB_DESCRIPTION, EMAIL, or CONTEXT_HINT; do not mark them as hallucinations merely because they are absent from the email text alone.\n"
    "- If the draft satisfies the expected format and has no clear hallucination or contradiction, set is_solved=true.\n"
    
    "Output rules:\n"
    "- If is_solved=true: final_response must contain the final answer, needs_reflect must be false, and executor_instructions must be empty.\n"
    "- If is_solved=false: final_response must be empty.\n"
    "- If REFLECTION_JSON is provided: set needs_reflect=false, convert must_fix into ordered executor_instructions, and include up to 5 preserve items from pros.\n"
    "- No extra keys, no markdown, no commentary outside the JSON.\n"
)

def _fallback_finalize(draft: str) -> Dict[str, Any]:
    return {
        "is_solved": True,
        "needs_reflect": False,
        "rationale": "Fallback finalize.",
        "preserve": [],
        "executor_instructions": "",
        "final_response": draft,
    }


async def replan(
    *,
    task_kind: str,
    context_hint: str,
    draft: str,
    trace: Trace,
    reflection: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    llm = LLModClient()

    user_payload = (
        f"TASK_KIND: {task_kind}\n"
        f"CONTEXT_HINT:\n<<<\n{context_hint}\n>>>\n"
    )
    if reflection is not None:
        user_payload += f"REFLECTION_JSON:\n<<<\n{json.dumps(reflection, ensure_ascii=False)}\n>>>\n"
    user_payload += f"DRAFT_RESPONSE:\n<<<\n{draft}\n>>>\n"

    messages = [
        {"role": "system", "content": REPLAN_SYSTEM},
        {"role": "user", "content": user_payload},
    ]
    out = await llm.chat(module="Replan LLM", messages=messages, trace=trace)

    try:
        data = json.loads(out)
        if not isinstance(data, dict):
            return _fallback_finalize(draft)

        is_solved = bool(data.get("is_solved", True))
        needs_reflect = bool(data.get("needs_reflect", False))
        rationale = str(data.get("rationale", "") or "").strip()

        preserve: List[str] = []
        pv = data.get("preserve", [])
        if isinstance(pv, list):
            preserve = [str(x) for x in pv if str(x).strip()][:5]

        executor_instructions = str(data.get("executor_instructions", "") or "").strip()
        final_response = str(data.get("final_response", "") or "")

        if is_solved:
            if not final_response.strip():
                final_response = draft
            return {
                "is_solved": True,
                "needs_reflect": False,
                "rationale": rationale or "Solved.",
                "preserve": [],
                "executor_instructions": "",
                "final_response": final_response,
            }

        if reflection is not None:
            needs_reflect = False

        return {
            "is_solved": False,
            "needs_reflect": needs_reflect,
            "rationale": rationale or "Needs revision.",
            "preserve": preserve,
            "executor_instructions": executor_instructions
            or "Revise the draft to satisfy the SYSTEM rules and required format exactly.",
            "final_response": "",
        }
    except Exception:
        return _fallback_finalize(draft)