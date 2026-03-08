import os
import asyncio
from typing import Optional, Dict, Any
from supabase import create_client, Client


def _get_client() -> Client:
    url = (os.getenv("SUPABASE_URL") or "").strip()
    key = (os.getenv("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
    return create_client(url, key)


async def create_application(*, job_title: str, jd_text: str, cv_text: str) -> str:
    """
    Inserts into 'applications' table and returns application_id (uuid as string).
    """
    job_title = (job_title or "").strip()
    jd_text = (jd_text or "").strip()
    cv_text = (cv_text or "").strip()

    if not job_title or not jd_text or not cv_text:
        raise ValueError("create_application requires job_title, jd_text, cv_text")

    def _insert() -> str:
        client = _get_client()
        res = (
            client.table("applications")
            .insert({"job_title": job_title, "jd_text": jd_text, "cv_text": cv_text})
            .execute()
        )
        data = res.data or []
        if not data:
            raise RuntimeError("Supabase insert returned no data")
        app_id = data[0].get("application_id")
        if not app_id:
            raise RuntimeError("Supabase insert missing application_id in returned row")
        return str(app_id)

    return await asyncio.to_thread(_insert)


async def get_application(*, application_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches application context from 'applications' by application_id.
    Returns dict with job_title/jd_text/cv_text or None if not found.
    """
    application_id = (application_id or "").strip()
    if not application_id:
        return None

    def _select() -> Optional[Dict[str, Any]]:
        client = _get_client()
        res = (
            client.table("applications")
            .select("application_id, job_title, jd_text, cv_text")
            .eq("application_id", application_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0] if rows else None

    return await asyncio.to_thread(_select)


async def add_email(*, application_id: str, email_text: str) -> None:
    """
    Optional persistence of emails for history.
    """
    application_id = (application_id or "").strip()
    email_text = (email_text or "").strip()
    if not application_id or not email_text:
        return

    def _insert() -> None:
        client = _get_client()
        client.table("emails").insert(
            {"application_id": application_id, "email_text": email_text}
        ).execute()

    await asyncio.to_thread(_insert)