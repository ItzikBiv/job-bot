import copy
import json
from pathlib import Path

FIX = Path(__file__).parent / "fixtures"


def profile():
    return json.loads((FIX / "profile.json").read_text(encoding="utf-8"))


def tailoring(**overrides):
    t = {
        "schema": "jobbot.tailoring/v1",
        "lang": "en",
        "job": {"company": "Acme", "title": "RF Student", "url": "https://example.com/j/1", "status": "unverified"},
        "headline": "h-1",
        "summary": {"text": "EE student with 4 years of lab work and hands-on RF measurements.", "from": ["f-years", "s-rf"]},
        "skills": ["s-rf", "s-matlab"],
        "experience": [
            {"id": "x-new", "bullets": [{"ref": "b-new-1"}, {"text": "Built and maintained RF test setups.", "from": ["b-new-2"]}]},
            {"id": "x-old", "bullets": [{"ref": "b-old-1"}]},
        ],
        "education": ["e-1"],
        "packet": {"answers": [{"question": "Why us?", "answer": "I want to grow my RF lab skills at Acme."}]},
    }
    t = copy.deepcopy(t)
    t.update(overrides)
    return t
