"""Greenhouse public Job Board API (read-only; no key needed). https://developers.greenhouse.io/job-board"""

from urllib.parse import quote

from .common import get_json, make_job

API = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"


def parse(board, data):
    return [
        make_job(
            "greenhouse", board, j["id"], j.get("title"), (j.get("location") or {}).get("name", ""),
            j.get("absolute_url"), description=j.get("content", ""), posted=j.get("updated_at", ""),
        )
        for j in data.get("jobs", [])
    ]


def fetch(board, getter=get_json):
    return parse(board, getter(API.format(board=quote(board, safe=""))))
