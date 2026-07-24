from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.config import Settings
from bot.db import Store
from bot.services.jobs_digest import format_jobs_digest
from bot.services.motivation import motivation_for
from bot.services.tasks import (
    build_tasks_for_day,
    format_tasks_message,
    rebuild_tasks_for_day,
)


def _tz(context: ContextTypes.DEFAULT_TYPE) -> ZoneInfo:
    settings: Settings = context.application.bot_data["settings"]
    return ZoneInfo(settings.timezone)


def _today(context: ContextTypes.DEFAULT_TYPE) -> date:
    return datetime.now(_tz(context)).date()


def _before_deadline(context: ContextTypes.DEFAULT_TYPE) -> bool:
    now = datetime.now(_tz(context))
    return (now.hour, now.minute) < (19, 0)


def tasks_keyboard(rows: list) -> InlineKeyboardMarkup:
    buttons = []
    for r in rows:
        if r["is_done"]:
            continue
        buttons.append(
            [InlineKeyboardButton(f"Done #{r['id']}", callback_data=f"done:{r['id']}")]
        )
    buttons.append([InlineKeyboardButton("Все Done", callback_data="done_all")])
    buttons.append([InlineKeyboardButton("Статистика", callback_data="stats")])
    return InlineKeyboardMarkup(buttons)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = context.application.bot_data["store"]
    chat = update.effective_chat
    if chat:
        store.set_meta("chat_id", str(chat.id))
    chat_id = chat.id if chat else "?"
    text = (
        "✅ Бот работает.\n\n"
        "Hola. Я trabajador — ассистент поиска работы в Испании.\n\n"
        f"Твой chat_id: {chat_id}\n"
        "Пропиши его в .env как TELEGRAM_CHAT_ID (если ещё не тот).\n\n"
        "Расписание (МСК):\n"
        "• 09:00 — задачи motivador (Done до 19:00)\n"
        "• 15:00 — топ вакансий (buscador outbox)\n"
        "• сб 11:00 — спокойная мотивация\n\n"
        "Команды: /tasks /tasks_refresh /jobs /motivation /stats /plan /ping"
    )
    # Plain text only: Markdown breaks on TELEGRAM_CHAT_ID underscores.
    if update.message:
        await update.message.reply_text(text)


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("pong — бот онлайн ✅")


async def cmd_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    store: Store = context.application.bot_data["store"]
    day = _today(context)
    rows = store.tasks_for_day(day)
    if not rows:
        rows = build_tasks_for_day(store, settings.outbox_dir, day)
    await update.message.reply_text(
        format_tasks_message(day, rows),
        reply_markup=tasks_keyboard(rows),
    )


async def cmd_tasks_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Rebuild today's incomplete tasks with clearer wording from pool/outbox."""
    settings: Settings = context.application.bot_data["settings"]
    store: Store = context.application.bot_data["store"]
    day = _today(context)
    rows = rebuild_tasks_for_day(store, settings.outbox_dir, day)
    await update.message.reply_text(
        "Обновил задачи на сегодня (незавершённые пересобраны).\n\n"
        + format_tasks_message(day, rows),
        reply_markup=tasks_keyboard(rows),
    )


async def cmd_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    day = _today(context)
    text = format_jobs_digest(
        settings.outbox_dir,
        settings.data_dir / "applications.csv",
        day,
    )
    await update.message.reply_text(text)


async def cmd_motivation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    text = motivation_for(_today(context), settings.outbox_dir)
    await update.message.reply_text(text)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    store: Store = context.application.bot_data["store"]
    s = store.stats_summary()
    rate = round(100 * s["completion_rate"])
    text = (
        "📊 Статистика (до 30 дней)\n"
        f"Дней в учёте: {s['days_tracked']}\n"
        f"Задачи: {s['tasks_done']}/{s['tasks_total']} ({rate}%)\n"
        f"Идеальных дней: {s['perfect_days']}\n"
        f"Закрыто до 19:00: {s['before_deadline_days']}\n"
        f"Текущая серия: {s['current_streak']}"
    )
    await update.message.reply_text(text)


