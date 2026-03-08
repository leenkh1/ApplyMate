import os
import asyncio
import httpx
import html
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

LLMOD_API_KEY = os.getenv("LLMOD_API_KEY", "")
LLMOD_BASE_URL = (os.getenv("LLMOD_BASE_URL") or "").rstrip("/")
LLMOD_EMBED_MODEL = os.getenv("LLMOD_EMBED_MODEL", "RPRTHPB-text-embedding-3-small")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "applymate")

GOODCV_NAMESPACE = os.getenv("PINECONE_GOODCV_NAMESPACE", "GoodCV")


async def _embed(text: str) -> list[float]:
    """
    Get an embedding vector for the given text using LLMod embeddings.
    """
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
    """
    Return Pinecone Index handle.
    """
    if not PINECONE_API_KEY:
        raise RuntimeError("Missing PINECONE_API_KEY in .env")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(PINECONE_INDEX)


async def retrieve_best_resume_for_jd(
        jd_text: str,
        job_title: Optional[str] = None,
        top_k: int = 1,
) -> Optional[Dict[str, Any]]:
    """
    Query Pinecone (namespace=GoodCV) for the resume most similar to the given JD (+ job_title).

    Expects metadata fields for the Kaggle dataset, e.g.:
      ID, Resume_str, Resume_html, Category

    Returns a dict with keys:
      - score
      - id
      - category
      - resume_str
      - resume_html
    or None if no match.
    """
    jd_text = (jd_text or "").strip()
    job_title = (job_title or "").strip()

    if not jd_text and not job_title:
        return None

    parts = []
    if job_title:
        parts.append(f"job title: {job_title}")
    if jd_text:
        parts.append(f"job description: {jd_text}")
    qtext = "\n".join(parts)

    qvec = await _embed(qtext)
    index = _get_index()

    res = await asyncio.to_thread(
        index.query,
        vector=qvec,
        top_k=top_k,
        include_metadata=True,
        namespace=GOODCV_NAMESPACE,
    )

    matches = res.get("matches") or []
    if not matches:
        return None

    m0 = matches[0]
    md = m0.get("metadata", {}) or {}

    return {
        "score": float(m0.get("score", 0.0)),
        "id": md.get("ID") or md.get("id") or "",
        "category": md.get("Category") or md.get("category") or "",
        "resume_str": md.get("Resume_str") or md.get("resume_str") or "",
        "resume_html": md.get("Resume_html") or md.get("resume_html") or "",
    }


def _html_to_text(html_str: str) -> str:
    """
    Very lightweight HTML → plain text converter for the stored Resume_html.

    Heuristics are tuned for GoodCV resumes:
    - Try to preserve headings and section breaks.
    - Normalize bullets to lines starting with '- '.
    - Merge wrapped lines inside the same bullet or paragraph when they
      are obviously continuations (e.g., lines starting with lowercase
      letters or digits).
    """
    if not html_str:
        return ""

    text = html_str.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?i)</li\s*>", "\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "- ", text)
    text = re.sub(r"(?i)<\s*br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\s*>", "\n\n", text)
    text = re.sub(
        r"(?i)</(div|section|article|header|footer|h[1-6])\s*>",
        "\n\n",
        text,
    )

    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)

    raw_lines = text.split("\n")
    lines: list[str] = []
    for ln in raw_lines:
        ln = ln.strip()
        if not ln:
            lines.append("")
        else:
            lines.append(ln)

    collapsed: list[str] = []
    empty_run = 0
    for ln in lines:
        if ln == "":
            empty_run += 1
            if empty_run <= 2:
                collapsed.append("")
        else:
            empty_run = 0
            collapsed.append(ln)

    merged: list[str] = []
    for ln in collapsed:
        if not merged:
            merged.append(ln)
            continue

        if ln == "":
            if merged[-1] != "":
                merged.append("")
            continue

        prev = merged[-1]
        prev_is_bullet = prev.lstrip().startswith("- ")
        ln_is_bullet = ln.lstrip().startswith("- ")

        if ln_is_bullet:
            content_ln = ln.lstrip()[2:].strip()
            if content_ln and (
                    content_ln[0].islower()
                    or content_ln[0].isdigit()
                    or content_ln[0] in "(["
            ):
                idx = len(merged) - 1
                if merged[idx] == "" and idx > 0 and merged[idx - 1].lstrip().startswith("- "):
                    base = merged[idx - 1]
                    merged[idx - 1] = base + " " + content_ln
                    merged.pop()
                    continue
                elif merged[idx].lstrip().startswith("- "):
                    base = merged[idx]
                    merged[idx] = base + " " + content_ln
                    continue
        if prev_is_bullet and not ln_is_bullet:
            if ln and (ln[0].islower() or ln[0].isdigit() or ln[0] in "(["):
                merged[-1] = prev + " " + ln
                continue
        if (
                prev
                and prev != ""
                and not prev.endswith((".", "!", "?", ":", ";"))
                and ln
                and (ln[0].islower() or ln[0].isdigit())
        ):
            merged[-1] = prev + " " + ln
        else:
            merged.append(ln)

    return "\n".join(merged).strip()


async def get_best_resume_text_for_jd(
        jd_text: str,
        job_title: Optional[str] = None,
        max_chars: int = 10000,
) -> str:
    """
    Public helper used by resume_flow.

    Returns a cleaned plain-text version of the best-matching resume:
    - Uses both job_title and JD text for the query.
    - Prefer Resume_html (converted to text) if available.
    - Fallback to Resume_str.
    - Truncate to max_chars to avoid extremely long outputs.
    """
    rec = await retrieve_best_resume_for_jd(jd_text, job_title=job_title, top_k=1)
    if not rec:
        return ""

    html_part = (rec.get("resume_html") or "").strip()
    str_part = (rec.get("resume_str") or "").strip()

    if html_part:
        text = _html_to_text(html_part)
    else:
        text = str_part.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
        text = text.strip()

    if not text:
        return ""

    if max_chars and len(text) > max_chars:
        text = text[:max_chars].rstrip() + "…"
    return text
