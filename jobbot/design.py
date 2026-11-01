"""Design options a tailoring may set under "design". The cv-designer agent edits only these.

Every option is a named choice (no raw CSS), so a design change can never inject markup or
break the page. Content stays governed by the truth gate; stat tiles are profile items too.
"""

PALETTES = {
    # name: (accent, accent-deep, sidebar, chip, chip-border)
    "blue": ("#2f6bff", "#1b3a8c", "#0f1b2d", "#1b2942", "#2a3a58"),
    "indigo": ("#4f46e5", "#312e81", "#14122b", "#211e45", "#332f63"),
    "teal": ("#0f8b8d", "#0b5557", "#0d2326", "#163639", "#24484b"),
    "graphite": ("#3d5a80", "#22324a", "#1b1f24", "#2a3038", "#3a414b"),
}
DENSITY = {
    "comfortable": ".summary{font-size:13px;line-height:1.75}.job{margin-top:13px}.job li{font-size:12px}h3.sec{margin-top:22px}",
    "normal": "",
    "compact": ".summary{font-size:12px;line-height:1.6}.job{margin-top:8px}.job li{font-size:11px;margin-top:2px}"
               "h3.sec{margin-top:15px}.main{padding-top:24px}.side{padding-top:22px}",
}
SKILL_STYLES = ("chips", "list")
THEMES = ("classic", "minimal")
DEFAULTS = {"theme": "classic", "stats": [], "emphasis": [], "palette": "blue", "density": "normal", "skills_style": "chips", "fact_pills": True}

STATS_CSS = """
.stats{display:grid;gap:0;margin:14px 0 4px;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.stat{padding:10px 10px;text-align:center}
[dir=rtl] .stat{border-left:1px solid var(--line)}[dir=rtl] .stat:last-child{border-left:none}
[dir=ltr] .stat{border-right:1px solid var(--line)}[dir=ltr] .stat:last-child{border-right:none}
.stat .n{font-size:19px;font-weight:800;color:var(--accent-deep);line-height:1;direction:ltr;unicode-bidi:isolate}
.stat .l{font-size:9px;letter-spacing:.02em;color:var(--muted);margin-top:5px;line-height:1.35}
.summary b{color:var(--ink);font-weight:700}
.skills-list{font-size:11px;line-height:1.6;color:var(--sidebar-soft)}
"""


def options(t):
    d = dict(DEFAULTS)
    d.update({k: v for k, v in (t.get("design") or {}).items() if k in DEFAULTS})
    return d


def problems(t, stat_ids):
    """Errors for a tailoring's design block (unknown options, bad stat ids, emphasis not in summary)."""
    errs = []
    raw = t.get("design") or {}
    for k in raw:
        if k not in DEFAULTS:
            errs.append(f"design: unknown option '{k}'")
    d = options(t)
    if d["theme"] not in THEMES:
        errs.append(f"design.theme must be one of {THEMES}")
    if d["palette"] not in PALETTES:
        errs.append(f"design.palette must be one of {sorted(PALETTES)}")
    if d["density"] not in DENSITY:
        errs.append(f"design.density must be one of {sorted(DENSITY)}")
    if d["skills_style"] not in SKILL_STYLES:
        errs.append(f"design.skills_style must be one of {SKILL_STYLES}")
    if not isinstance(d["fact_pills"], bool):
        errs.append("design.fact_pills must be true or false")
    if len(d["stats"]) > 4:
        errs.append("design.stats: at most 4 tiles")
    for s in d["stats"]:
        if s not in stat_ids:
            errs.append(f"design.stats: unknown stat id '{s}'")
    summary = (t.get("summary") or {}).get("text", "")
    if len(d["emphasis"]) > 4:
        errs.append("design.emphasis: at most 4 phrases")
    for ph in d["emphasis"]:
        if not ph or ph not in summary:
            errs.append(f"design.emphasis: '{ph}' is not an exact phrase of the summary")
    return errs


def css(t):
    d = options(t)
    acc, deep, side, chip, border = PALETTES.get(d["palette"], PALETTES["blue"])
    n = max(len(d["stats"]), 1)
    return (f":root{{--accent:{acc};--accent-deep:{deep};--sidebar:{side};--chip:{chip}}}"
            f".chip{{border-color:{border}}}.stats{{grid-template-columns:repeat({n},1fr)}}"
            + STATS_CSS + DENSITY.get(d["density"], ""))
