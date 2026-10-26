"""The "minimal" theme: the clean look of the user's original English CV.

Large serif name over a spaced-caps title, thin grey rules, a two-column body split by a hairline
(contact / skills / languages on one side; summary / experience / education on the other),
spaced-caps section headings and grey bullet text. Hebrew mirrors it right-to-left with
Hebrew-capable faces. Fonts are embedded, so the PDF looks the same everywhere.
"""

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

from . import design
from .profile import index

FONT_DIR = Path(__file__).parent / "fonts"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TITLES = {
    "contact": {"en": "Contact information", "he": "פרטי קשר"},
    "skills": {"en": "Skills", "he": "כישורים"},
    "languages": {"en": "Languages", "he": "שפות"},
    "summary": {"en": "Summary", "he": "תקציר"},
    "experience": {"en": "Experience", "he": "ניסיון תעסוקתי"},
    "education": {"en": "Education", "he": "השכלה"},
    "present": {"en": "Present", "he": "היום"},
}
ICONS = {  # thin line icons (stroke uses currentColor)
    "mail": '<svg viewBox="0 0 16 16"><rect x="1.5" y="3.5" width="13" height="9" rx="1"/><path d="M2 4l6 5 6-5"/></svg>',
    "phone": '<svg viewBox="0 0 16 16"><rect x="4.5" y="1.5" width="7" height="13" rx="1.5"/><path d="M7 12.5h2"/></svg>',
    "home": '<svg viewBox="0 0 16 16"><path d="M2 7.5L8 2.5l6 5"/><path d="M3.5 6.5v7h9v-7"/></svg>',
    "link": '<svg viewBox="0 0 16 16"><rect x="1.5" y="1.5" width="13" height="13" rx="2"/><path d="M5 7v4M5 5v.01M8 11V8.5a1.5 1.5 0 013 0V11M8 7v4"/></svg>',
}


@lru_cache(maxsize=None)
def _font(name):
    return base64.b64encode((FONT_DIR / name).read_bytes()).decode("ascii")


def font_css():
    faces = [
        ("Roboto", 300, "roboto-latin-300-normal.woff2"), ("Roboto", 400, "roboto-latin-400-normal.woff2"),
        ("Roboto", 700, "roboto-latin-700-normal.woff2"), ("Libre Bodoni", 500, "libre-bodoni-latin-500-normal.woff2"),
        ("Heebo", 300, "heebo-hebrew-300-normal.woff2"), ("Heebo", 400, "heebo-hebrew-400-normal.woff2"),
        ("Heebo", 700, "heebo-hebrew-700-normal.woff2"), ("Heebo", 300, "heebo-latin-300-normal.woff2"),
        ("Heebo", 400, "heebo-latin-400-normal.woff2"), ("Heebo", 700, "heebo-latin-700-normal.woff2"),
        ("Frank Ruhl Libre", 500, "frank-ruhl-libre-hebrew-500-normal.woff2"),
        ("Frank Ruhl Libre", 700, "frank-ruhl-libre-hebrew-700-normal.woff2"),
    ]
    return "".join(
        f"@font-face{{font-family:'{fam}';font-weight:{w};font-style:normal;"
        f"src:url(data:font/woff2;base64,{_font(f)}) format('woff2')}}"
        for fam, w, f in faces if (FONT_DIR / f).exists()
    )


