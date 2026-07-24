from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_key TEXT NOT NULL,
  day TEXT NOT NULL,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  minutes INTEGER NOT NULL,
  done_criteria TEXT NOT NULL,
  rules TEXT NOT NULL DEFAULT '',
  is_done INTEGER NOT NULL DEFAULT 0,
  carried INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  done_at TEXT,
  UNIQUE(task_key, day)
);

CREATE TABLE IF NOT EXISTS daily_stats (
  day TEXT PRIMARY KEY,
  total INTEGER NOT NULL,
  done INTEGER NOT NULL,
  completed_before_deadline INTEGER NOT NULL DEFAULT 0
);
"""


class Store:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            cols = {
                str(r["name"])
                for r in conn.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "rules" not in cols:
                conn.execute("ALTER TABLE tasks ADD COLUMN rules TEXT NOT NULL DEFAULT ''")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def get_meta(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
            return None if row is None else str(row["value"])

    def replace_day_tasks(self, day: date, tasks: list[dict[str, Any]]) -> list[sqlite3.Row]:
        day_s = day.isoformat()
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE day=? AND is_done=0", (day_s,))
            for t in tasks:
                conn.execute(
                    """
                    INSERT INTO tasks(task_key, day, kind, title, minutes, done_criteria, rules, is_done, carried, created_at)
                    VALUES(?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ON CONFLICT(task_key, day) DO UPDATE SET
                      kind=excluded.kind,
                      title=excluded.title,
                      minutes=excluded.minutes,
                      done_criteria=excluded.done_criteria,
                      rules=excluded.rules,
                      carried=excluded.carried
                    """,
                    (
                        t["task_key"],
                        day_s,
                        t["kind"],
                        t["title"],
                        t["minutes"],
                        t["done_criteria"],
                        t.get("rules") or "",
                        int(t.get("carried", 0)),
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
            rows = conn.execute(
                "SELECT * FROM tasks WHERE day=? ORDER BY id", (day_s,)
            ).fetchall()
            self._refresh_daily_stats(conn, day_s)
            return rows

    def incomplete_tasks(self, day: date) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM tasks WHERE day=? AND is_done=0 ORDER BY id",
                (day.isoformat(),),
            ).fetchall()

    def clear_incomplete_for_day(self, day: date) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM tasks WHERE day=? AND is_done=0",
                (day.isoformat(),),
            )
            self._refresh_daily_stats(conn, day.isoformat())
            return int(cur.rowcount or 0)

    def tasks_for_day(self, day: date) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM tasks WHERE day=? ORDER BY id",
                (day.isoformat(),),
            ).fetchall()

    def mark_done(self, task_id: int, before_deadline: bool) -> sqlite3.Row | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None:
                return None
            if row["is_done"]:
                return row
            conn.execute(
                "UPDATE tasks SET is_done=1, done_at=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), task_id),
            )
            self._refresh_daily_stats(conn, row["day"], bump_deadline=before_deadline)
            return conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()

    def mark_all_done(self, day: date, before_deadline: bool) -> int:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM tasks WHERE day=? AND is_done=0",
                (day.isoformat(),),
            ).fetchall()
            now = datetime.now().isoformat(timespec="seconds")
            for r in rows:
                conn.execute(
                    "UPDATE tasks SET is_done=1, done_at=? WHERE id=?",
                    (now, r["id"]),
                )
            self._refresh_daily_stats(conn, day.isoformat(), bump_deadline=before_deadline and bool(rows))
            return len(rows)

    def _refresh_daily_stats(
        self, conn: sqlite3.Connection, day_s: str, bump_deadline: bool = False
    ) -> None:
        total = conn.execute(
            "SELECT COUNT(*) AS c FROM tasks WHERE day=?", (day_s,)
        ).fetchone()["c"]
        done = conn.execute(
            "SELECT COUNT(*) AS c FROM tasks WHERE day=? AND is_done=1", (day_s,)
        ).fetchone()["c"]
        existing = conn.execute(
            "SELECT completed_before_deadline FROM daily_stats WHERE day=?", (day_s,)
        ).fetchone()
        completed_before = int(existing["completed_before_deadline"]) if existing else 0
        if bump_deadline and done == total and total > 0:
            completed_before = 1
        conn.execute(
            """
            INSERT INTO daily_stats(day, total, done, completed_before_deadline)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(day) DO UPDATE SET
              total=excluded.total,
              done=excluded.done,
              completed_before_deadline=excluded.completed_before_deadline
            """,
            (day_s, total, done, completed_before),
        )

    def stats_summary(self, limit_days: int = 30) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM daily_stats ORDER BY day DESC LIMIT ?",
                (limit_days,),
            ).fetchall()
            days = list(rows)
            total_tasks = sum(r["total"] for r in days)
            done_tasks = sum(r["done"] for r in days)
            perfect = sum(1 for r in days if r["total"] and r["done"] == r["total"])
            before = sum(1 for r in days if r["completed_before_deadline"])
            streak = 0
            for r in days:
                if r["total"] and r["done"] == r["total"]:
                    streak += 1
                else:
                    break
            return {
                "days_tracked": len(days),
                "tasks_total": total_tasks,
                "tasks_done": done_tasks,
                "completion_rate": (done_tasks / total_tasks) if total_tasks else 0.0,
                "perfect_days": perfect,
                "before_deadline_days": before,
                "current_streak": streak,
            }
