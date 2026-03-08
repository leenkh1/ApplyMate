import json
from typing import Any, Dict, List, Optional

from app.core.trace import Trace
from app.llm.llmod_client import LLModClient



OPENING_SENTENCE = "Thank you for providing the relevant information. Below is the analysis explanation:"
STRENGTHS_LINE = "Here are the strengths between your CV and the job description:"
TIPS_LINE = "Here are prioritized tips on what to emphasize, reorder, or rephrase in your CV to better match the job description and ATS wording:"
COMMON_SKILLS_LINE = "Here are common skills for this role that you may consider developing, or you might already have but forgot to include in your CV:"
NOT_AVAILABLE_LINE = "Common skills for this role is Not available"


REPLAN_SYSTEM = (
    "You are the Replan LLM.\n"
    "Goal: decide if the draft is good enough to finalize, or if a revision is required.\n"
    "Return ONLY valid JSON with these keys:\n"
    "{\n"
    '  "is_solved": true|false,\n'
    '  "needs_reflect": true|false,\n'
    '  "rationale": string,\n'
    '  "preserve": [string, ...],\n'
    '  "executor_instructions": string,\n'
    '  "final_response": string\n'
    "}\n"
    "\n"
    "FORMAT CONTRACT (MUST MATCH EXECUTOR EXACTLY):\n"
    f"A) The very first line MUST be exactly:\n{OPENING_SENTENCE}\n"
    "B) The next required line MUST start with 'Match score:' and include '/100'. "
    "This is NOT a section header; it is a single required line.\n"
    "C) The ONLY allowed section header lines are EXACTLY these three lines, and they MUST appear in this exact order:\n"
    f"   {STRENGTHS_LINE}\n"
    f"   {TIPS_LINE}\n"
    f"   {COMMON_SKILLS_LINE}\n"
    "D) No other section headers or extra titles are allowed.\n"
    "E) The document MUST end immediately after the common-skills section content.\n"
    f"   If common skills are unavailable, the common-skills section MUST be exactly:\n"
    f"   {COMMON_SKILLS_LINE}\n"
    f"   {NOT_AVAILABLE_LINE}\n"
    "   and then STOP (no trailing text).\n"
    "F) Common-skills items must be copied exactly from MARKET_COMMON_SKILLS.skills_list (no renaming, no casing changes). "
    "Do NOT request capitalization/normalization of skill names.\n"
    "G) Do NOT request removing the opening line if it matches A.\n"
    "\n"
    "Rules:\n"
    "- If is_solved=true:\n"
    "  - final_response MUST contain the final user-facing answer.\n"
    "  - needs_reflect MUST be false.\n"
    "  - executor_instructions MUST be empty.\n"
    "- If is_solved=false:\n"
    "  - final_response MUST be empty.\n"
    "- Set needs_reflect=true ONLY for worst-case situations:\n"
    "  A) Hallucination risk (invented dates/availability/platform/personal details; invented skills not in CV; invented company/project).\n"
    "  B) Contradictions (two deadlines; conflicting intent; next steps contradict email).\n"
    "  C) Unclear intent that changes the whole output.\n"
    "  D) Severe format failure where minimal edits are unreliable.\n"
    "- Otherwise set needs_reflect=false and provide concrete executor_instructions (minimal edits) for the Executor.\n"
    "- When deciding is_solved for normal drafts (no worst-case condition):\n"
    "  - Treat the draft as good enough (is_solved=true, needs_reflect=false) if it satisfies the FORMAT CONTRACT and there is no clear hallucination or contradiction.\n"
    "  - Do NOT request a revision only for minor style or wording issues.\n"
    "  - If there are small but clear structural/format issues you can describe precisely (e.g., missing one of the three exact header lines, extra text after the common-skills section, "
    "or the match score line missing '/100'), set is_solved=false and needs_reflect=false and provide a short executor_instructions checklist with minimal edits only.\n"
    "- If REFLECTION_JSON is provided:\n"
    "  - Set needs_reflect=false and convert must_fix into an ordered executor_instructions list.\n"
    "  - Include up to 5 preserve items based on pros.\n"
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

        # not solved
        if reflection is not None:
            needs_reflect = False  # reflection already provided; do not ask again

        return {
            "is_solved": False,
            "needs_reflect": needs_reflect,
            "rationale": rationale or "Needs revision.",
            "preserve": preserve,
            "executor_instructions": executor_instructions or "Revise the draft to satisfy the SYSTEM rules and required format exactly.",
            "final_response": "",
        }
    except Exception:
        return _fallback_finalize(draft)