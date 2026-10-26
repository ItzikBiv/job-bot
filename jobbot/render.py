"""Render a tailored CV to HTML (and PDF via headless Chromium).

The layout follows the user's own Hebrew CV design (navy sidebar, blue accent, A4), in both
RTL (he) and LTR (en). Every string is HTML-escaped: tailoring text may come from an LLM that
has read untrusted job postings.
"""

import os
import re
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

from . import design
from .profile import index

SKILL_GROUPS = {
    "engineering": {"en": "Engineering", "he": "תחומי מומחיות"},
    "software": {"en": "Software", "he": "תוכנה ופיתוח"},
    "ai": {"en": "AI & Automation", "he": "AI ואוטומציה"},
    "strengths": {"en": "Strengths", "he": "חוזקות"},
}
SKILLS_LABEL = {"en": "Skills", "he": "כישורים"}
LABELS = {
    "contact": {"en": "Contact", "he": "פרטי קשר"},
    "languages": {"en": "Languages", "he": "שפות"},
    "experience": {"en": "Experience", "he": "ניסיון תעסוקתי"},
    "education": {"en": "Education", "he": "השכלה"},
    "present": {"en": "Present", "he": "היום"},
}

CSS = """
:root{--ink:#0f1b2d;--ink-soft:#3a4658;--muted:#6b7685;--line:#e2e6ec;--accent:#2f6bff;--accent-deep:#1b3a8c;
--sidebar:#0f1b2d;--sidebar-soft:#aeb8c7;--chip:#1b2942;--page:#ffffff}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#525965;font-family:'Assistant','Heebo','Rubik','Segoe UI',Arial,'DejaVu Sans',sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
.ltr{direction:ltr;unicode-bidi:isolate}
.page{width:210mm;min-height:297mm;margin:14px auto;background:var(--page);display:grid;grid-template-columns:64mm 1fr;box-shadow:0 8px 40px rgba(0,0,0,.35);overflow:hidden}
.side{background:var(--sidebar);color:#fff;padding:26px 20px 30px;grid-column:1;grid-row:1}
.main{grid-column:2;grid-row:1}
.logo{width:44px;height:44px;border-radius:9px;background:var(--accent);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;margin-bottom:22px;direction:ltr}
.side h2{font-size:11.5px;letter-spacing:.06em;color:#fff;font-weight:700;margin:22px 0 10px}
.side h2:first-of-type{margin-top:0}
.contact{font-size:11.5px;line-height:1.95;color:var(--sidebar-soft)}
.contact .row{display:flex;gap:8px;align-items:center}
.contact .k{color:#fff;opacity:.55;width:14px;flex:none;text-align:center;direction:ltr}
.contact .v{direction:ltr;unicode-bidi:isolate}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:11px;line-height:1.1;padding:6px 9px;border:1px solid #2a3a58;border-radius:6px;color:#dbe2ee;background:var(--chip)}
.lang .row{display:flex;justify-content:space-between;font-size:11.5px;color:var(--sidebar-soft);padding:3px 0}
.lang .row b{color:#fff;font-weight:600}
.main{padding:30px 30px 26px;min-width:0}
.name{font-size:34px;line-height:1.05;font-weight:800}
.role{color:var(--accent);font-weight:700;font-size:13px;margin-top:7px}
.rule{height:3px;width:46px;background:var(--accent);border-radius:2px;margin:12px 0 14px}
.summary{font-size:12.5px;line-height:1.7;color:var(--ink-soft)}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 0}
.fact{font-size:10.5px;color:var(--accent-deep);border:1px solid var(--line);border-radius:6px;padding:5px 8px;font-weight:600}
h3.sec{font-size:13px;color:var(--ink);font-weight:800;margin:20px 0 4px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.job{margin-top:11px;break-inside:avoid}
.job .top{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.job .title{font-size:13px;font-weight:700}
.date{font-size:10px;color:var(--muted);white-space:nowrap;letter-spacing:.04em;direction:ltr;unicode-bidi:isolate;font-variant-numeric:tabular-nums}
.job .org{font-size:11px;color:var(--accent-deep);font-weight:600;margin-top:1px}
.job ul{list-style:none;margin:5px 0 0}
.job li{position:relative;font-size:11.5px;line-height:1.55;color:var(--ink-soft);margin-top:3px}
[dir=rtl] .job li{padding-right:13px}[dir=ltr] .job li{padding-left:13px}
.job li::before{content:"";position:absolute;top:8px;width:4px;height:4px;border-radius:50%;background:var(--accent)}
[dir=rtl] .job li::before{right:0}[dir=ltr] .job li::before{left:0}
.edu{margin-top:10px}
.edu .top{display:flex;justify-content:space-between;align-items:baseline;gap:12px}
.edu .title{font-size:12.5px;font-weight:700}
.edu .meta{font-size:11px;color:var(--muted)}
.edu .note{font-size:11px;color:var(--ink-soft);margin-top:2px}
@media print{html,body{background:#fff}.page{margin:0;box-shadow:none;width:auto;min-height:296mm}@page{size:A4;margin:0}}
"""


