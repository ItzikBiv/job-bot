"""Lever public Postings API (read-only; no key needed). https://github.com/lever/postings-api"""

from datetime import datetime, timezone
from urllib.parse import quote

from .common import get_json, make_job

API = "https://api.lever.co/v0/postings/{company}?mode=json"


def parse(company, data):
    jobs = []
    for p in data:
        cats = p.get("categories") or {}
        created = p.get("createdAt")
        posted = datetime.fromtimestamp(created / 1000, tz=timezone.utc).date().isoformat() if created else ""
        jobs.append(make_job(
            "lever", company, p["id"], p.get("text"), cats.get("location", ""), p.get("hostedUrl"),
            apply_url=p.get("applyUrl"), description=p.get("descriptionPlain") or p.get("description", ""),
            employment=cats.get("commitment", ""), posted=posted,
        ))
    return jobs


def fetch(company, getter=get_json):
    return parse(company, getter(API.format(company=quote(company, safe=""))))
