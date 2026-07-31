---
name: buscador
description: >-
  Searches popular Spain job boards plus public LinkedIn pages for AI Security
  Researcher, AI Engineer, and AI Data Analyst roles matching the candidate
  profile. Use when the user says buscador, asks for vacancies in Spain, daily
  job digest, or to update the applications tracker.
---

# buscador — Job search (Spain)

## Read first
1. `profile/profile.yaml`
2. `profile/cv.md`
3. `data/applications.csv` (avoid duplicates)

## Goal
Find **top 5** best-fit open roles for today. Semi-manual / browser-assisted search (no LinkedIn login/API required).

## Sites (all)
InfoJobs, Infoempleo, Indeed ES, Tecnoempleo, Jooble, LinkedIn (public pages only).

## Filters
- Roles: AI Security Researcher, AI Engineer, AI Data Analyst (and close synonyms)
- Level: middle (± junior-strong / senior-light if strong match)
- Location: any Spain city or ES-remote
- Salary: prefer ≥ €50k gross/year when stated; if unknown, still include if role fit is strong
- Employment: prefer formal empleo / contrato
- Languages: English-first OK; Spanish B2 is a plus, not a hard filter
- **Visa sponsorship:** always add a separate line: `Visa sponsorship: yes | no | unknown`

## Workflow
1. Search each site with role keywords + `Spain` / city / `remoto`.
2. Rank by: role fit → seniority fit → salary signal → sponsorship clarity → recency.
3. Prefer new finds; **repeats are OK** if a vacancy is still relevant (user user preference). Still avoid flooding tracker with exact same URL on the same day.
4. Write today's digest to `data/outbox/jobs_YYYY-MM-DD.md` (Moscow date). Always write a concrete top-5 file — never leave the day empty.
5. Append new/repeated rows to `data/applications.csv` with `status=found` (optional note `repeat` if reused).
6. Push/sync to VPS so the bot can send at 15:00. The bot also falls back to the latest outbox or tracker if today's file is missing.
7. If user asks to send now, format for Telegram (see Output).

## Output (Telegram / daily 15:00 MSK)
For each of top 5, exactly:

```
1. {Title} — {Company}
📍 {City or Spain} | {office|hybrid|remote|unknown}
💰 {salary or n/d}
Visa sponsorship: {yes|no|unknown}
🔗 {url}
```

Language: titles/companies as on the source; short labels can be RU/EN mix.

## Outbox file format
```markdown
# Jobs YYYY-MM-DD

1. ...
```

## Do not
- Log into LinkedIn or bypass ToS/auth walls
- Invent salary or sponsorship
- Send more than 5 unless user asks