async def cmd_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    path = settings.data_dir / "plan" / "current_sprint.md"
    if path.exists():
        body = path.read_text(encoding="utf-8").strip()
        await update.message.reply_text(f"Текущий спринт:\n\n{body[:3500]}")
    else:
        await update.message.reply_text(
            "Плана пока нет. В Cursor запусти скилл **planificador**."
        )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    store: Store = context.application.bot_data["store"]
    settings: Settings = context.application.bot_data["settings"]
    data = query.data or ""
    day = _today(context)
    before = _before_deadline(context)

    if data == "stats":
        s = store.stats_summary()
        rate = round(100 * s["completion_rate"])
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text(
            "📊 "
            f"{s['tasks_done']}/{s['tasks_total']} ({rate}%), "
            f"серия {s['current_streak']}"
        )
        return

    if data == "done_all":
        n = store.mark_all_done(day, before)
        rows = store.tasks_for_day(day)
        await query.edit_message_text(
            format_tasks_message(day, rows) + f"\n\nЗакрыто задач: {n}",
            reply_markup=tasks_keyboard(rows) if any(not r["is_done"] for r in rows) else None,
        )
        return

    if data.startswith("done:"):
        task_id = int(data.split(":", 1)[1])
        store.mark_done(task_id, before)
        rows = store.tasks_for_day(day)
        await query.edit_message_text(
            format_tasks_message(day, rows),
            reply_markup=tasks_keyboard(rows) if any(not r["is_done"] for r in rows) else None,
        )
        return


async def job_send_tasks(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    store: Store = context.application.bot_data["store"]
    chat_id = _resolve_chat_id(settings, store)
    if chat_id is None:
        return
    day = _today(context)
    day_s = day.isoformat()
    if store.get_meta(f"sent_tasks_{day_s}") == "1":
        return
    rows = build_tasks_for_day(store, settings.outbox_dir, day)
    await context.bot.send_message(
        chat_id=chat_id,
        text=format_tasks_message(day, rows),
        reply_markup=tasks_keyboard(rows),
    )
    store.set_meta(f"sent_tasks_{day_s}", "1")


async def job_send_jobs(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    store: Store = context.application.bot_data["store"]
    chat_id = _resolve_chat_id(settings, store)
    if chat_id is None:
        return
    day = _today(context)
    day_s = day.isoformat()
    if store.get_meta(f"sent_jobs_{day_s}") == "1":
        return
    text = format_jobs_digest(
        settings.outbox_dir,
        settings.data_dir / "applications.csv",
        day,
    )
    await context.bot.send_message(chat_id=chat_id, text=text)
    store.set_meta(f"sent_jobs_{day_s}", "1")


async def job_send_motivation(context: ContextTypes.DEFAULT_TYPE) -> None:
    settings: Settings = context.application.bot_data["settings"]
    store: Store = context.application.bot_data["store"]
    chat_id = _resolve_chat_id(settings, store)
    if chat_id is None:
        return
    day = _today(context)
    day_s = day.isoformat()
    if store.get_meta(f"sent_motivation_{day_s}") == "1":
        return
    text = motivation_for(day, settings.outbox_dir)
    await context.bot.send_message(chat_id=chat_id, text=text)
    store.set_meta(f"sent_motivation_{day_s}", "1")


def _resolve_chat_id(settings: Settings, store: Store) -> int | None:
    # Prefer chat_id from last /start (always correct for this user).
    raw = store.get_meta("chat_id")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return settings.chat_id


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log = __import__("logging").getLogger("trabajador")
    log.exception("Handler error: %s", context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Ошибка обработки команды. Бот всё ещё онлайн — попробуй /ping"
            )
        except Exception:
            pass


async def notify_online(application) -> None:
    """Send online ping and catch up missed daily digests for today (MSK)."""
    settings: Settings = application.bot_data["settings"]
    store: Store = application.bot_data["store"]
    chat_id = _resolve_chat_id(settings, store)
    if chat_id is None:
        return
    log = __import__("logging").getLogger("trabajador")
    try:
        await application.bot.send_message(
            chat_id=chat_id,
            text="✅ trabajador онлайн. Расписание МСК: задачи 09:00 · вакансии 15:00 · мотивация сб 11:00",
        )
    except Exception as exc:
        log.warning("Could not send online ping to chat_id=%s: %s", chat_id, exc)
        return

    # Catch-up so restart after 09:00/15:00 still delivers today's mailings once.
    now = datetime.now(ZoneInfo(settings.timezone))
    day = now.date()
    day_s = day.isoformat()

    if now.hour > 9 or (now.hour == 9 and now.minute >= 0):
        if store.get_meta(f"sent_tasks_{day_s}") != "1":
            rows = build_tasks_for_day(store, settings.outbox_dir, day)
            await application.bot.send_message(
                chat_id=chat_id,
                text=format_tasks_message(day, rows),
                reply_markup=tasks_keyboard(rows),
            )
            store.set_meta(f"sent_tasks_{day_s}", "1")

    if now.hour > 15 or (now.hour == 15 and now.minute >= 0):
        if store.get_meta(f"sent_jobs_{day_s}") != "1":
            text = format_jobs_digest(
                settings.outbox_dir,
                settings.data_dir / "applications.csv",
                day,
            )
            await application.bot.send_message(chat_id=chat_id, text=text)
            store.set_meta(f"sent_jobs_{day_s}", "1")
