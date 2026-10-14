"""Build the review desk: one page with every packet, ready for the user to read and apply.

Output is an artifact-ready HTML fragment (no <html>/<head>/<body>), with PDFs referenced as
files published alongside it under cvs/<slug>.pdf.
"""

import json
from html import escape
from urllib.parse import urlsplit
from pathlib import Path

STATUS_LABEL = {
    "unverified": "Check the posting is still open",
    "verified": "Posting verified open",
    "lead": "No posting found: open application",
    "linkedin": "LinkedIn: apply manually",
}

PAGE_CSS = r"""
/* Layout: a single column "review desk"; each job is a packet sheet with the CV beside its fields. */
:root{
  --bg:#f3f5f9; --surface:#ffffff; --ink:#0f1b2d; --ink-soft:#46526a; --line:#dde2ea;
  --accent:#2f6bff; --accent-ink:#ffffff; --navy:#0f1b2d;
  --ok:#1f8a4c; --warn:#a15c00; --warn-bg:#fff4e0; --ok-bg:#e6f5ec; --chip:#eef2fb;
  --f-display:'Heebo','Assistant','Segoe UI',Arial,sans-serif;
  --f-body:'Heebo','Assistant','Segoe UI',Arial,sans-serif;
  --f-mono:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bg:#0b1220; --surface:#121b2c; --ink:#e7ecf5; --ink-soft:#a9b4c7; --line:#24314a;
  --accent:#6d97ff; --accent-ink:#0b1220; --navy:#1a2740;
  --ok:#5fd394; --warn:#ffb85c; --warn-bg:#2b2112; --ok-bg:#12291d; --chip:#1a2740; color-scheme:dark}}
:root[data-theme="dark"]{
  --bg:#0b1220; --surface:#121b2c; --ink:#e7ecf5; --ink-soft:#a9b4c7; --line:#24314a;
  --accent:#6d97ff; --accent-ink:#0b1220; --navy:#1a2740;
  --ok:#5fd394; --warn:#ffb85c; --warn-bg:#2b2112; --ok-bg:#12291d; --chip:#1a2740; color-scheme:dark}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--f-body);line-height:1.5;
  padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px 48px}
.wrap{max-width:1180px;margin:0 auto;display:flex;flex-direction:column;gap:22px;min-width:0}
article.packet,.p-head>div{min-width:0}
header.top h1{font-family:var(--f-display);font-weight:800;font-size:clamp(24px,3.4vw,34px);margin:0;text-wrap:balance}
header.top p{margin:6px 0 0;color:var(--ink-soft);max-width:70ch}
.tally{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.tally span{font-size:13px;background:var(--chip);border-radius:999px;padding:4px 12px;font-variant-numeric:tabular-nums}
.notice{border:1px solid var(--line);background:var(--surface);border-radius:10px;padding:12px 16px;font-size:14px;color:var(--ink-soft)}
.notice b{color:var(--ink)}
article.packet{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.p-head{display:flex;flex-wrap:wrap;gap:12px 20px;align-items:flex-start;justify-content:space-between;padding:18px 20px;border-bottom:1px solid var(--line)}
.p-head h2{margin:0;font-family:var(--f-display);font-size:20px;font-weight:700;text-wrap:balance}
.p-head .co{color:var(--ink-soft);font-size:14px;margin-top:2px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{font-size:12px;border-radius:6px;padding:3px 8px;background:var(--chip);color:var(--ink-soft)}
.chip.warn{background:var(--warn-bg);color:var(--warn)}
.chip.ok{background:var(--ok-bg);color:var(--ok)}
.fit{font-family:var(--f-mono);font-size:13px;color:var(--ink-soft);text-align:end}
.fit b{font-size:22px;color:var(--ink);font-family:var(--f-display)}
.actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
a.btn,button.btn{font:inherit;font-size:14px;font-weight:600;border-radius:8px;padding:8px 14px;border:1px solid var(--line);background:var(--surface);color:var(--ink);cursor:pointer;text-decoration:none;display:inline-flex;gap:6px;align-items:center}
a.btn.primary{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.btn:focus-visible,input:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.p-body{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:0}
.cv{border-inline-end:1px solid var(--line);background:var(--navy);padding:14px;min-width:0}
.cvframe{position:relative;overflow:hidden;border-radius:6px;background:#fff;width:100%;max-width:100%;aspect-ratio:794/1123}
.cvframe iframe{position:absolute;top:0;left:0;width:794px;height:1123px;border:0;transform-origin:top left;background:#fff}
.cv .cap{color:#c7d0de;font-size:12px;margin:8px 2px 0}
.side{padding:16px 20px;display:flex;flex-direction:column;gap:18px;min-width:0}
.side h3{margin:0 0 8px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-soft)}
dl.fields{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:6px 10px;margin:0;align-items:center}
dl.fields dt{font-size:13px;color:var(--ink-soft)}
dl.fields dd{margin:0;font-family:var(--f-mono);font-size:13px;overflow-wrap:anywhere}
.qa{border:1px solid var(--line);border-radius:8px;padding:10px 12px;display:flex;flex-direction:column;gap:6px}
.qa .q{font-weight:600;font-size:14px}
.qa .a{white-space:pre-wrap;font-size:14px;color:var(--ink-soft);overflow-wrap:anywhere}
.qa .row{display:flex;justify-content:flex-end}
button.copy{font:inherit;font-size:12px;border:1px solid var(--line);background:transparent;color:var(--accent);border-radius:6px;padding:3px 8px;cursor:pointer}
ul.changes{margin:0;padding-inline-start:18px;font-size:13px;color:var(--ink-soft);display:flex;flex-direction:column;gap:3px}
ul.warns{margin:0;padding-inline-start:18px;font-size:13px;color:var(--warn)}
.gaps{font-size:13px;color:var(--ink-soft)}
label.done{display:flex;gap:8px;align-items:center;font-size:14px;cursor:pointer}
article.packet.is-done{opacity:.6}
.leads{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 20px}
.leads h2{margin:0 0 8px;font-size:18px}
.leads ul{margin:0;padding-inline-start:18px;display:flex;flex-direction:column;gap:6px;font-size:14px}
[dir=rtl]{unicode-bidi:isolate}
@media (max-width:820px){.p-body{grid-template-columns:minmax(0,1fr)}.cv{border-inline-end:0;border-bottom:1px solid var(--line)}}
@media (prefers-reduced-motion:no-preference){article.packet{transition:opacity .2s}}
"""

