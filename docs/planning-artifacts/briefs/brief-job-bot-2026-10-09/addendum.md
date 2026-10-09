# Addendum — job-bot brief (research digest, 2026-10-09)

Detail for the PRD and architecture. Sources are mostly vendor/competitor blogs unless marked official; treat figures as indicative.

## Landscape
- **Mass auto-apply** (LazyApply, LoopCV, AIApply, Sonara — shut down 2024, relaunched by BOLD): poorly reviewed (LazyApply ~2/5 Trustpilot), "spray and pray", LinkedIn restriction/ban reports.
- **Human-in-the-loop assist** (Simplify Copilot, Teal, Jobscan): autofill, tracking, tailoring, keyword match; the user clicks submit. Well regarded.
- job-bot sits between: automated search + truthful tailoring + pre-fill, with a per-application approval gate (D1).

## Job sources
| Source | Read postings | Submit application |
|---|---|---|
| Greenhouse (official docs) | Public GET, no key | Employer key only |
| Lever (official README) | Public | Employer key only |
| Ashby | Likely public (unverified) | Employer key only |
| SmartRecruiters | Conflicting | Partner OAuth / employer |
| Workable | Employer token | Employer only |
| Comeet (big in Israel) | Per-company UID+token found in public embeds (gray area) | No third-party apply API found |
| AllJobs / Drushim / JobMaster | No official API/RSS; ToS **not yet checked** | — |
| Secret Tel Aviv | Greenhouse-fed → readable via Greenhouse | — |
| LinkedIn | ToS §8.2 bans bots/scraping; active enforcement | Out of scope for automation (link out only) |

**Implication:** applying = the user's own session on the employer's hosted form (bot pre-fills, user submits) or a prepared package the user submits by hand.

## Recruiter sentiment
Application volume per job roughly doubled 2022→2025 (Greenhouse benchmark, secondhand). Recruiters/hiring managers report AI-generated, generic, high-volume applications as a burden. No evidence found that a truthful, tailored, low-volume application is penalised — supports D1 + D3.
