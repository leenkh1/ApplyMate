# app/storage/interview_links.py
import os
import asyncio
from typing import List

import httpx
from pinecone import Pinecone


LLMOD_API_KEY = os.getenv("LLMOD_API_KEY", "")
LLMOD_BASE_URL = (os.getenv("LLMOD_BASE_URL") or "").rstrip("/")
EMBED_MODEL = os.getenv("LLMOD_EMBED_MODEL", "RPRTHPB-text-embedding-3-small")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
INDEX_NAME = os.getenv("PINECONE_INDEX", "applymate")
NAMESPACE = os.getenv("PINECONE_PREP_LINKS_NAMESPACE", "prep_links")


def _check_env():
    if not LLMOD_API_KEY or not LLMOD_BASE_URL:
        raise RuntimeError("Missing LLMOD_API_KEY or LLMOD_BASE_URL")
    if not PINECONE_API_KEY:
        raise RuntimeError("Missing PINECONE_API_KEY")
    if not INDEX_NAME:
        raise RuntimeError("Missing PINECONE_INDEX")


async def _embed_job_title(job_title: str) -> List[float]:
    """
    Must match the same embedding text used during upsert for best retrieval.
    """
    _check_env()
    job_title = (job_title or "").strip()
    if not job_title:
        return []

    text = f"interview prep link for job title: {job_title}"

    url = f"{LLMOD_BASE_URL}/v1/embeddings"
    headers = {"Authorization": f"Bearer {LLMOD_API_KEY}"}
    payload = {"model": EMBED_MODEL, "input": [text]}

    timeout = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["data"][0]["embedding"]


def _get_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(INDEX_NAME)


async def match_prep_links(job_title: str, max_links: int = 1) -> List[str]:
    """
    Given a job_title, return the best prep_link(s) from Pinecone.
    Default is best single link (max_links=1).
    """
    job_title = (job_title or "").strip()
    if not job_title:
        return []

    emb = await _embed_job_title(job_title)
    if not emb:
        return []

    index = _get_index()

    # Pinecone client is sync; run it off the event loop
    res = await asyncio.to_thread(
        index.query,
        vector=emb,
        top_k=max_links,
        namespace=NAMESPACE,
        include_metadata=True,
    )

    links: List[str] = []
    for m in (res.get("matches") or []):
        md = m.get("metadata") or {}
        link = (md.get("prep_link") or "").strip()
        if link and link not in links:
            links.append(link)

    return links