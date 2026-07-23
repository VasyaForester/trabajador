# trabajador

Умный ассистент поиска работы в **Испании** для иностранца: Cursor skills + Telegram-бот.

Целевые роли: **AI Security Researcher**, **AI Engineer**, **AI Data Analyst**.  
Горизонт: оффер / переезд к **февралю 2027**, зарплата от **€50k** bruto/año.

## Возможности

| Компонент | Что делает |
|-----------|------------|
| **buscador** | Топ-5 вакансий (InfoJobs, Infoempleo, Indeed ES, Tecnoempleo, Jooble, LinkedIn public) |
| **entrevistador** | Gap-анализ под вакансию + mock-интервью (тон рекрутера) |
| **abogado** | Визы и разрешение на работу под кейс РФ → ES, со ссылками на официальные источники |
| **motivador** | Ежедневные задачи (~1ч) + субботняя мотивация |
| **planificador** | План на 180 дней спринтами 1–2 недели |
| **Telegram-бот** | Расписание, кнопки Done, статистика, дайджест вакансий |

## Telegram — расписание (МСК)

- **09:00** — задачи дня + Done (дедлайн 19:00; незавершённое переносится)
- **15:00** — вакансии из `data/outbox/jobs_YYYY-MM-DD.md`
- **сб 11:00** — спокойное мотивационное сообщение

Команды: `/start` `/ping` `/tasks` `/jobs` `/motivation` `/stats` `/plan`

## Быстрый старт

### 1. Клонировать и зависимости

```powershell
git clone https://github.com/VasyaForester/trabajador.git
cd trabajador
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Настроить Telegram

1. Создайте бота у [@BotFather](https://t.me/BotFather).
2. Скопируйте env:

```powershell
copy .env.example .env
```

3. Впишите в `.env`:

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=
TZ=Europe/Moscow
```

4. Запуск:

```powershell
.\.venv\Scripts\python.exe run_bot.py
```

5. В Telegram: `/start` → скопируйте `chat_id` в `.env` → перезапустите бота.  
Проверка: `/ping`.

> Не коммитьте `.env`. Не кладите токен в `.env.example`. Держите **один** процесс бота.

### 3. Cursor skills

Skills лежат в `.cursor/skills/`. В чате Cursor вызовите по имени, например:

- `buscador` — собрать топ-5 и записать outbox + `data/applications.csv`
- `entrevistador` + текст вакансии
- `abogado` — путь к work authorization
- `planificador` / `motivador`

Профиль кандидата: `profile/profile.yaml`, `profile/cv.md`.

## Структура

```
.cursor/skills/     # buscador, entrevistador, abogado, motivador, planificador
bot/                # Telegram bot
profile/            # профиль и CV summary
data/
  applications.csv  # трекер вакансий
  outbox/           # jobs_*, tasks_*, motivation_* для бота
  plan/             # roadmap 180 дней и текущий спринт
```

## Связка buscador → Telegram

1. В Cursor: скилл **buscador** → `data/outbox/jobs_YYYY-MM-DD.md`
2. В 15:00 бот отправляет дайджест в Telegram
3. Опционально: `tasks_YYYY-MM-DD.json`, `motivation_YYYY-MM-DD.md`

## Лицензия

Личный проект. Используйте на свой риск; юридические советы сверяйте с официальными источниками.
