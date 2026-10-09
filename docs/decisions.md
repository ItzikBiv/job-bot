# Decision log

Settled decisions. Supersede an entry by adding a new one that names the old ID; don't edit history.

| ID | Date | Decision | Why |
|----|------|----------|-----|
| D1 | 2026-10-09 | **Human approves every submission.** The bot finds jobs, tailors the CV, and pre-fills the application, but nothing is sent until the user approves it. | Avoids account bans on sites that forbid automated applying (e.g. LinkedIn), and catches mistakes before an employer sees them. |
| D2 | 2026-10-09 | **Automate sources with public job APIs first** (company career pages on Greenhouse, Lever, Comeet and similar). Aggregators that forbid scraping or bots (LinkedIn, etc.) are out of scope for automation; at most, the user applies to them manually from a list the bot prepares. | ToS compliance and reliability. |
| D3 | 2026-10-09 | **Truthful tailoring only.** CV tailoring may reword, reorder, emphasise, and trim content from the user's master CV; it must never invent experience, skills, titles, dates, or credentials. | Honesty, and fabricated claims get caught in interviews and background checks. |
| D4 | 2026-10-09 | **Process size: Medium.** Brief → PRD → security decision framing → architecture → riskiest-path spike → epics/stories → readiness → sprints. | Multiple integrations, credentials and personal data, and external actions. |
