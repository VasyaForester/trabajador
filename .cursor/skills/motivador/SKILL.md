---
name: motivador
description: >-
  Plans daily technical and interview-prep study tasks (~1h), carries over
  incomplete work, and drafts calm lightly romantic weekly motivation about
  living and working in Spain. Use when the user says motivador, asks for daily
  tasks, weekly motivation text, or study reminders for Spain job goals.
---

# motivador — Study tasks + weekly motivation

## Read first
1. `profile/profile.yaml` (1h/day study; focus: technical + interview prep)
2. `profile/cv.md`
3. Active sprint from `data/plan/current_sprint.md` if present
4. `data/runtime/tasks_state.json` if present (bot state)

## Daily tasks (for Telegram 09:00 MSK)
- Total effort ≈ **60 minutes**
- Mix: technical AI security / agents / data **and** interview prep
- If yesterday incomplete: **repeat unfinished items first**, then fill remaining time
- Each task: clear Done criteria (what “done” means in one line)
- Tone of task list: clear, neutral, actionable

### Output for bot / user
```
🗓 {YYYY-MM-DD}
Задачи до 19:00 МСК (~1ч):

1. [tech] ... (25м) — Done: ...
2. [interview] ... (20м) — Done: ...
3. [tech/interview] ... (15м) — Done: ...

Отметь Done в боте до 19:00.
```

Also write machine-readable JSON to `data/outbox/tasks_YYYY-MM-DD.json`:
```json
{
  "date": "YYYY-MM-DD",
  "deadline_msk": "19:00",
  "tasks": [
    {"id": "t1", "kind": "tech", "title": "...", "minutes": 25, "done_criteria": "..."}
  ]
}
```

## Weekly motivation (Saturday 11:00 MSK)
- Calm, light, slightly romantic tone about life/work in Spain
- Short (8–12 lines), no hype, no pressure, no emojis overload (0–2 max)
- Tie gently to progress (skills, language, future city mornings) without guilt
- Write to `data/outbox/motivation_YYYY-MM-DD.md` and/or return text for Telegram

## Do not
- Assign >70 minutes unless user asks
- Shame for missed days — carry over calmly
- Focus on Spanish grammar drills as primary (secondary only if user asks)
