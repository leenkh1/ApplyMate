import os
import httpx
from typing import Any, Dict, List

from dotenv import load_dotenv, find_dotenv
from app.core.trace import Trace

# Robust: find .env up the directory tree (works regardless of cwd)
load_dotenv(find_dotenv(), override=False)

class LLModClient:
    def __init__(self):
        self.api_key = os.getenv("LLMOD_API_KEY", "")
        self.base_url = os.getenv("LLMOD_BASE_URL", "").rstrip("/")
        self.chat_model = os.getenv("LLMOD_CHAT_MODEL", "RPRTHPB-gpt-5-mini")

        if not self.base_url:
            raise RuntimeError("Missing LLMOD_BASE_URL in .env / environment")
        if not self.api_key:
            raise RuntimeError("Missing LLMOD_API_KEY in .env / environment")

    async def chat(self, *, module: str, messages: List[Dict[str, str]], trace: Trace) -> str:
        url = f"{self.base_url}/v1/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.chat_model,
            "messages": messages,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, headers=headers, json=payload)
            if r.status_code >= 400:
                trace.add_llm_step(module, payload, {"error_status": r.status_code, "error_text": r.text})
                raise RuntimeError(f"LLMod error {r.status_code}: {r.text}")

            raw = r.json()

        trace.add_llm_step(module, payload, raw)
        return raw["choices"][0]["message"]["content"]