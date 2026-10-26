# job-bot

A personal bot that searches for jobs, tailors the user's CV to each one, and applies after the user approves.

## Development process

This repo is built with the **workflow** operating model and the BMad Method skills from
[Bent40/Workflow-Marketplace](https://github.com/Bent40/Workflow-Marketplace)
(enabled in `.claude/settings.json`: workflow-core, workflow-method, workflow-test-architect, workflow-editorial).

- **At session start, invoke the `workflow-operating-model` skill.** Claude Code web does not run plugin SessionStart hooks, so the skill is how the operating model gets loaded.
- Use `bmad-help` to see where the project is in the flow and what comes next.
- BMad config: `_bmad/bmm/config.yaml`. Planning docs go in `docs/planning-artifacts/`, implementation docs (stories, sprint status) in `docs/implementation-artifacts/`.
- Settled decisions: `docs/decisions.md`. Follow them; flag any drift from them.

## Hard rules (see docs/decisions.md)

- Nothing is submitted to an employer without the user's explicit approval (D1).
- No automation against sites whose terms forbid it (D2).
- CV tailoring never invents facts (D3).
- Every CV for a new job goes through `cv-upgrader` → `cv-designer` → `cv-scorer` (loop until PASS ≥85 or 2 rounds), then is re-verified before it is sent to the user (D9, D10).
- No secrets or `.env` in the repo; `.env.example` only.
