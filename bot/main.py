from __future__ import annotations

import asyncio
import logging
import sys

from telegram.ext import Application, CallbackQueryHandler, CommandHandler

from bot.config import load_settings
from bot.db import Store
from bot.handlers import (
    cmd_jobs,
    cmd_motivation,
    cmd_ping,
    cmd_plan,
    cmd_start,
    cmd_stats,
    cmd_tasks,
    cmd_tasks_refresh,
    job_send_jobs,
    job_send_motivation,
    job_send_tasks,
    notify_online,
    on_callback,
    on_error,
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("trabajador")


def _ensure_event_loop() -> None:
    """Python 3.14+: get_event_loop() no longer creates a loop automatically."""
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)


def main() -> None:
    _ensure_event_loop()
    if sys.version_info >= (3, 14):
        log.warning(
            "Python %s.%s detected; prefer 3.12 on VPS if problems persist",
            sys.version_info.major,
            sys.version_info.minor,
        )

    settings = load_settings()
    settings.outbox_dir.mkdir(parents=True, exist_ok=True)
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)

    store = Store(settings.db_path)
    app = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(notify_online)
        .build()
    )
    app.bot_data["settings"] = settings
    app.bot_data["store"] = store

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("tasks", cmd_tasks))
    app.add_handler(CommandHandler("tasks_refresh", cmd_tasks_refresh))
    app.add_handler(CommandHandler("jobs", cmd_jobs))
    app.add_handler(CommandHandler("motivation", cmd_motivation))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("plan", cmd_plan))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_error_handler(on_error)

    jq = app.job_queue
    if jq is None:
        raise RuntimeError("JobQueue is unavailable. Install: pip install 'python-telegram-bot[job-queue]'")

    from datetime import time
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(settings.timezone)
    jq.run_daily(job_send_tasks, time=time(9, 0, tzinfo=tz), name="daily_tasks")
    jq.run_daily(job_send_jobs, time=time(15, 0, tzinfo=tz), name="daily_jobs")
    jq.run_daily(
        job_send_motivation,
        time=time(11, 0, tzinfo=tz),
        days=(5,),
        name="weekly_motivation",
    )

    log.info(
        "Bot starting. TZ=%s schedules: tasks 09:00, jobs 15:00, motivation Sat 11:00",
        settings.timezone,
    )
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()
