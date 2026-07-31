#!/usr/bin/env bash
# Force-update trabajador bot code + prove jobs digest is concrete.
set -euo pipefail
cd /opt/trabajador

echo "== git sync =="
git fetch origin
git reset --hard origin/master
# keep .env (not in git)

echo "== code check =="
grep -n "ensure_today_digest\|_from_tracker" bot/services/jobs_digest.py || {
  echo "ERROR: new jobs_digest.py not on disk"
  exit 1
}

echo "== outbox files =="
ls -la data/outbox/jobs_*.md 2>/dev/null || echo "(no jobs_*.md yet)"

echo "== digest preview =="
.venv/bin/python - <<'PY'
from datetime import date
from zoneinfo import ZoneInfo
from pathlib import Path
from bot.services.jobs_digest import format_jobs_digest, ensure_today_digest
from bot.config import load_settings
s = load_settings()
day = date.today()  # server local; bot uses Moscow via TZ in handlers
# force Moscow calendar day like the bot
day = __import__("datetime").datetime.now(ZoneInfo(s.timezone)).date()
ensure_today_digest(s.outbox_dir, s.data_dir / "applications.csv", day)
text = format_jobs_digest(s.outbox_dir, s.data_dir / "applications.csv", day)
print(text[:1200])
if "Пока нет файла" in text:
    raise SystemExit("FAIL: still old placeholder text")
if "InfoJobs:" in text and "🔗" not in text:
    raise SystemExit("FAIL: only search links, no concrete jobs")
print("\nOK: concrete digest")
PY

echo "== restart bot =="
systemctl restart trabajador-bot
sleep 2
systemctl --no-pager --full status trabajador-bot | head -n 20
echo
echo "Now send /jobs in Telegram"
