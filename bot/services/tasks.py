from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from bot.db import Store

# Rotating pool: technical + interview (~60 minutes)
TASK_POOL: list[dict[str, Any]] = [
    {
        "kind": "tech",
        "title": "Read one AI security incident/advisory and write 5 bullet findings (EN)",
        "minutes": 25,
        "done_criteria": "5 bullets saved in notes",
    },
    {
        "kind": "interview",
        "title": "Draft STAR story: a time you investigated an AI/security risk",
        "minutes": 20,
        "done_criteria": "STAR text ≥120 words in EN",
    },
    {
        "kind": "tech",
        "title": "Sketch an agent architecture (tools, memory, guardrails) for a toy use-case",
        "minutes": 15,
        "done_criteria": "1 diagram or 10-line outline",
    },
    {
        "kind": "tech",
        "title": "Practice prompt-injection threat model for a tool-using agent",
        "minutes": 25,
        "done_criteria": "assets/threats/mitigations listed",
    },
    {
        "kind": "interview",
        "title": "Answer aloud: Why Spain + why this AI role? Record or write 90 seconds",
        "minutes": 20,
        "done_criteria": "script or voice note done",
    },
    {
        "kind": "tech",
        "title": "Implement or refine a tiny Python eval harness for an LLM/agent behavior",
        "minutes": 30,
        "done_criteria": "script runs or pseudocode + tests plan",
    },
    {
        "kind": "interview",
        "title": "Prepare answer: explaining a complex AI risk to a non-security hiring manager",
        "minutes": 15,
        "done_criteria": "plain-language paragraph in EN",
    },
    {
        "kind": "tech",
        "title": "Compare 2 AI security papers/posts: methods, limits, what you'd reuse",
        "minutes": 25,
        "done_criteria": "comparison table 4 rows",
    },
    {
        "kind": "interview",
        "title": "Mock: walk through your agent project end-to-end (problem → design → failure modes)",
        "minutes": 25,
        "done_criteria": "outline with failure modes section",
    },
    {
        "kind": "tech",
        "title": "Data angle: define metrics/dashboards you'd use to monitor AI system risk",
        "minutes": 20,
        "done_criteria": "≥6 metrics with owners/cadence",
    },
    {
        "kind": "interview",
        "title": "Salary & sponsorship narrative: practice calm 60s pitch (≥€50k, need work auth)",
        "minutes": 15,
        "done_criteria": "spoken once without notes",
    },
    {
        "kind": "tech",
        "title": "Hands-on: build a minimal tool-calling agent loop and list abuse cases",
        "minutes": 35,
        "done_criteria": "code or detailed pseudo + 3 abuse cases",
    },
]


def _load_outbox_tasks(outbox: Path, day: date) -> list[dict[str, Any]] | None:
    path = outbox / f"tasks_{day.isoformat()}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data.get("tasks") or []
    result = []
    for i, t in enumerate(tasks, start=1):
        result.append(
            {
                "task_key": t.get("id") or f"outbox-{i}",
                "kind": t.get("kind", "tech"),
                "title": t["title"],
                "minutes": int(t.get("minutes", 20)),
                "done_criteria": t.get("done_criteria", "completed"),
                "carried": 0,
            }
        )
    return result or None


def _pool_slice(day: date, minutes_budget: int = 60) -> list[dict[str, Any]]:
    start = day.toordinal() % len(TASK_POOL)
    picked: list[dict[str, Any]] = []
    total = 0
    i = 0
    while total < minutes_budget and i < len(TASK_POOL):
        item = TASK_POOL[(start + i) % len(TASK_POOL)]
        # avoid duplicate kinds back-to-back when possible
        if picked and picked[-1]["kind"] == item["kind"] and i + 1 < len(TASK_POOL):
            i += 1
            continue
        if total + item["minutes"] > minutes_budget + 5:
            i += 1
            continue
        picked.append(
            {
                "task_key": f"pool-{(start + i) % len(TASK_POOL)}",
                "kind": item["kind"],
                "title": item["title"],
                "minutes": item["minutes"],
                "done_criteria": item["done_criteria"],
                "carried": 0,
            }
        )
        total += item["minutes"]
        i += 1
    if not picked:
        item = TASK_POOL[start]
        picked = [
            {
                "task_key": f"pool-{start}",
                "kind": item["kind"],
                "title": item["title"],
                "minutes": item["minutes"],
                "done_criteria": item["done_criteria"],
                "carried": 0,
            }
        ]
    return picked


def build_tasks_for_day(store: Store, outbox: Path, day: date) -> list[Any]:
    """Carry incomplete from yesterday, then fill from outbox or pool."""
    yesterday = day - timedelta(days=1)
    carried = []
    for row in store.incomplete_tasks(yesterday):
        carried.append(
            {
                "task_key": f"carry-{row['task_key']}",
                "kind": row["kind"],
                "title": f"(carry) {row['title']}",
                "minutes": row["minutes"],
                "done_criteria": row["done_criteria"],
                "carried": 1,
            }
        )

    carried_minutes = sum(t["minutes"] for t in carried)
    remaining = max(0, 60 - carried_minutes)

    fresh: list[dict[str, Any]] = []
    if remaining > 0:
        outbox_tasks = _load_outbox_tasks(outbox, day)
        if outbox_tasks:
            for t in outbox_tasks:
                if sum(x["minutes"] for x in fresh) + t["minutes"] <= remaining + 5:
                    fresh.append(t)
        else:
            fresh = _pool_slice(day, remaining)

    combined = carried + fresh
    # de-dup keys if needed
    seen: set[str] = set()
    unique = []
    for t in combined:
        key = t["task_key"]
        if key in seen:
            key = f"{key}-{len(unique)}"
            t = {**t, "task_key": key}
        seen.add(key)
        unique.append(t)

    return store.replace_day_tasks(day, unique)


def format_tasks_message(day: date, rows: list[Any]) -> str:
    lines = [
        f"🗓 {day.isoformat()}",
        "Задачи до 19:00 МСК (~1ч):",
        "",
    ]
    for i, r in enumerate(rows, start=1):
        status = "✅" if r["is_done"] else "⬜"
        lines.append(
            f"{status} {i}. [{r['kind']}] {r['title']} ({r['minutes']}м)\n"
            f"   Done: {r['done_criteria']}"
        )
    lines.append("")
    lines.append("Нажми Done по каждой задаче (или «Все Done»). Незавершённое перейдёт на завтра.")
    return "\n".join(lines)