# A run of English words, including lists like "Scope, VNA" or "C-130H, C-130J": one LTR span
# keeps the list in reading order; separate spans would be reversed by the RTL paragraph.
LATIN_RUN = re.compile(r"[A-Za-z0-9][A-Za-z0-9+#./&'@_-]*(?:,?\s+[A-Za-z0-9+#./&'@_-]+)*")


def bidi(text, lang):
    """Escape text; in Hebrew, isolate Latin runs (C++, n8n + OpenAI API) so they keep their order."""
    text = text or ""
    if lang != "he":
        return escape(text, quote=True)
    out, pos = [], 0
    for m in LATIN_RUN.finditer(text):
        if not re.search(r"[A-Za-z]", m.group()):
            continue
        # Sentence punctuation after the run belongs to the Hebrew sentence, not the English
        # word; inside the LTR span it would show on the wrong side ("MATLAB." -> ".MATLAB").
        run = m.group().rstrip(".,;:!?'")
        out.append(escape(text[pos:m.start()], quote=True))
        out.append(f'<span dir="ltr">{escape(run, quote=True)}</span>')
        pos = m.start() + len(run)
    out.append(escape(text[pos:], quote=True))
    return "".join(out)


# Single-column variant for portals that parse the PDF into fields (Workday, Taleo): no sidebar,
# contact line under the name, skills as plain lines, standard section order.
SINGLE_CSS = """
.page{display:block;min-height:auto}.main{padding:28px 34px 10px}
.contact-line{font-size:11px;color:var(--ink-soft);margin-top:8px}
.contact-line span{white-space:nowrap}
h3.sec{margin-top:16px}
.skills-plain{font-size:11.5px;line-height:1.6;color:var(--ink-soft);margin-top:6px}
.skills-plain b{color:var(--ink)}
@media print{.page{min-height:auto}}
"""


def emphasize(text, phrases, lang):
    """Escape text with bidi() and wrap exact phrases in <b> (phrases are validated substrings)."""
    if not phrases:
        return bidi(text, lang)
    out, pos = [], 0
    spans = sorted((text.find(p), p) for p in phrases if p and text.find(p) >= 0)
    for start, ph in spans:
        if start < pos:
            continue
        out.append(bidi(text[pos:start], lang))
        out.append(f"<b>{bidi(ph, lang)}</b>")
        pos = start + len(ph)
    out.append(bidi(text[pos:], lang))
    return "".join(out)


def _fmt_date(ym, lang):
    """'2023-01' -> '01.2023'; a bare year stays as is; empty means present."""
    if not ym:
        return LABELS["present"][lang]
    parts = str(ym).split("-")
    return f"{parts[1]}.{parts[0]}" if len(parts) >= 2 else parts[0]


def _range(item, lang):
    if not item.get("start") and not item.get("end"):
        return ""  # undated items such as licences
    return f"{_fmt_date(item.get('start'), lang)} – {_fmt_date(item.get('end'), lang)}"


