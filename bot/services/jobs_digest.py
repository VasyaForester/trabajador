from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus


def _read_outbox_day(outbox: Path, day: date) -> str | None:
    path = outbox / f"jobs_{day.isoformat()}.md"
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        return text or None
    return None


def _latest_outbox(outbox: Path) -> tuple[date, str] | None:
    """Most recent jobs_YYYY-MM-DD.md (repeats allowed when today missing)."""
    if not outbox.exists():
        return None
    best: tuple[date, Path] | None = None
    for path in outbox.glob("jobs_*.md"):
        m = re.fullmatch(r"jobs_(\d{4}-\d{2}-\d{2})\.md", path.name)
        if not m:
            continue
        try:
            d = date.fromisoformat(m.group(1))
        except ValueError:
            continue
        if best is None or d > best[0]:
            best = (d, path)
    if best is None:
        return None
    text = best[1].read_text(encoding="utf-8").strip()
    return (best[0], text) if text else None


def _from_tracker(applications_csv: Path, limit: int = 5) -> str | None:
    """Build Telegram-style digest from newest tracker rows (repeats OK)."""
    if not applications_csv.exists():
        return None
    with applications_csv.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None

    # Newest first; skip explicit skips / closed if noted
    rows = list(reversed(rows))
    picked: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for r in rows:
        url = (r.get("url") or "").strip()
        if not url or url in seen_urls:
            continue
        if (r.get("status") or "").lower() in {"skip", "closed", "rejected"}:
            continue
        seen_urls.add(url)
        picked.append(r)
        if len(picked) >= limit:
            break
    if not picked:
        return None

    blocks = []
    for i, r in enumerate(picked, start=1):
        title = (r.get("title") or "Role").strip()
        company = (r.get("company") or "?").strip()
        location = (r.get("location") or "Spain").strip()
        mode = (r.get("work_mode") or "unknown").strip()
        salary = (r.get("salary") or "n/d").strip()
        visa = (r.get("visa_sponsorship") or "unknown").strip()
        url = (r.get("url") or "").strip()
        blocks.append(
            f"{i}. {title} — {company}\n"
            f"📍 {location} | {mode}\n"
            f"💰 {salary}\n"
            f"Visa sponsorship: {visa}\n"
            f"🔗 {url}"
        )
    return "\n\n".join(blocks)


def _search_links() -> str:
    q = quote_plus('AI Security OR AI Engineer OR "Data Analyst" Spain')
    links = [
        f"InfoJobs: https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword={q}",
        f"Indeed ES: https://es.indeed.com/jobs?q={quote_plus('AI Engineer OR AI Security')}&l=España",
        f"Tecnoempleo: https://www.tecnoempleo.com/busqueda-empleo.php?te={quote_plus('AI')}",
        f"Infoempleo: https://www.infoempleo.com/trabajo/",
        f"Jooble: https://es.jooble.org/SearchResult?ukw={quote_plus('AI Security')}",
        f"LinkedIn (public): https://www.linkedin.com/jobs/search/?keywords={quote_plus('AI Security')}&location={quote_plus('Spain')}",
    ]
    return "\n".join(f"• {x}" for x in links)


def ensure_today_digest(outbox: Path, applications_csv: Path, day: date) -> Path | None:
    """
    Make sure jobs_YYYY-MM-DD.md exists for today.
    Copies latest outbox or builds from tracker (repeats OK).
    """
    outbox.mkdir(parents=True, exist_ok=True)
    today_path = outbox / f"jobs_{day.isoformat()}.md"
    if today_path.exists() and today_path.read_text(encoding="utf-8").strip():
        return today_path

    latest = _latest_outbox(outbox)
    if latest:
        _src_day, body = latest
        # strip a leading "# Jobs ..." header if present; rewrite for today
        lines = body.splitlines()
        if lines and lines[0].startswith("# Jobs"):
            body = "\n".join(lines[1:]).strip()
        today_path.write_text(f"# Jobs {day.isoformat()}\n\n{body}\n", encoding="utf-8")
        return today_path

    tracker = _from_tracker(applications_csv, limit=5)
    if tracker:
        today_path.write_text(f"# Jobs {day.isoformat()}\n\n{tracker}\n", encoding="utf-8")
        return today_path
    return None


def format_jobs_digest(outbox: Path, applications_csv: Path, day: date) -> str:
    """
    Always prefer concrete vacancies:
    1) ensure/create today's outbox (from latest or tracker)
    2) search links only if tracker/outbox empty
    """
    ensure_today_digest(outbox, applications_csv, day)
    today = _read_outbox_day(outbox, day)
    if today:
        return f"🔍 Вакансии на {day.isoformat()} (топ под тебя)\n\n{today}"

    return (
        f"🔍 Вакансии на {day.isoformat()}\n\n"
        "Трекер и outbox пусты. Запусти **buscador** в Cursor.\n\n"
        "Быстрые поиски:\n"
        f"{_search_links()}"
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
