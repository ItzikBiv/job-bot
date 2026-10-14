"""Truthfulness gate (decision D3): a tailored CV may only select, reorder and reword
what the master profile already says. It never adds facts.

This is a deterministic check, not a prompt, and it is a floor rather than a proof: it cannot
read meaning, so plain-word claims ("won a national award") still need the user's eyes. That is
why every reworded line is shown to the user next to its source before anything is sent.

What it catches: unknown ids, bullets moved between roles, reordered timelines, and free text
that introduces numbers, number words, technologies, credentials or acronyms that the cited
source items do not contain.
"""

import re

from .profile import LANGS, all_text, index

TAILORING_SCHEMA = "jobbot.tailoring/v1"

# Technologies and credentials that commonly get "added" to engineering CVs.
TECH_TERMS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "verilog", "vhdl", "systemverilog",
    "fpga", "fpgas", "asic", "pcb", "pcbs", "altium", "orcad", "cadence", "kicad", "spice", "ltspice",
    "hfss", "cst", "ads", "labview", "simulink", "matlab", "sql", "linux", "docker", "kubernetes",
    "aws", "azure", "gcp", "n8n", "openai", "base44", "lovable", "claude", "rf", "vna", "emc", "emi",
    "gnss", "gps", "radar", "sigint", "plc", "scada", "arduino", "raspberry", "stm32", "firmware",
    "dsp", "autocad", "solidworks", "jira", "scrum", "phd", "ph.d", "m.sc", "msc", "mba", "pmp",
    "ccna", "iso", "do-178", "do-254", "mil-std", "as9100", "doctorate", "master's", "patent", "patents",
    # Hebrew spellings, so Hebrew text is checked too
    "פייתון", "וורילוג", "ג'אווה", "מטלב", "לינוקס", "פטנט", "פטנטים", "דוקטורט",
}
# Everyday words that are only a technology when written exactly like this.
CASE_SENSITIVE_TERMS = {"Go": "golang", "C": "c-lang", "ARM": "arm", "Node.js": "node.js", "React": "react", "Rust": "rust"}
NUMBER_WORDS = {
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
    "thirteen", "fourteen", "fifteen", "twenty", "thirty", "forty", "fifty", "hundred", "hundreds",
    "thousand", "thousands", "dozen", "dozens", "million",
}
# Acronyms that describe the application itself, not the candidate.
NON_CLAIM = {"cv", "pdf", "hr", "faq"}

NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")
WORD_RE = re.compile(r"[^\W\d_][\w'.+#-]*")
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9/&-]{1,}\b")


def _norm(token):
    return token.lower().strip(".,;:()/-'")


def _numbers(text):
    return {n.replace(",", "") for n in NUMBER_RE.findall(text)}


def _words(text):
    out = {h for w in WORD_RE.findall(text) for h in _hebrew_stems(_norm(w))}
    out |= {CASE_SENSITIVE_TERMS[w] for w in WORD_RE.findall(text) if w in CASE_SENSITIVE_TERMS}
    return out


HEBREW_PREFIXES = "ובלכמשה"


def _hebrew_stems(word):
    """'ובפייתון' -> {'ובפייתון', 'בפייתון', 'פייתון'}: strip up to two one-letter prefixes."""
    out = {word}
    for _ in range(2):
        out |= {w[1:] for w in out if len(w) > 3 and w[0] in HEBREW_PREFIXES}
    return out


def _claim_tokens(text):
    """Technologies, credentials and number words: must come from the cited sources."""
    tokens = set()
    for tok in WORD_RE.findall(text):
        n = _norm(tok)
        hebrew_hit = next((h for h in _hebrew_stems(n) if h in TECH_TERMS), None)
        if hebrew_hit and hebrew_hit != n:
            tokens.add(hebrew_hit)
        elif tok in CASE_SENSITIVE_TERMS:
            tokens.add(CASE_SENSITIVE_TERMS[tok])
        elif n in TECH_TERMS or n in NUMBER_WORDS:
            tokens.add(n)
    return tokens - NON_CLAIM


def _acronyms(text):
    """Other acronyms (IDF, SCE, EE): usually names, so they only need to exist in the profile."""
    return {_norm(a) for a in ACRONYM_RE.findall(text)} - NON_CLAIM


def _strip_phrases(text, phrases):
    for ph in sorted((p for p in phrases if p), key=len, reverse=True):
        text = text.replace(ph, " ")
    return text


def _check_free_text(label, text, sources, errors, warnings, confirm_texts, profile_tokens, allowed_phrases=()):
    """Free text may only use numbers and claim tokens found in the texts it cites.

    `allowed_phrases` (the job's company and title, the user's own contact details) are removed
    as whole phrases first, so a job posting cannot launder single words into claims.
    A claim backed only by unconfirmed profile items produces a warning.
    """
    text = _strip_phrases(text, allowed_phrases)
    src = " ".join(sources)
    for n in sorted(_numbers(text) - _numbers(src)):
        errors.append(f"{label}: number '{n}' does not appear in the cited source items")
    src_tokens = _words(src) | {_norm(a) for a in ACRONYM_RE.findall(src)}
    confirmed_src = " ".join(s for s in sources if s not in set(confirm_texts))
    confirmed_tokens = _words(confirmed_src) | {_norm(a) for a in ACRONYM_RE.findall(confirmed_src)}
    for tok in sorted(_claim_tokens(text)):
        if tok not in src_tokens:
            errors.append(f"{label}: '{tok}' is not in the cited source items (possible invented claim)")
        elif tok not in confirmed_tokens:
            warnings.append(f"{label}: '{tok}' rests only on items the user has not confirmed")
    for acr in sorted(_acronyms(text) - _claim_tokens(text) - src_tokens):
        if acr not in profile_tokens:
            errors.append(f"{label}: '{acr}' is not in the master profile (possible invented claim)")


