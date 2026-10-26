"""Load the master profile (the single source of truth for every CV claim)."""

import json
from pathlib import Path

PROFILE_SCHEMA = "jobbot.profile/v1"
LANGS = ("en", "he")


class ProfileError(ValueError):
    pass


def load_profile(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    check_profile(data)
    return data


def check_profile(p):
    if p.get("schema") != PROFILE_SCHEMA:
        raise ProfileError(f"profile schema must be {PROFILE_SCHEMA!r}")
    seen = set()
    for item_id in iter_ids(p):
        if item_id in seen:
            raise ProfileError(f"duplicate id in profile: {item_id}")
        seen.add(item_id)
    for x in p.get("experience", []):
        if not x.get("start"):
            raise ProfileError(f"experience {x['id']} has no start date")


def iter_ids(p):
    for key in ("headlines", "facts", "stats", "skills", "experience", "education", "languages"):
        for item in p.get(key, []):
            yield item["id"]
            for b in item.get("bullets", []):
                yield b["id"]


def index(p):
    """Map every id to (kind, item, parent_experience_id_or_None)."""
    idx = {}
    for key in ("headlines", "facts", "stats", "skills", "education", "languages"):
        for item in p.get(key, []):
            idx[item["id"]] = (key, item, None)
    for x in p.get("experience", []):
        idx[x["id"]] = ("experience", x, None)
        for b in x.get("bullets", []):
            idx[b["id"]] = ("bullet", b, x["id"])
    return idx


def all_text(node):
    """Every string inside a profile node, for claim checking."""
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [s for v in node.values() for s in all_text(v)]
    if isinstance(node, list):
        return [s for v in node for s in all_text(v)]
    return []
