#!/usr/bin/env bash
# One-shot repair for Hetzner VPS: stable Python + deps + systemd
set -euo pipefail

ROOT="/opt/trabajador"
cd "$ROOT"

echo "==> Prefer Python 3.12 if available"
PY=python3
if command -v python3.12 >/dev/null 2>&1; then
  PY=python3.12
elif command -v python3.11 >/dev/null 2>&1; then
  PY=python3.11
fi
echo "Using: $($PY --version)"

echo "==> Pull latest code"
git pull --ff-only || git pull

echo "==> Recreate venv"
rm -rf .venv
"$PY" -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

if [[ ! -f .env ]]; then
  echo "ERROR: missing $ROOT/.env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)"
  exit 1
fi

echo "==> Install/restart systemd unit"
cp deploy/trabajador-bot.service /etc/systemd/system/trabajador-bot.service
systemctl daemon-reload
systemctl enable trabajador-bot
systemctl restart trabajador-bot
sleep 2
systemctl --no-pager --full status trabajador-bot || true
echo
echo "==> Last logs:"
journalctl -u trabajador-bot -n 40 --no-pager
echo
echo "Done. Test /ping in Telegram. PC can be OFF — VPS must keep running."
