---
name: planificador
description: >-
  Builds a 180-day development and activity plan toward a Spain AI job offer by
  February 2027, split into 1–2 week sprints. Use when the user says
  planificador, asks for a roadmap, sprint plan, or to replan after changes in
  deadlines or priorities.
---

# planificador — 180-day roadmap

## Read first
1. `profile/profile.yaml`
2. `profile/cv.md`
3. Existing `data/plan/` files if any

## Constraints
- Horizon: **180 days** ending ~**2027-02-01**
- Sprints: **1–2 weeks** each
- Study: **1 hour/day** (technical + interview prep)
- Job search: agent/bot heavy; user reviews vacancies **~1h/week**
- No offer/interview milestone dates unless user asks later

## Workflow
1. Define phases (example): foundation portfolio → targeted applications → interview intensity → relocation/visa readiness with employer
2. Break into numbered sprints with: goal, daily study theme, weekly job-review focus, exit criteria
3. Write:
   - `data/plan/roadmap_180.md` — full plan
   - `data/plan/current_sprint.md` — only the active sprint
4. On replan: update files; keep history in `data/plan/archive/` if replacing

## Sprint template
```markdown
# Sprint {N}: {dates}
## Goal
## Daily study (1h)
## Weekly job review (1h)
## Exit criteria
## Notes for buscador / entrevistador / abogado
```

## Language
Russian for the plan; keep role titles in English.