CSS = """
:root{--ink:#3d4146;--text:#4a4f55;--soft:#6c7279;--line:#dcdcdc;--accent:#3d4146}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#fff;color:var(--ink);-webkit-font-smoothing:antialiased}
body{font-family:'Roboto','Heebo',Arial,sans-serif}
[lang=he] body,[lang=he] .page{font-family:'Heebo','Roboto',Arial,sans-serif}
.ltr{direction:ltr;unicode-bidi:isolate}
.page{width:210mm;min-height:296mm;margin:0 auto;padding:13mm 15mm 9mm;background:#fff}
.head .title{font-size:10.2px;letter-spacing:.11em;text-transform:uppercase;color:var(--ink)}
.head .name{font-family:'Libre Bodoni',Georgia,serif;font-weight:500;font-size:42px;line-height:1.02;
  text-transform:uppercase;letter-spacing:.02em;color:var(--ink);margin-top:8px}
[lang=he] .head .title{letter-spacing:.06em;font-size:13px;text-transform:none}
[lang=he] .head .name{font-family:'Frank Ruhl Libre',serif;font-weight:700;font-size:42px;text-transform:none;letter-spacing:0}
.rule{border-top:1.6px solid var(--line);margin-top:17px}
.cols{display:grid;grid-template-columns:31% 1fr}
.left{padding:16px 20px 0 0;border-right:1.4px solid var(--line)}
.right{padding:16px 0 0 20px;min-width:0}
[dir=rtl] .left{padding:16px 0 0 20px;border-right:0;border-left:1.4px solid var(--line)}
[dir=rtl] .right{padding:16px 20px 0 0}
h2{font-weight:400;font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink);margin:0 0 10px}
[lang=he] h2{letter-spacing:.04em;font-size:13.5px;font-weight:700}
.sep{border-top:1px solid var(--line);margin:14px 0}
.contact .row{display:flex;gap:9px;align-items:center;font-size:9.6px;color:var(--text);margin-bottom:9px}
.contact svg{width:12px;height:12px;flex:none;fill:none;stroke:var(--soft);stroke-width:1.1}
.contact .v{direction:ltr;unicode-bidi:isolate}
.skills .grp{font-size:8.2px;letter-spacing:.14em;text-transform:uppercase;color:var(--soft);margin:10px 0 3px}
[lang=he] .skills .grp{letter-spacing:.02em;font-size:9.5px}
.skills .grp:first-child{margin-top:0}
.skills ul,.langs ul{list-style:none}
.skills li,.langs li{position:relative;font-size:9.5px;color:var(--text);line-height:1.85}
[dir=ltr] .skills li,[dir=ltr] .langs li{padding-left:13px}
[dir=rtl] .skills li,[dir=rtl] .langs li{padding-right:13px}
.skills li::before,.langs li::before{content:"";position:absolute;top:.95em;width:5px;height:1.2px;background:var(--soft)}
[dir=ltr] .skills li::before,[dir=ltr] .langs li::before{left:0}
[dir=rtl] .skills li::before,[dir=rtl] .langs li::before{right:0}
.summary{font-size:9.7px;line-height:1.6;color:var(--text)}
.summary b{color:var(--ink);font-weight:700}
.stats{display:grid;margin:14px 0 2px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stat{padding:9px 6px;text-align:center}
[dir=ltr] .stat+.stat{border-left:1px solid var(--line)}[dir=rtl] .stat+.stat{border-right:1px solid var(--line)}
.stat .n{font-family:'Libre Bodoni',Georgia,serif;font-size:19px;color:var(--ink);line-height:1;direction:ltr;unicode-bidi:isolate}
.stat .l{font-size:7.6px;letter-spacing:.12em;text-transform:uppercase;color:var(--soft);margin-top:5px;line-height:1.35}
[lang=he] .stat .l{letter-spacing:.02em;font-size:8.6px}
.job{margin-bottom:8px;break-inside:avoid}
.job .t{font-weight:700;font-size:9.4px;letter-spacing:.03em;text-transform:uppercase;color:var(--ink)}
[lang=he] .job .t{font-size:10.5px;text-transform:none;letter-spacing:0}
.job .m{font-size:9.3px;color:var(--text);margin:3px 0 3px}
.job .m b{color:var(--ink)}
.job .m .d{direction:ltr;unicode-bidi:isolate;white-space:nowrap}
.job ul{list-style:none}
.job li{position:relative;font-size:9.3px;line-height:1.5;color:var(--soft);margin-top:2px}
[dir=ltr] .job li{padding-left:11px}[dir=rtl] .job li{padding-right:11px}
.job li::before{content:"\\2022";position:absolute;top:0;color:#b9bdc2;font-size:9px}
[dir=ltr] .job li::before{left:0}[dir=rtl] .job li::before{right:0}
.single .contact-line{font-size:9.6px;color:var(--text);margin-top:12px;display:flex;flex-wrap:wrap;gap:4px 16px}
.single .contact-line span{direction:ltr;unicode-bidi:isolate}
.single .body{padding-top:14px}
/* PDF-parsing portals read letter-spaced capitals as separate letters: keep tracking tight in single layout */
.single .head .title,.single h2,.single .stat .l{letter-spacing:.02em}.single .sep{margin:16px 0}
.single .skills-plain div{font-size:9.6px;line-height:1.7;color:var(--text)}
.single .skills-plain b{color:var(--ink);font-weight:700}
@media print{.page{margin:0}@page{size:A4;margin:0}}
"""