PAGE_JS = r"""
(function(){
  function store(){try{return window.localStorage}catch(e){return null}}
  document.querySelectorAll('button.copy').forEach(function(b){
    b.addEventListener('click',function(){
      var src=document.getElementById(b.getAttribute('data-for'));var text=src?src.innerText:'';
      var done=function(){var t=b.textContent;b.textContent='Copied';setTimeout(function(){b.textContent=t},1200)};
      var fallback=function(){var r=document.createRange();r.selectNodeContents(src);var s=window.getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Selected, press Ctrl+C'};
      try{navigator.clipboard.writeText(text).then(done,fallback)}catch(e){fallback()}
    });
  });
  function fit(){document.querySelectorAll('.cvframe').forEach(function(f){var i=f.querySelector('iframe');if(i){i.style.transform='scale('+(f.clientWidth/794)+')'}})}
  fit();window.addEventListener('resize',fit);
  document.querySelectorAll('input.applied').forEach(function(cb){
    var key='jobbot-applied-'+cb.id, s=store();
    try{if(s&&s.getItem(key)==='1'){cb.checked=true}}catch(e){}
    var sync=function(){cb.closest('article').classList.toggle('is-done',cb.checked)};sync();
    cb.addEventListener('change',function(){try{if(s){s.setItem(key,cb.checked?'1':'0')}}catch(e){}sync()});
  });
})();
"""

FIELD_LABELS = [
    ("full_name", "Name"), ("full_name_en", "Name (English)"), ("email", "Email"),
    ("phone", "Phone"), ("city", "City"), ("linkedin", "LinkedIn"),
]


def safe_url(url):
    """Only http(s) links reach the page; job data is untrusted."""
    try:
        return url if urlsplit(url or "").scheme in ("http", "https") else ""
    except ValueError:
        return ""


