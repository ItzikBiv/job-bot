"""Shared job shape and filtering. Job text is untrusted input: it is stored and shown, never executed."""

import html
import json
import re
import urllib.request

USER_AGENT = "job-bot/0.1 (personal job search; contact via repo owner)"
TAG_RE = re.compile(r"<[^>]+>")


def make_job(source, company, job_id, title, location, url, apply_url=None, description="", employment="", posted=""):
    return {
        "source": source,
        "company": company,
        "id": f"{source}:{company}:{job_id}",
        "title": (title or "").strip(),
        "location": (location or "").strip(),
        "url": url,
        "apply_url": apply_url or url,
        "employment": employment or "",
        "posted": posted or "",
        "description": strip_html(description)[:20000],
    }


def strip_html(text):
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", html.unescape(text or "")))).strip()


def get_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https API hosts
        return json.loads(resp.read().decode("utf-8"))


def matches(job, keywords=(), locations=(), exclude=()):
    """Case-insensitive keyword match on title+description; location substring match; exclusions on title."""
    hay = f"{job['title']} {job['description']}".lower()
    title = job["title"].lower()
    if keywords and not any(k.lower() in hay for k in keywords):
        return False
    if locations and not any(l.lower() in job["location"].lower() for l in locations):
        return False
    if any(x.lower() in title for x in exclude):
        return False
    return True
