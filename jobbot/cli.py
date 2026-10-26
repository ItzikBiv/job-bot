"""Command line: python -m jobbot <command>.

  search   --greenhouse BOARD --lever COMPANY --keyword K [--location L | --profile P]   list matching jobs
  check    PROFILE TAILORING.json...                                    run the truthfulness gate
  build    PROFILE TAILORING.json... --out DIR                          gate + render CV + packet
  review   PACKET_DIR... --out FILE [--leads leads.json]                build the review desk page
"""

import argparse
import json
import sys
from pathlib import Path

from . import packet, review, truth
from .profile import load_profile
from .sources import common, greenhouse, lever


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_search(a):
    jobs, failures = [], []
    for board in a.greenhouse:
        try:
            jobs += greenhouse.fetch(board)
        except Exception as exc:  # network/policy errors are reported, not fatal
            failures.append(f"greenhouse:{board}: {exc}")
    for company in a.lever:
        try:
            jobs += lever.fetch(company)
        except Exception as exc:
            failures.append(f"lever:{company}: {exc}")
    locations = a.location
    if not locations and a.profile:
        locations = load_profile(a.profile).get("preferences", {}).get("regions", [])
    hits = [j for j in jobs if common.matches(j, a.keyword, locations, a.exclude)][: a.limit]
    print(json.dumps(hits, ensure_ascii=False, indent=2))
    for f in failures:
        print(f"warning: {f}", file=sys.stderr)
    return 0 if hits or not failures else 2


def cmd_check(a):
    profile = load_profile(a.profile)
    bad = 0
    for path in a.tailoring:
        errors, warnings = truth.validate(profile, _load(path))
        print(f"{path}: {'FAIL' if errors else 'ok'}")
        for e in errors:
            print(f"  error: {e}")
        for w in warnings:
            print(f"  warning: {w}")
        bad += bool(errors)
    return 1 if bad else 0


def cmd_build(a):
    profile = load_profile(a.profile)
    status = 0
    for path in a.tailoring:
        try:
            folder, p = packet.build(profile, _load(path), a.out, make_pdf=not a.no_pdf)
            print(f"built {folder} (pdf: {'yes' if p['files']['cv_pdf'] else 'no'}, warnings: {len(p['warnings'])})")
        except packet.TailoringRejected as exc:
            print(f"{path}: {exc}", file=sys.stderr)
            status = 1
        except Exception as exc:  # keep building the rest of the batch
            print(f"{path}: build failed: {exc}", file=sys.stderr)
            status = 1
    return status


def cmd_review(a):
    leads = _load(a.leads) if a.leads else []
    html = review.build_page(a.packets, leads=leads, title=a.title, generated=a.generated)
    Path(a.out).write_text(html, encoding="utf-8")
    print(f"wrote {a.out}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="jobbot", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search")
    s.add_argument("--greenhouse", action="append", default=[])
    s.add_argument("--lever", action="append", default=[])
    s.add_argument("--keyword", action="append", default=[])
    s.add_argument("--location", action="append", default=[])
    s.add_argument("--profile", help="read preferred regions from this profile when no --location is given")
    s.add_argument("--exclude", action="append", default=["senior", "director", "manager"])
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_search)

    c = sub.add_parser("check")
    c.add_argument("profile")
    c.add_argument("tailoring", nargs="+")
    c.set_defaults(fn=cmd_check)

    b = sub.add_parser("build")
    b.add_argument("profile")
    b.add_argument("tailoring", nargs="+")
    b.add_argument("--out", default="private/applications")
    b.add_argument("--no-pdf", action="store_true")
    b.set_defaults(fn=cmd_build)

    r = sub.add_parser("review")
    r.add_argument("packets", nargs="+")
    r.add_argument("--out", default="private/review.html")
    r.add_argument("--leads")
    r.add_argument("--title", default="Application Desk")
    r.add_argument("--generated", default="")
    r.set_defaults(fn=cmd_review)

    a = ap.parse_args(argv)
    return a.fn(a)
