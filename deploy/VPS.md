# Deploy Telegram bot on Hetzner VPS

The bot must run **only on the VPS**, not on your Windows PC.  
If the PC is off and Telegram is silent, the process on the server is not running (or never started as a service).

## 1. On your Windows PC — stop local bot

1. Close any terminal with `run_bot.py`.
2. Remove Startup shortcut (if present):

```powershell
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\TrabajadorTelegramBot.lnk" -ErrorAction SilentlyContinue
```

3. Do **not** start `run_bot.py` at home while the VPS is polling (Telegram Conflict).

## 2. On Hetzner (SSH)

Replace paths/user if different.

```bash
sudo apt update
sudo apt install -y python3 python3-venv git

sudo useradd -r -m -d /opt/trabajador -s /bin/bash trabajador || true
sudo mkdir -p /opt/trabajador
sudo chown -R trabajador:trabajador /opt/trabajador

# as trabajador or with correct ownership:
cd /opt/trabajador
git clone https://github.com/VasyaForester/trabajador.git .
# or: git pull if already cloned

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

nano .env
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...
# TZ=Europe/Moscow
```

Install systemd unit:

```bash
sudo cp deploy/trabajador-bot.service /etc/systemd/system/trabajador-bot.service
# edit User=/WorkingDirectory= if your paths differ
sudo systemctl daemon-reload
sudo systemctl enable --now trabajador-bot
sudo systemctl status trabajador-bot
```

## 3. Verify

```bash
sudo journalctl -u trabajador-bot -f
```

You should see `Application started`. Then in Telegram: `/ping`.

Turn off your PC and wait 1–2 minutes — `/ping` must still work.

## 4. Update code later

```bash
cd /opt/trabajador
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart trabajador-bot
```

## Common failures

| Symptom | Cause |
|---------|--------|
| Works only when PC is on | Bot still runs on Windows, not on VPS |
| `Conflict: terminated by other getUpdates` | Two instances (PC + VPS) |
| `Unauthorized` | Bad/revoked token in VPS `.env` |
| Service exits immediately | Wrong path, missing `.venv`, or missing `.env` |