def render_html(profile, t):
    lang = t["lang"]
    direction = "rtl" if lang == "he" else "ltr"
    idx = index(profile)
    person = profile["person"]
    e = lambda s: bidi(s, lang)  # noqa: E731

    headline = idx[t["headline"]][1][lang]
    summary = (t.get("summary") or {}).get("text", "")

    groups = {}
    for sid in t.get("skills", []):
        s = idx[sid][1]
        groups.setdefault(s.get("group") if s.get("group") in SKILL_GROUPS else "engineering", []).append(s[lang])
    as_list = (t.get("design") or {}).get("skills_style") == "list"
    side_skills = "".join(
        f"<h2>{e(SKILL_GROUPS[g][lang])}</h2>"
        + (f"<div class=\"skills-list\">{e(' · '.join(items))}</div>" if as_list else
           "<div class=\"chips\">" + "".join(f"<span class=\"chip\">{e(x)}</span>" for x in items) + "</div>")
        for g, items in sorted(groups.items(), key=lambda kv: list(SKILL_GROUPS).index(kv[0]))
    )
    langs = "".join(
        f"<div class=\"row\"><span>{e(l[lang])}</span><b>{e(l['level'][lang])}</b></div>"
        for l in profile.get("languages", [])
    )
    opts = design.options(t)
    facts = "".join(f"<span class=\"fact\">{e(idx[f][1][lang])}</span>" for f in t.get("facts", [])) if opts["fact_pills"] else ""
    stats = "".join(
        f"<div class=\"stat\"><div class=\"n\">{escape(idx[s][1]['value'], quote=True)}</div><div class=\"l\">{e(idx[s][1][lang])}</div></div>"
        for s in opts["stats"] if s in idx
    )
    stats_html = f'<div class="stats">{stats}</div>' if stats else ""
    summary_html = emphasize(summary, opts["emphasis"], lang)

    jobs = []
    for x in t.get("experience", []):
        src = idx[x["id"]][1]
        bullets = []
        for b in x.get("bullets", []):
            text = idx[b["ref"]][1][lang] if "ref" in b else b["text"]
            bullets.append(f"<li>{e(text)}</li>")
        jobs.append(
            f"<div class=\"job\"><div class=\"top\"><span class=\"title\">{e(src['title'][lang])}</span>"
            f"<span class=\"date\">{e(_range(src, lang))}</span></div>"
            f"<div class=\"org\">{e(src['org'][lang])}</div><ul>{''.join(bullets)}</ul></div>"
        )
    edu = []
    for eid in t.get("education", []):
        ed = idx[eid][1]
        note = f"<div class=\"note\">{e(ed['note'][lang])}</div>" if ed.get("note") else ""
        edu.append(
            f"<div class=\"edu\"><div class=\"top\"><span class=\"title\">{e(ed['title'][lang])}</span>"
            f"<span class=\"date\">{e(_range(ed, lang))}</span></div>"
            f"<div class=\"meta\">{e(ed['org'][lang])}</div>{note}</div>"
        )

    contact = [
        ("@", person["email"], True),
        ("✆", person["phone"], True),
        ("⌂", person["city"][lang], False),
    ]
    if person.get("linkedin"):
        contact.append(("in", person["linkedin"], True))
    contact_html = "".join(
        f"<div class=\"row\"><span class=\"k\">{k}</span><span class=\"{'v' if ltr else ''}\">{e(v)}</span></div>"
        for k, v, ltr in contact
    )

    if t.get("layout") == "single":
        sep = " · "
        contact_line = sep.join(f"<span>{e(v)}</span>" for _, v, _ in contact)
        skills_plain = "".join(
            f"<div><b>{e(SKILL_GROUPS[g][lang])}:</b> {e(', '.join(items))}</div>"
            for g, items in sorted(groups.items(), key=lambda kv: list(SKILL_GROUPS).index(kv[0]))
        )
        lang_plain = ", ".join(f"{l[lang]} ({l['level'][lang]})" for l in profile.get("languages", []))
        return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(person['name'][lang])} — CV</title><style>{CSS}{SINGLE_CSS}{design.css(t)}</style></head>
<body><div class="page"><main class="main">
<div class="name">{e(person['name'][lang])}</div>
<div class="role">{e(headline)}</div>
<div class="contact-line">{contact_line}</div><div class="rule"></div>
<p class="summary">{summary_html}</p>
{stats_html}{f'<div class="facts">{facts}</div>' if facts else ''}
<h3 class="sec">{e(LABELS['experience'][lang])}</h3>{''.join(jobs)}
<h3 class="sec">{e(LABELS['education'][lang])}</h3>{''.join(edu)}
<h3 class="sec">{e(SKILLS_LABEL[lang])}</h3><div class="skills-plain">{skills_plain}</div>
<h3 class="sec">{e(LABELS['languages'][lang])}</h3><div class="skills-plain">{e(lang_plain)}</div>
</main></div></body></html>
"""

    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(person['name'][lang])} — CV</title><style>{CSS}{design.css(t)}</style></head>
<body><div class="page">
<main class="main"><div class="name">{e(person['name'][lang])}</div>
<div class="role">{e(headline)}</div><div class="rule"></div>
<p class="summary">{summary_html}</p>
{stats_html}{f'<div class="facts">{facts}</div>' if facts else ''}
<h3 class="sec">{e(LABELS['experience'][lang])}</h3>{''.join(jobs)}
<h3 class="sec">{e(LABELS['education'][lang])}</h3>{''.join(edu)}
</main>
<aside class="side"><div class="logo">{e(person.get('initials', ''))}</div>
<h2>{e(LABELS['contact'][lang])}</h2><div class="contact">{contact_html}</div>
{side_skills}
<h2>{e(LABELS['languages'][lang])}</h2><div class="lang">{langs}</div></aside></div></body></html>
"""


def find_chromium():
    for cand in (os.environ.get("JOBBOT_CHROMIUM"), "chromium", "chromium-browser", "google-chrome",
                 "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"):
        if cand and (shutil.which(cand) or Path(cand).exists()):
            return shutil.which(cand) or cand
    return None


def render_pdf(html_path, pdf_path):
    """Print the HTML to an A4 PDF with headless Chromium. Returns False if no browser is available."""
    chrome = find_chromium()
    pdf_path = Path(pdf_path)
    pdf_path.unlink(missing_ok=True)  # never report a stale PDF from an earlier build as fresh
    if not chrome:
        return False
    # Headless print occasionally exits cleanly without writing a file; one retry covers it.
    for _attempt in range(2):
        with tempfile.TemporaryDirectory() as profile_dir:
            subprocess.run(
                [chrome, "--headless", "--no-sandbox", "--disable-gpu", f"--user-data-dir={profile_dir}",
                 "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", Path(html_path).resolve().as_uri()],
                check=True, capture_output=True, timeout=120,
            )
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            return True
    return pdf_path.exists() and pdf_path.stat().st_size > 0
