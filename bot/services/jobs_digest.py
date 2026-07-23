from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus


SEARCH_QUERIES = [
    "AI Security Researcher",
    "AI Engineer",
    "AI Data Analyst",
    "Machine Learning Security",
    "LLM Security",
]


def _read_outbox(outbox: Path, day: date) -> str | None:
    path = outbox / f"jobs_{day.isoformat()}.md"
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        return text or None
    return None


def _search_links() -> str:
    q = quote_plus("AI Security OR AI Engineer OR \"Data Analyst\" Spain")
    links = [
        f"InfoJobs: https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword={q}",
        f"Indeed ES: https://es.indeed.com/jobs?q={quote_plus('AI Engineer OR AI Security')}&l=España",
        f"Tecnoempleo: https://www.tecnoempleo.com/busqueda-empleo.php?te={quote_plus('AI')}",
        f"Infoempleo: https://www.infoempleo.com/trabajo/",
        f"Jooble: https://es.jooble.org/SearchResult?ukw={quote_plus('AI Security')}",
        f"LinkedIn (public): https://www.linkedin.com/jobs/search/?keywords={quote_plus('AI Security')}&location={quote_plus('Spain')}",
    ]
    return "\n".join(f"• {x}" for x in links)


def format_jobs_digest(outbox: Path, applications_csv: Path, day: date) -> str:
    out = _read_outbox(outbox, day)
    if out:
        header = f"🔍 Вакансии на {day.isoformat()} (топ под тебя)\n\n"
        return header + out

    # Fallback: remind to run buscador + deep links + recent tracker count
    tracked = 0
    if applications_csv.exists():
        with applications_csv.open(encoding="utf-8", newline="") as f:
            tracked = max(0, sum(1 for _ in csv.DictReader(f)))

    return (
        f"🔍 Вакансии на {day.isoformat()}\n\n"
        "Пока нет файла `data/outbox/jobs_YYYY-MM-DD.md`.\n"
        "В Cursor запусти скилл **buscador** — он соберёт топ-5 и запишет outbox; "
        "завтра/сегодня после этого дайджест станет конкретным.\n\n"
        f"В трекере сейчас записей: {tracked}\n\n"
        "Быстрые поиски:\n"
        f"{_search_links()}\n\n"
        "Формат каждой вакансии:\n"
        "название · зарплата · город · формат · Visa sponsorship · ссылка"
    )


def append_application(
    applications_csv: Path,
    *,
    day: date,
    title: str,
    company: str,
    location: str,
    work_mode: str,
    salary: str,
    visa: str,
    url: str,
    source: str,
) -> None:
    applications_csv.parent.mkdir(parents=True, exist_ok=True)
    new_file = not applications_csv.exists() or applications_csv.stat().st_size == 0
    with applications_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "date_found",
                "title",
                "company",
                "location",
                "work_mode",
                "salary",
                "visa_sponsorship",
                "url",
                "source",
                "status",
                "notes",
            ],
        )
        if new_file:
            writer.writeheader()
        writer.writerow(
            {
                "date_found": day.isoformat(),
                "title": title,
                "company": company,
                "location": location,
                "work_mode": work_mode,
                "salary": salary,
                "visa_sponsorship": visa,
                "url": url,
                "source": source,
                "status": "found",
                "notes": "",
            }
        )