def _score(fit):
    try:
        return float((fit or {}).get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


def _preview(cv_html):
    """Show the CV page edge to edge inside the preview frame."""
    return cv_html.replace("</style>", "html,body{background:#fff}.page{margin:0;box-shadow:none}</style>", 1)


def _e(s):
    return escape(s or "", quote=True)


def _copy_block(uid, text, rtl=False):
    d = ' dir="rtl"' if rtl else ""
    return f'<div class="a" id="{uid}"{d}>{_e(text)}</div><div class="row"><button class="copy" type="button" data-for="{uid}">Copy</button></div>'


def render_packet(p, cv_html):
    slug = p["slug"]
    job = p["job"]
    rtl = p["lang"] == "he"
    fit = p.get("fit") or {}
    status = job.get("status", "unverified")
    chips = [f'<span class="chip">{_e(job.get("location", ""))}</span>',
             f'<span class="chip">{_e(job.get("employment", ""))}</span>',
             f'<span class="chip">CV in {"Hebrew" if rtl else "English"}</span>',
             f'<span class="chip {"ok" if status == "verified" else "warn"}">{_e(STATUS_LABEL.get(status, status))}</span>']
    fields = "".join(
        f'<dt>{label}</dt><dd id="{slug}-f-{key}">{_e(p["fields"].get(key, ""))}</dd>'
        f'<button class="copy" type="button" data-for="{slug}-f-{key}">Copy</button>'
        for key, label in FIELD_LABELS if p["fields"].get(key)
    )
    qa = []
    for i, a in enumerate(p.get("answers", [])):
        qa.append(f'<div class="qa"><div class="q">{_e(a.get("question", "Question"))}</div>{_copy_block(f"{slug}-a{i}", a.get("answer", ""), rtl)}</div>')
    if p.get("cover_note"):
        qa.append(f'<div class="qa"><div class="q">Cover note</div>{_copy_block(f"{slug}-cover", p["cover_note"], rtl)}</div>')
    em = p.get("email")
    if em:
        qa.insert(0, f'<div class="qa"><div class="q">Email to: <span style="font-family:var(--f-mono)" id="{slug}-to">{_e(em.get("to"))}</span> '
                     f'<button class="copy" type="button" data-for="{slug}-to">Copy</button></div>'
                     f'<div class="q">Subject</div>{_copy_block(f"{slug}-subj", em.get("subject"), rtl)}'
                     f'<div class="q">Body (attach the PDF)</div>{_copy_block(f"{slug}-body", em.get("body"), rtl)}</div>')
    changes = "".join(f"<li>{_e(c)}</li>" for c in p.get("changes", []))
    warns = "".join(f"<li>{_e(w)}</li>" for w in p.get("warnings", []))
    pdf = f'<a class="btn" href="cvs/{_e(slug)}.pdf" target="_blank" rel="noopener">Open CV PDF</a>' if p["files"].get("cv_pdf") else ""
    apply_label = "Open posting & apply" if status != "lead" else "Open careers site"
    link = safe_url(job.get("apply_url")) or safe_url(job.get("url"))
    gaps = fit.get("gaps") or []
    return f"""
<article class="packet" id="{_e(slug)}">
  <div class="p-head">
    <div style="min-width:0">
      <h2>{_e(job.get("title"))}</h2>
      <div class="co">{_e(job.get("company"))} · via {_e(job.get("source", ""))}</div>
      <div class="chips">{''.join(chips)}</div>
    </div>
    <div style="display:flex;flex-direction:column;gap:10px;align-items:flex-end">
      <div class="fit"><b>{_e(str(fit.get("score", "–")))}</b>/10 fit<br>{_e(fit.get("reason", ""))}</div>
      <div class="actions">
        {f'<a class="btn primary" href="{_e(link)}" target="_blank" rel="noopener">{apply_label}</a>' if link else '<span class="chip warn">No safe link</span>'}
        {pdf}
        <label class="done"><input type="checkbox" class="applied" id="done-{_e(slug)}"> Applied</label>
      </div>
    </div>
  </div>
  <div class="p-body">
    <div class="cv"><div class="cvframe"><iframe title="Tailored CV for {_e(job.get("company"))}" srcdoc="{_e(_preview(cv_html))}" sandbox="" loading="lazy" tabindex="-1"></iframe></div>
      <p class="cap">Tailored CV preview. The PDF is the file to upload.</p></div>
    <div class="side">
      <section><h3>How to apply</h3><div class="gaps">{_e(job.get("how_to_apply", ""))}</div></section>
      <section><h3>Form fields</h3><dl class="fields">{fields}</dl></section>
      {f'<section><h3>Ready answers</h3><div style="display:flex;flex-direction:column;gap:10px">{"".join(qa)}</div></section>' if qa else ''}
      {f'<section><h3>Gaps to be ready for</h3><ul class="changes">{"".join(f"<li>{_e(g)}</li>" for g in gaps)}</ul></section>' if gaps else ''}
      <section><h3>What changed vs. your master CV</h3><ul class="changes">{changes}</ul></section>
      {f'<section><h3>Confirm before sending</h3><ul class="warns">{warns}</ul></section>' if warns else ''}
    </div>
  </div>
</article>"""


def build_page(packet_dirs, leads=(), title="Application Desk", generated=""):
    packets = []
    for d in packet_dirs:
        d = Path(d)
        p = json.loads((d / "packet.json").read_text(encoding="utf-8"))
        packets.append((p, (d / "cv.html").read_text(encoding="utf-8")))
    packets.sort(key=lambda pc: -_score(pc[0].get("fit")))
    cards = "".join(render_packet(p, html) for p, html in packets)
    lead_items = "".join(
        (f'<li><a href="{_e(safe_url(l.get("url")))}" target="_blank" rel="noopener">{_e(l.get("name"))}</a>: {_e(l.get("note"))}</li>'
         if safe_url(l.get("url")) else f'<li>{_e(l.get("name"))}: {_e(l.get("note"))}</li>')
        for l in leads
    )
    n_unverified = sum(1 for p, _ in packets if p["job"].get("status", "unverified") != "verified")
    return f"""<title>{_e(title)}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{PAGE_CSS}</style>
<div class="wrap">
  <header class="top">
    <h1>{_e(title)}</h1>
    <p>Each packet has a CV tailored to the job, the form fields, and ready answers. Read it, open the posting, and apply yourself. Nothing here was sent to anyone.</p>
    <div class="tally"><span>{len(packets)} packets</span><span>{n_unverified} need the posting checked</span>{f"<span>{_e(generated)}</span>" if generated else ""}</div>
  </header>
  <div class="notice"><b>Every CV line comes from your own CVs.</b> Nothing was invented. Items marked "Confirm before sending" appear only in your Hebrew CV; make sure they're accurate before you send.</div>
  {cards}
  {f'<section class="leads"><h2>More leads to check by hand</h2><ul>{lead_items}</ul></section>' if lead_items else ''}
</div>
<script>{PAGE_JS}</script>
"""
