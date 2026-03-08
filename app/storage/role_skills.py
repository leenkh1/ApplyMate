import os
import asyncio
import httpx
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()
LLMOD_API_KEY = os.getenv("LLMOD_API_KEY", "")
LLMOD_BASE_URL = os.getenv("LLMOD_BASE_URL", "").rstrip("/")
LLMOD_EMBED_MODEL = os.getenv("LLMOD_EMBED_MODEL", "RPRTHPB-text-embedding-3-small")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "applymate")


def parse_skills_top(skills_top: str, limit: int = 25) -> list[str]:
    s = (skills_top or "").strip()
    if not s:
        return []
    parts = [p.strip() for p in s.split(",")]
    parts = [p for p in parts if p]
    return parts[:limit]


async def _embed(text: str) -> list[float]:
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


async def retrieve_common_role_skills(job_title: str, top_k: int = 5) -> dict:
    """
    Returns:
      {
        "query_title": "...",
        "matches": [
          {"job_title": "...", "score": 0.78, "n_posts": 123, "skills_top": "..."},
          ...
        ]
      }
    """
    title = (job_title or "").strip()
    if not title:
        return {"query_title": "", "matches": []}

    qvec = await _embed(f"job title: {title}")
    index = _get_index()

    res = await asyncio.to_thread(
        index.query,
        vector=qvec,
        top_k=top_k,
        include_metadata=True,
    )

    matches = []
    for m in res.get("matches", []):
        md = m.get("metadata", {}) or {}
        title_val = md.get("job_title") or md.get("title") or md.get("role") or ""
        skills_val = md.get("skills_top") or md.get("skills_list") or md.get("skills") or ""

        matches.append({
            "job_title": title_val,
            "score": float(m.get("score", 0.0)),
            "n_posts": int(float(md.get("n_posts", 0))) if md.get("n_posts") is not None else 0,
            "skills_top": skills_val,
        })

    return {"query_title": title, "matches": matches}