DENSITY = {
    "comfortable": ".summary{font-size:10.4px}.job li{font-size:10px}.job{margin-bottom:13px}",
    "normal": "",
    "compact": ".summary{font-size:9.3px;line-height:1.55}.job li{font-size:9px;margin-top:2px}.job{margin-bottom:8px}"
               ".page{padding-top:14mm;padding-bottom:10mm}.head .name{font-size:40px}.rule{margin-top:16px}.sep{margin:14px 0}",
}


def _date(ym, lang):
    if not ym:
        return TITLES["present"][lang]
    parts = str(ym).split("-")
    if len(parts) < 2:
        return parts[0]
    y, m = parts[0], int(parts[1])
    return f"{MONTHS[m - 1]} {y}" if lang == "en" else f"{m:02d}.{y}"


def _range(item, lang):
    if not item.get("start") and not item.get("end"):
        return ""
    return f"{_date(item.get('start'), lang)} – {_date(item.get('end'), lang)}"


def render(profile, t, bidi, emphasize, skill_groups):
    lang = t["lang"]
    direction = "rtl" if lang == "he" else "ltr"
    idx = index(profile)
    person = profile["person"]
    e = lambda s: bidi(s, lang)  # noqa: E731
    opts = design.options(t)
    single = t.get("layout") == "single"

    headline = idx[t["headline"]][1][lang]
    name = person["name"][lang]
    name_html = "<br>".join(e(part) for part in name.split(" ", 1))

    groups = {}
    for sid in t.get("skills", []):
        s = idx[sid][1]
        g = s.get("group") if s.get("group") in skill_groups else "engineering"
        groups.setdefault(g, []).append(s[lang])
    ordered = sorted(groups.items(), key=lambda kv: list(skill_groups).index(kv[0]))

    stats = "".join(
        f"<div class=\"stat\"><div class=\"n\">{escape(idx[s][1]['value'], quote=True)}</div>"
        f"<div class=\"l\">{e(idx[s][1][lang])}</div></div>"
        for s in opts["stats"] if s in idx
    )
    stats_html = (f'<div class="stats" style="grid-template-columns:repeat({len(opts["stats"])},1fr)">{stats}</div>'
                  if stats else "")

    def job_html(src, bullets, sub=None):
        org = src["org"][lang]
        head, _, rest = org.partition(" · ")
        meta = f"<b>{e(head)}</b>" + (f" · {e(rest)}" if rest else "")
        dates = _range(src, lang)
        if dates:
            meta += f" &nbsp;|&nbsp; <span class=\"d\">{e(dates)}</span>"
        lis = "".join(f"<li>{e(b)}</li>" for b in bullets)
        note = f"<li>{e(sub)}</li>" if sub else ""
        return (f"<div class=\"job\"><div class=\"t\">{e(src['title'][lang])}</div>"
                f"<div class=\"m\">{meta}</div><ul>{lis}{note}</ul></div>")

    jobs = []
    for x in t.get("experience", []):
        src = idx[x["id"]][1]
        texts = [idx[b["ref"]][1][lang] if "ref" in b else b["text"] for b in x.get("bullets", [])]
        jobs.append(job_html(src, texts))
    edu = []
    for eid in t.get("education", []):
        ed = idx[eid][1]
        edu.append(job_html(ed, [], ed["note"][lang] if ed.get("note") else None))

    contact = [("mail", person["email"]), ("phone", person["phone"]), ("home", person["city"][lang])]
    if person.get("linkedin"):
        contact.append(("link", person["linkedin"]))
    summary_html = emphasize(t.get("summary", {}).get("text", ""), opts["emphasis"], lang)
    langs = [f"{l[lang]} | {l['level'][lang]}" for l in profile.get("languages", [])]
    style = f"<style>{font_css()}{CSS}{DENSITY.get(opts['density'], '')}</style>"
    head = (f"<div class=\"head\"><div class=\"title\">{e(headline)}</div>"
            f"<div class=\"name\">{name_html}</div></div><div class=\"rule\"></div>")
    T = lambda k: e(TITLES[k][lang])  # noqa: E731

    if single:
        contact_line = "".join(f"<span>{e(v)}</span>" for _, v in contact)
        skills_plain = "".join(f"<div><b>{e(skill_groups[g][lang])}:</b> {e(', '.join(items))}</div>" for g, items in ordered)
        body = (f"<div class=\"contact-line\">{contact_line}</div><div class=\"body\">"
                f"<h2>{T('summary')}</h2><p class=\"summary\">{summary_html}</p>{stats_html}<div class=\"sep\"></div>"
                f"<h2>{T('experience')}</h2>{''.join(jobs)}<div class=\"sep\"></div>"
                f"<h2>{T('education')}</h2>{''.join(edu)}<div class=\"sep\"></div>"
                f"<h2>{T('skills')}</h2><div class=\"skills-plain\">{skills_plain}"
                f"<div><b>{T('languages')}:</b> {e(', '.join(langs))}</div></div></div>")
        page = f"<div class=\"page single\">{head}{body}</div>"
    else:
        contact_rows = "".join(
            f"<div class=\"row\">{ICONS[k]}<span class=\"{'' if k == 'home' else 'v'}\">{e(v)}</span></div>"
            for k, v in contact)
        skills_html = "".join(
            f"<div class=\"grp\">{e(skill_groups[g][lang])}</div><ul>" + "".join(f"<li>{e(s)}</li>" for s in items) + "</ul>"
            for g, items in ordered)
        left = (f"<aside class=\"left\"><h2>{T('contact')}</h2><div class=\"contact\">{contact_rows}</div>"
                f"<div class=\"sep\"></div><h2>{T('skills')}</h2><div class=\"skills\">{skills_html}</div>"
                f"<div class=\"sep\"></div><h2>{T('languages')}</h2><div class=\"langs\"><ul>"
                + "".join(f"<li>{e(x)}</li>" for x in langs) + "</ul></div></aside>")
        right = (f"<main class=\"right\"><h2>{T('summary')}</h2><p class=\"summary\">{summary_html}</p>{stats_html}"
                 f"<div class=\"sep\"></div><h2>{T('experience')}</h2>{''.join(jobs)}"
                 f"<div class=\"sep\"></div><h2>{T('education')}</h2>{''.join(edu)}</main>")
        # main column first in the DOM so text extraction reads the summary before the sidebar
        page = (f"<div class=\"page\">{head}<div class=\"cols\">{right.replace('<main class=\"right\">', '<main class=\"right\" style=\"grid-column:2;grid-row:1\">')}"
                f"{left.replace('<aside class=\"left\">', '<aside class=\"left\" style=\"grid-column:1;grid-row:1\">')}</div></div>")

    return (f"<!DOCTYPE html>\n<html lang=\"{lang}\" dir=\"{direction}\"><head><meta charset=\"UTF-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
            f"<title>{e(name)} — CV</title>{style}</head><body>{page}</body></html>\n")
