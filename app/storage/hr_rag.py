import os
import asyncio
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

LLMOD_API_KEY = os.getenv("LLMOD_API_KEY", "")
LLMOD_BASE_URL = os.getenv("LLMOD_BASE_URL", "").rstrip("/")
LLMOD_EMBED_MODEL = os.getenv("LLMOD_EMBED_MODEL", "RPRTHPB-text-embedding-3-small")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "applymate")
HR_NAMESPACE = "hr_questions"

async def _embed(text: str) -> List[float]:
    if not (LLMOD_API_KEY and LLMOD_BASE_URL):
        raise RuntimeError("Missing LLMOD_API_KEY or LLMOD_BASE_URL in .env")

    url = f"{LLMOD_BASE_URL}/v1/embeddings"
    headers = {"Authorization": f"Bearer {LLMOD_API_KEY}"}
    payload = {"model": LLMOD_EMBED_MODEL, "input": text}

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["data"][0]["embedding"]

def _get_index():
    if not PINECONE_API_KEY:
        raise RuntimeError("Missing PINECONE_API_KEY in .env")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(PINECONE_INDEX)

async def retrieve_hr_questions(job_title: str, top_k: int = 5) -> List[Dict[str, Any]]:
    title = (job_title or "").strip()
    if not title:
        return []

    qvec = await _embed(f"hr interview questions for role: {title}")
    index = _get_index()

    res = await asyncio.to_thread(
        index.query,
        vector=qvec,
        top_k=top_k,
        include_metadata=True,
        namespace=HR_NAMESPACE,
    )

    out = []
    for m in res.get("matches", []):
        md = m.get("metadata", {}) or {}
        out.append({
            "score": float(m.get("score", 0.0)),
            "role": md.get("role", ""),
            "category": md.get("category", ""),
            "question": md.get("question", ""),
            "ideal_answer": md.get("ideal_answer", ""),
        })
    return out