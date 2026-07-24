from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from bot.db import Store

# Rotating pool: technical + interview (~60 minutes).
# Each task: short title + rules (how to do it) + done_criteria (when to press Done).
TASK_POOL: list[dict[str, Any]] = [
    {
        "kind": "tech",
        "title": "Разобрать 1 AI-security инцидент/advisory",
        "minutes": 25,
        "rules": (
            "Выбери один публичный источник (advisory, blog, CVE write-up) про LLM/agent security. "
            "Прочитай целиком. Запиши на английском 5 пунктов: (1) что сломалось, (2) атакующий вектор, "
            "(3) затронутый актив, (4) почему это важно для бизнеса, (5) какая защита помогла бы. "
            "Не копируй текст статьи — своими словами."
        ),
        "done_criteria": "В заметках есть ровно 5 bullets на EN + ссылка на источник",
    },
    {
        "kind": "interview",
        "title": "STAR: расследование AI/security риска",
        "minutes": 20,
        "rules": (
            "Напиши ответ на EN по структуре S-T-A-R (Situation / Task / Action / Result). "
            "Тема: реальный или учебный кейс, где ты разбирал AI/security риск. "
            "Минимум 120 слов. В Result укажи измеримый итог (что изменили / какой контроль внедрили). "
            "Это текст, который можно сказать на собеседовании за ~90 секунд."
        ),
        "done_criteria": "Готовый STAR-текст ≥120 слов на EN с явными буквами S/T/A/R",
    },
    {
        "kind": "tech",
        "title": "Набросать архитектуру tool-using агента",
        "minutes": 15,
        "rules": (
            "Выбери простой use-case (например: assistant с поиском и тикетами). "
            "Опиши или нарисуй: LLM/orchestrator, memory, список tools, guardrails. "
            "Отметь 2 trust boundary (где недоверенные данные входят в систему). "
            "Формат: схема или маркированный список на 8–12 строк."
        ),
        "done_criteria": "Есть схема/outline + явно названы ≥2 trust boundaries",
    },
    {
        "kind": "tech",
        "title": "Threat model: prompt injection у агента с tools",
        "minutes": 25,
        "rules": (
            "Для агента с tools сделай мини threat model: "
            "активы (данные, credentials, actions) → угрозы (direct/indirect injection, tool abuse) → "
            "1–2 сценария атаки цепочкой → mitigations (least privilege, human approve, isolate retrieved text). "
            "Пиши коротко, можно на RU или EN."
        ),
        "done_criteria": "Список: активы, ≥3 угрозы, ≥1 attack chain, ≥3 mitigation",
    },
    {
        "kind": "interview",
        "title": "Pitch: Why Spain + why AI security role",
        "minutes": 20,
        "rules": (
            "Подготовь устный ответ на EN на 60–90 секунд: почему Испания, почему сейчас (к Feb 2027), "
            "почему роль AI Security/AI Engineer. "
            "Структура: motivation → professional fit → timeline. "
            "Без клише только про погоду: добавь рынок/карьеру. Произнеси вслух 1 раз или запиши текст."
        ),
        "done_criteria": "Есть текст/запись 60–90 сек; есть блок про timeline до Feb 2027",
    },
    {
        "kind": "tech",
        "title": "Мини eval-harness для поведения LLM/агента",
        "minutes": 30,
        "rules": (
            "Сделай простой набор проверок (Python или подробный псевдокод): "
            "≥5 тест-кейсов (jailbreak, injection, отказ в опасном tool call, корректный ответ, hallucination). "
            "Для каждого: input → expected behavior → pass/fail. "
            "Цель — регрессия после смены промпта/модели."
        ),
        "done_criteria": "Файл/заметка с ≥5 кейсами в формате input/expected/pass-fail",
    },
    {
        "kind": "interview",
        "title": "Объяснить AI-риск non-security менеджеру",
        "minutes": 15,
        "rules": (
            "На EN напиши 1 абзац (80–120 слов) без жаргона: что такое prompt injection для tool-using агента, "
            "какой бизнес-вред, что вы сделаете в первую очередь. "
            "Представь, что слушатель — hiring manager без security background."
        ),
        "done_criteria": "1 абзац EN 80–120 слов без необъяснённых терминов",
    },
    {
        "kind": "tech",
        "title": "Сравнить 2 материала по AI security",
        "minutes": 25,
        "rules": (
            "Возьми 2 источника (paper/post/advisory). Сравни в таблице 4 строки: "
            "метод / что хорошо / ограничения / что возьмёшь в свою практику. "
            "Язык: EN или RU."
        ),
        "done_criteria": "Таблица 4 строк + 2 ссылки на источники",
    },
    {
        "kind": "interview",
        "title": "Mock walkthrough агент-проекта",
        "minutes": 25,
        "rules": (
            "Подготовь рассказ на EN: problem → architecture → tools → 3 failure modes → mitigations. "
            "Это должен быть агент (LLM + tools), не обычный бот/CRUD. "
            "Если реального агента мало — опиши учебный, но честно скажи, что prototype. "
            "Outline на 10–15 строк."
        ),
        "done_criteria": "Outline с секциями architecture/tools/failure modes/mitigations",
    },
    {
        "kind": "tech",
        "title": "Метрики риска LLM-продукта",
        "minutes": 20,
        "rules": (
            "Составь dashboard из ≥6 метрик для LLM/agent продукта "
            "(не только «вероятность×ущерб»). "
            "Для каждой: что измеряем, зачем, как часто смотрим. "
            "Примеры: injection probe fail rate, blocked tool calls, leakage incidents, audit completeness."
        ),
        "done_criteria": "≥6 метрик с полями: name / why / cadence",
    },
    {
        "kind": "interview",
        "title": "60s pitch: зарплата €50k+ и work authorization",
        "minutes": 15,
        "rules": (
            "На EN спокойно отрепетируй 60 секунд: ожидаешь formal employment, floor €50k gross, "
            "нужен employer-sponsored work authorization (ты гражданин РФ вне Испании), "
            "готов предоставить документы и timeline к early 2027. "
            "Без извинений и без «не знаю». Произнеси вслух без шпаргалки."
        ),
        "done_criteria": "Произнёс вслух 1 раз; текст при желании сохранён в заметках",
    },
    {
        "kind": "tech",
        "title": "Собрать минимальный tool-calling loop",
        "minutes": 35,
        "rules": (
            "Код или детальный псевдокод: цикл agent → choose tool → execute → observe → stop. "
            "Ограничения: allowlist tools, max steps, schema validation. "
            "Отдельно перечисли 3 abuse cases (injection, over-permission, infinite loop) и как их режешь."
        ),
        "done_criteria": "Код/псевдокод loop + список из 3 abuse cases с защитой",
    },
]


