"""Build an application packet: validated tailoring -> cv.html, cv.pdf, packet.json."""

import json
import re
from pathlib import Path

from . import render, truth


class TailoringRejected(ValueError):
    def __init__(self, errors):
        super().__init__("tailoring failed the truthfulness check:\n  " + "\n  ".join(errors))
        self.errors = errors


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "job"


def change_log(profile, t):
    """Human-readable list of what this CV changes relative to the full master profile."""
    lang = t["lang"]
    out = []
    order = [x["id"] for x in profile.get("experience", [])]
    chosen = {x["id"]: x for x in t.get("experience", [])}
    titles = {x["id"]: x["title"][lang] for x in profile.get("experience", [])}
    for xid in order:
        if xid not in chosen:
            out.append(f"Left out role: {titles[xid]}")
            continue
        src = next(x for x in profile["experience"] if x["id"] == xid)
        used = set()
        for b in chosen[xid].get("bullets", []):
            if "text" in b:
                out.append(f"Reworded ({titles[xid]}): {b['text']}")
                used.update(b.get("from", []))
            else:
                used.add(b["ref"])
        dropped = [b for b in src.get("bullets", []) if b["id"] not in used]
        for b in dropped:
            out.append(f"Dropped bullet ({titles[xid]}): {b[lang]}")
    all_skills = [s["id"] for s in profile.get("skills", [])]
    picked = t.get("skills", [])
    if picked != all_skills:
        out.append(f"Skills: {len(picked)} of {len(all_skills)} shown, ordered for this role")
    return out


def unconfirmed_items(profile, t):
    """Plain-language names of unconfirmed profile items this CV shows."""
    from .profile import index
    idx = index(profile)
    lang = t["lang"]
    used = list(t.get("skills", [])) + list(t.get("facts", []))
    used += [b["ref"] for x in t.get("experience", []) for b in x.get("bullets", []) if "ref" in b]
    names = []
    for item_id in used:
        item = idx.get(item_id, (None, {}, None))[1]
        if item.get("confirm"):
            names.append(f"{item.get(lang) or item_id}: only in one of your CVs; make sure it's accurate")
    return names


def download_name(profile, t, slug):
    """A file name a recruiter can recognise: Firstname_Lastname_CV_<job label>.pdf (ASCII only)."""
    who = re.sub(r"[^A-Za-z0-9]+", "_", profile["person"]["name"]["en"]).strip("_")
    label = t.get("file_label") or "_".join(w.capitalize() for w in slug.split("-"))
    label = re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_")
    return f"{who}_CV_{label}.pdf"


def build(profile, t, out_root, make_pdf=True):
    errors, warnings = truth.validate(profile, t)
    if errors:
        raise TailoringRejected(errors)
    job = t["job"]
    slug = slugify(t.get("slug") or f"{job['company']}-{job['title']}")
    folder = Path(out_root) / slug
    folder.mkdir(parents=True, exist_ok=True)
    html_path = folder / "cv.html"
    html_path.write_text(render.render_html(profile, t), encoding="utf-8")
    pdf_ok = render.render_pdf(html_path, folder / "cv.pdf") if make_pdf else False
    nice_name = download_name(profile, t, slug)
    if pdf_ok:
        (folder / nice_name).write_bytes((folder / "cv.pdf").read_bytes())

    person = profile["person"]
    lang = t["lang"]
    packet = {
        "schema": "jobbot.packet/v1",
        "slug": slug,
        "job": job,
        "lang": lang,
        "fit": t.get("fit", {}),
        "fields": {
            "full_name": person["name"][lang],
            "full_name_en": person["name"]["en"],
            "email": person["email"],
            "phone": person["phone"],
            "city": person["city"][lang],
            "linkedin": person.get("linkedin", ""),
        },
        "answers": (t.get("packet") or {}).get("answers", []),
        "cover_note": (t.get("packet") or {}).get("cover_note", ""),
        "email": (t.get("packet") or {}).get("email"),
        "changes": change_log(profile, t) + list(t.get("notes", [])),
        "warnings": unconfirmed_items(profile, t) + [w for w in warnings if "not yet confirmed" not in w],
        "files": {"cv_html": "cv.html", "cv_pdf": "cv.pdf" if pdf_ok else None,
                  "cv_named": nice_name if pdf_ok else None},
    }
    (folder / "packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2), encoding="utf-8")
    return folder, packet
