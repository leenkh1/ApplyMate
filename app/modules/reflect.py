import json
from typing import Any, Dict
from app.core.trace import Trace
from app.llm.llmod_client import LLModClient

REFLECT_SYSTEM = (
    "You are the Reflect LLM.\n"
    "Goal: critique the DRAFT response for correctness, compliance with constraints, and clarity.\n"
    "Return ONLY valid JSON with these keys:\n"
    "{\n"
    '  "pros": [string, ...],\n'
    '  "cons": [string, ...],\n'
    '  "must_fix": [string, ...],\n'
    '  "nice_to_fix": [string, ...]\n'
    "}\n"
    "Rules:\n"
    "- must_fix: items that violate required format or safety constraints (inventing facts, wrong sections/order, missing required parts).\n"
    "- nice_to_fix: optional improvements.\n"
    "- No extra keys or commentary.\n"
)

def _safe_json_fallback() -> Dict[str, Any]:
    return {"pros": [], "cons": [], "must_fix": [], "nice_to_fix": []}

async def reflect(*, task_kind: str, context_hint: str, draft: str, trace: Trace) -> Dict[str, Any]:
    llm = LLModClient()
    user_payload = (
        f"TASK_KIND: {task_kind}\n"
        f"CONTEXT_HINT:\n<<<\n{context_hint}\n>>>\n"
        f"DRAFT_RESPONSE:\n<<<\n{draft}\n>>>\n"
    )
    messages = [
        {"role": "system", "content": REFLECT_SYSTEM},
        {"role": "user", "content": user_payload},
    ]
    out = await llm.chat(module="Reflect LLM", messages=messages, trace=trace)

    try:
        data = json.loads(out)
        if not isinstance(data, dict):
            return _safe_json_fallback()
        for k in ("pros", "cons", "must_fix", "nice_to_fix"):
            v = data.get(k, [])
            if not isinstance(v, list):
                data[k] = []
            else:
                data[k] = [str(x) for x in v][:8]
        return {
            "pros": data["pros"],
            "cons": data["cons"],
            "must_fix": data["must_fix"],
            "nice_to_fix": data["nice_to_fix"],
        }
    except Exception:
        return _safe_json_fallback()