import json
from typing import Any, Dict, List
from app.core.trace import Trace
from app.llm.llmod_client import LLModClient

PLANNER_SYSTEM = (
    "You are the Planner LLM.\n"
    "Task: extract structured fields from the user's prompt AND propose a short task list.\n"
    "Return ONLY valid JSON with these keys:\n"
    "{\n"
    '  "task": "RESUME_TAILOR" | "EMAIL_ANALYZE" | "UNKNOWN",\n'
    '  "application_id": string,\n'
    '  "job_title": string,\n'
    '  "cv_text": string,\n'
    '  "jd_text": string,\n'
    '  "email_text": string,\n'
    '  "task_list": [string, ...]\n'
    "}\n"
    "Rules:\n"
    "- If a field is missing, return an empty string for it.\n"
    "- task_list must be 3-7 short items.\n"
    "- For RESUME_TAILOR: include in the task_list steps like parsing CV/JD, scoring/matching, ATS-aligned tips, market skills retrieval, and storing APPLICATION_ID.\n"
    "- For EMAIL_ANALYZE: task_list should include short steps such as parsing the email, loading application context if APPLICATION_ID exists, identifying the email intent, retrieving relevant HR/technical/rejection-related resources only if needed, and generating next steps plus a suggested reply.\n"
    "- Do not include any extra keys or commentary.\n"
)

def _fallback_task_list(task: str) -> List[str]:
    if task == "RESUME_TAILOR":
        return [
            "Parse CV",
            "Parse Job Description",
            "Match & Score",
            "Generate ATS-aligned tips",
            "Retrieve market common skills",
            "Store application context",
        ]
    if task == "EMAIL_ANALYZE":
        return [
            "Parse email + identifiers",
            "Load application context",
            "Classify intent",
            "Retrieve interview resources if needed",
            "Generate next steps + suggested reply",
            "Store email",
        ]
    return ["Clarify user request", "Ask for missing fields", "Provide usage instructions"]

async def plan(prompt: str, trace: Trace) -> Dict[str, Any]:
    llm = LLModClient()
    messages = [
        {"role": "system", "content": PLANNER_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    out = await llm.chat(module="Planner LLM", messages=messages, trace=trace)

    try:
        data = json.loads(out)
        if not isinstance(data, dict):
            raise ValueError("planner output not a dict")

        task = data.get("task", "UNKNOWN") or "UNKNOWN"
        task_list = data.get("task_list", [])
        if not isinstance(task_list, list) or not all(isinstance(x, str) for x in task_list):
            task_list = _fallback_task_list(task)
        if len(task_list) < 1:
            task_list = _fallback_task_list(task)

        return {
            "task": task,
            "application_id": (data.get("application_id", "") or "").strip(),
            "job_title": (data.get("job_title", "") or "").strip(),
            "cv_text": data.get("cv_text", "") or "",
            "jd_text": data.get("jd_text", "") or "",
            "email_text": data.get("email_text", "") or "",
            "task_list": task_list[:7],
        }
    except Exception:
        return {
            "task": "UNKNOWN",
            "application_id": "",
            "job_title": "",
            "cv_text": "",
            "jd_text": "",
            "email_text": "",
            "task_list": _fallback_task_list("UNKNOWN"),
        }