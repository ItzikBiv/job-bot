---
title: job-bot — Product Brief
status: draft-for-review
created: 2026-10-09
updated: 2026-10-14
---

# job-bot — Product Brief

## The problem

Applying for engineering jobs well is slow. Each good application needs a CV re-cut for the role, the same personal details typed into yet another form, and a short note on why you fit. Doing this properly for a handful of jobs a week takes hours. Spraying a generic CV is fast but gets ignored: recruiters report being flooded with AI-generated, high-volume applications (see addendum).

## Who it is for

One person: the owner. He is a 3rd-year B.Sc. Electrical Engineering student (RF, communications and satellites) and a certified practical engineer, based in Ashdod. He has about six years of IAF aircraft electrical-systems experience and recent work building AI automations. He is looking for a student position or a junior role that fits around his studies. `[ASSUMPTION]` Other users are not a goal for now.

## What it does

1. **Search.** Finds open roles that match his profile, starting with sources that allow it: public ATS job feeds (Greenhouse, Lever) and in-session web search. LinkedIn is never automated; at most it appears as a link.
2. **Tailor.** For each job, produces a CV cut for that role from a single master profile. It may reorder, emphasise, trim and reword, but never invent anything (D3). Every change is listed so he can check it.
3. **Prepare.** Fills in everything an application needs: contact fields, short answers, a cover note, and the right CV language (Hebrew or English, matching the posting).
4. **Hand over.** Shows him a review page with one card per job. He reads the packet, downloads the CV, and applies himself (D1, D5).

## What success looks like

- `[ASSUMPTION]` 5–10 well-matched packets a week, each ready to send in under 3 minutes of his time.
- Zero fabricated claims. Each tailored CV traces line-by-line to the master profile.
- `[ASSUMPTION]` Within 6 weeks, interview invitations at a better rate than his generic CV got.

## Out of scope (for now)

- Submitting applications on his behalf (D5).
- Any automation against LinkedIn or sites whose terms forbid it (D2).
- Unattended LLM tailoring on a server. This needs its own security decision first (D7).
- Multi-user accounts, payments, mobile app.

## Risks and unknowns

- **Source coverage.** Many Israeli defence and aviation employers (IAI, Elbit, Rafael) use their own career sites, not Greenhouse or Lever. Search may lean on web search plus manual links.
- **Network.** The current cloud environment blocks the ATS APIs. Fetchers need the domains allowed, or need to run on his machine.
- **Prompt injection.** Job text is untrusted input to the tailoring step. Mitigation: tailoring may only select and reword items from the master profile, enforced by a validator, not just a prompt.
- **CV claims to confirm.** The Hebrew and English CVs differ (for example "200+ aircraft / 15+ platforms", EMC/EMI, VNA). These stay flagged until he confirms them.

## What's next

Use this first slice (profile → tailoring → render → review page) for real. Then write the PRD (`bmad-prd`) and run `bmad-security-decision-framing` before any unattended automation.