def validate(profile, t):
    """Return (errors, warnings). Errors block rendering; warnings are shown to the user."""
    errors, warnings = [], []
    idx = index(profile)
    profile_texts = all_text({k: v for k, v in profile.items() if k != "person"})
    confirm_texts = [s for kind, item, _ in idx.values() if item.get("confirm") for s in all_text(item)]
    blob = " ".join(profile_texts)
    profile_tokens = _words(blob) | _acronyms(blob)

    if t.get("schema") != TAILORING_SCHEMA:
        errors.append(f"tailoring schema must be {TAILORING_SCHEMA!r}")
    job = t.get("job") if isinstance(t.get("job"), dict) else {}
    if not job.get("company") or not job.get("title"):
        errors.append("job: 'company' and 'title' are required")
    lang = t.get("lang")
    if lang not in LANGS:
        errors.append(f"lang must be one of {LANGS}")
        return errors, warnings

    def need(item_id, kinds, where):
        entry = idx.get(item_id)
        if entry is None:
            errors.append(f"{where}: unknown id '{item_id}'")
            return None
        if entry[0] not in kinds:
            errors.append(f"{where}: '{item_id}' is a {entry[0]}, expected {'/'.join(kinds)}")
            return None
        if entry[1].get("confirm"):
            warnings.append(f"{where}: '{item_id}' is not yet confirmed by the user")
        return entry

    need(t.get("headline"), ("headlines",), "headline")

    summary = t.get("summary") or {}
    if summary.get("text"):
        refs = summary.get("from") or []
        if not refs:
            errors.append("summary: free text must cite source ids in 'from'")
        sources = []
        for r in refs:
            e = need(r, ("facts", "bullet", "skills", "education", "experience"), "summary.from")
            if e:
                sources += all_text(e[1])
        _check_free_text("summary", summary["text"], sources, errors, warnings, confirm_texts, profile_tokens)

    for fid in t.get("facts", []):
        need(fid, ("facts",), "facts")
    for sid in t.get("skills", []):
        need(sid, ("skills",), "skills")
    for eid in t.get("education", []):
        need(eid, ("education",), "education")

    order = [x["id"] for x in profile.get("experience", [])]
    chosen = [x.get("id") for x in t.get("experience", [])]
    positions = [order.index(c) for c in chosen if c in order]
    if positions != sorted(positions):
        errors.append("experience: entries must keep the profile's chronological order")
    omitted = [o for o in order if o not in chosen]
    if omitted:
        warnings.append(f"experience: omitted {', '.join(omitted)} (creates a gap in the timeline)")

    for x in t.get("experience", []):
        xe = need(x.get("id"), ("experience",), "experience")
        if not xe:
            continue
        for i, b in enumerate(x.get("bullets", [])):
            where = f"experience.{x['id']}.bullets[{i}]"
            if "ref" in b and "text" in b:
                errors.append(f"{where}: use either 'ref' or 'text', not both")
            elif "ref" in b:
                be = need(b["ref"], ("bullet",), where)
                if be and be[2] != x["id"]:
                    errors.append(f"{where}: bullet '{b['ref']}' belongs to '{be[2]}', not '{x['id']}'")
            elif "text" in b:
                refs = b.get("from") or []
                if not refs:
                    errors.append(f"{where}: reworded bullet must cite source bullet ids in 'from'")
                sources = []
                for r in refs:
                    be = need(r, ("bullet",), where + ".from")
                    if be:
                        if be[2] != x["id"]:
                            errors.append(f"{where}: source '{r}' belongs to '{be[2]}', not '{x['id']}'")
                        sources += all_text(be[1])
                sources += all_text(xe[1].get("title", {})) + all_text(xe[1].get("org", {}))
                _check_free_text(where, b["text"], sources, errors, warnings, confirm_texts, profile_tokens)
            else:
                errors.append(f"{where}: needs 'ref' or 'text'")

    # Packet text cites the whole profile; it may name the job (as whole phrases) and repeat the
    # user's own contact details.
    phrases = [job.get("company", ""), job.get("title", "")] + list(job.get("aliases", []))
    phrases += all_text(profile.get("person", {}))
    packet = t.get("packet") or {}
    texts = [(f"packet.answers[{i}]", qa.get("answer", "")) for i, qa in enumerate(packet.get("answers", []))]
    texts.append(("packet.cover_note", packet.get("cover_note", "")))
    email = packet.get("email") or {}
    texts += [(f"packet.email.{part}", email.get(part, "")) for part in ("subject", "body")]
    for label, text in texts:
        if text:
            _check_free_text(label, text, profile_texts, errors, warnings, confirm_texts, profile_tokens, phrases)

    return errors, warnings
