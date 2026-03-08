def route(prompt: str) -> str:
    p = (prompt or "").lower()

    if "task: email_analyze" in p or "email_analyze" in p:
        return "email"
    if "task: resume_tailor" in p or "resume_tailor" in p:
        return "resume"

    email_markers = ["application_id:", "subject:", "from:", "regards", "dear", "interview", "schedule", "recruiter"]
    resume_markers = ["resume", "cv", "job description", "jd", "tailor", "rewrite", "job_title:"]

    if any(m in p for m in email_markers) and "job description" not in p:
        return "email"

    if any(m in p for m in resume_markers):
        return "resume"

    return "help"