def _normalize_task(raw: dict[str, Any], task_key: str, carried: int = 0) -> dict[str, Any]:
    return {
        "task_key": task_key,
        "kind": raw.get("kind", "tech"),
        "title": raw["title"],
        "minutes": int(raw.get("minutes", 20)),
        "rules": (raw.get("rules") or "").strip(),
        "done_criteria": (raw.get("done_criteria") or "Задача выполнена по смыслу").strip(),
        "carried": carried,
    }


def _load_outbox_tasks(outbox: Path, day: date) -> list[dict[str, Any]] | None:
    path = outbox / f"tasks_{day.isoformat()}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = data.get("tasks") or []
    result = []
    for i, t in enumerate(tasks, start=1):
        result.append(_normalize_task(t, t.get("id") or f"outbox-{i}", carried=0))
    return result or None


def _pool_slice(day: date, minutes_budget: int = 60) -> list[dict[str, Any]]:
    start = day.toordinal() % len(TASK_POOL)
    picked: list[dict[str, Any]] = []
    total = 0
    i = 0
    while total < minutes_budget and i < len(TASK_POOL):
        item = TASK_POOL[(start + i) % len(TASK_POOL)]
        if picked and picked[-1]["kind"] == item["kind"] and i + 1 < len(TASK_POOL):
            i += 1
            continue
        if total + item["minutes"] > minutes_budget + 5:
            i += 1
            continue
        picked.append(_normalize_task(item, f"pool-{(start + i) % len(TASK_POOL)}"))
        total += item["minutes"]
        i += 1
    if not picked:
        item = TASK_POOL[start]
        picked = [_normalize_task(item, f"pool-{start}")]
    return picked


def build_tasks_for_day(store: Store, outbox: Path, day: date) -> list[Any]:
    """Carry incomplete from yesterday, then fill from outbox or pool."""
    yesterday = day - timedelta(days=1)
    carried = []
    for row in store.incomplete_tasks(yesterday):
        rules = ""
        try:
            rules = row["rules"] or ""
        except (KeyError, IndexError):
            rules = ""
        carried.append(
            _normalize_task(
                {
                    "kind": row["kind"],
                    "title": f"(перенос) {row['title']}",
                    "minutes": row["minutes"],
                    "rules": rules,
                    "done_criteria": row["done_criteria"],
                },
                f"carry-{row['task_key']}",
                carried=1,
            )
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


def rebuild_tasks_for_day(store: Store, outbox: Path, day: date) -> list[Any]:
    """Drop today's incomplete tasks and rebuild from outbox/pool (keep completed)."""
    store.clear_incomplete_for_day(day)
    return build_tasks_for_day(store, outbox, day)


def format_tasks_message(day: date, rows: list[Any]) -> str:
    lines = [
        f"🗓 {day.isoformat()}",
        "Задачи до 19:00 МСК (всего ~1 час).",
        "Правила: делай по инструкции «Как сделать»; жми Done только когда выполнен критерий «Готово когда».",
        "Незавершённое автоматически перейдёт на завтра.",
        "",
    ]
    for i, r in enumerate(rows, start=1):
        status = "✅" if r["is_done"] else "⬜"
        kind = r["kind"]
        title = r["title"]
        minutes = r["minutes"]
        try:
            rules = (r["rules"] or "").strip()
        except (KeyError, IndexError):
            rules = ""
        done = r["done_criteria"]
        block = [f"{status} {i}. [{kind}] {title} ({minutes} мин)"]
        if rules:
            block.append(f"Как сделать: {rules}")
        block.append(f"Готово когда: {done}")
        lines.append("\n".join(block))
        lines.append("")
    lines.append("Кнопки: Done по задаче · Все Done · Статистика")
    lines.append("Обновить формулировки на сегодня: /tasks_refresh")
    text = "\n".join(lines).strip()
    # Telegram hard limit 4096
    if len(text) > 4000:
        text = text[:3990] + "\n…"
    return text
