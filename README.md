# job-bot

A personal bot that finds jobs, tailors your CV to each one **truthfully**, and hands you a ready-to-send application packet. You read it and apply yourself; the bot never submits anything (see `docs/decisions.md`, D1/D5).

**Status:** first working slice. Search, the truthfulness gate, CV rendering, packets and the review page all work. Unattended LLM tailoring is not built yet (D7).

## How it works

1. **Master profile** (`private/profile.json`, git-ignored): every true fact about you, with ids. Items marked `"confirm": true` are claims you haven't confirmed yet.
2. **Tailoring** (`private/tailorings/*.json`): for one job, which headline, skills and bullets to show and in what order, plus any reworded lines (each citing the source ids it rewords), and the packet text (answers, cover note, email).
3. **Truthfulness gate** (`jobbot/truth.py`): rejects unknown ids, bullets moved between roles, reordered timelines, and reworded text that brings in numbers, number words, technologies or credentials that its cited sources don't contain. It is a floor, not a proof, so the review page also lists every reworded line.
4. **Render** (`jobbot/render.py`): the CV as HTML in your design (Hebrew RTL or English LTR), then printed to a one-page A4 PDF with headless Chromium.
5. **Review page** (`jobbot/review.py`): one page with every packet, including the CV preview, copyable form fields, ready answers, gaps, and what changed.

## Commands

```bash
python3 -m jobbot search --greenhouse <board> --lever <company> --keyword RF --location Israel
python3 -m jobbot check  private/profile.json private/tailorings/*.json
python3 -m jobbot build  private/profile.json private/tailorings/*.json --out private/applications
python3 -m jobbot review private/applications/*/ --leads private/leads.json --out private/site/review.html
python3 -m unittest discover -s tests -t .
```

Python 3.10+ standard library only. PDF output needs Chromium or Chrome (set `JOBBOT_CHROMIUM` if it isn't on `PATH`; see `.env.example`). `search` needs network access to `boards-api.greenhouse.io` and `api.lever.co`.

## Personal data

This repo is public. Everything personal lives in `private/`, which is git-ignored (D6). Tests use a fictional profile in `tests/fixtures/`.
