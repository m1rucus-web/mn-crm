# День 1 — Промпты для Claude Code (v2)
# Версия FOUNDATION: 4.9 (2026-02-27)
# Копируй по одному. После каждого блока — /clear.
# Работаем под root (sudo su).

---

## ⚠️ Подготовка перед Днём 1 (вручную, НЕ через Claude Code)

Перед запуском первого промпта убедись, что на сервере лежат:

```
/opt/mn/FOUNDATION.md              ← архитектурный документ (v4.9)
/opt/mn/avito-bot-CLAUDE.md        ← CLAUDE.md для Авито-бота (скопируешь в сервис позже)
/opt/mn/crm-core-CLAUDE.md         ← CLAUDE.md для CRM (скопируешь в сервис позже)
/opt/mn/shared/config/             ← 10 JSON-конфигов:
  pricelist.json, company.json, employees.json, work_hours.json,
  ai_models.json, tax_calendar.json, templates.json, objections.json,
  brand_voice.json, services_catalog.json
/opt/mn/shared/templates/          ← договор (.docx) + логотип (.png/.jpg)
```

Если чего-то нет — загрузи. Claude Code НЕ должен создавать эти файлы.

---

## Промпт 1: Разведка (3 мин)

```
Проверь текущее состояние сервера. Для каждого пункта — ДА/НЕТ:

1. test -f /opt/mn/FOUNDATION.md && echo "FOUNDATION: ДА" || echo "FOUNDATION: НЕТ — СТОП!"
2. ls /opt/mn/shared/config/*.json 2>/dev/null | wc -l  (ожидаем: 10)
3. ls /opt/mn/shared/templates/ 2>/dev/null  (ожидаем: договор + логотип)
4. test -f /opt/mn/avito-bot-CLAUDE.md && echo "avito CLAUDE.md: ДА" || echo "avito CLAUDE.md: НЕТ"
5. test -f /opt/mn/crm-core-CLAUDE.md && echo "crm CLAUDE.md: ДА" || echo "crm CLAUDE.md: НЕТ"
6. python3.12 --version  (ожидаем: 3.12.x. Если нет — СТОП, установи python3.12)
7. id mn-avito 2>/dev/null && echo "mn-avito: существует" || echo "mn-avito: НЕТ"
8. id mn-crm 2>/dev/null && echo "mn-crm: существует" || echo "mn-crm: НЕТ"
9. test -d /opt/mn/avito-bot/ && echo "avito-bot/: существует" || echo "avito-bot/: НЕТ"
10. test -d /opt/mn/crm-core/ && echo "crm-core/: существует" || echo "crm-core/: НЕТ"

Если FOUNDATION.md или python3.12 отсутствует — выведи СТОП и больше ничего не делай.

НЕ СОЗДАВАЙ НИЧЕГО. Только отчёт.
```

> ☝️ Если есть СТОП — исправь вручную. Все 10 JSON на месте? FOUNDATION.md есть? Python3.12?
> Потом: `/clear`

---

## Промпт 2: Структура, пользователи, git init (5 мин)

```
Создай инфраструктуру по FOUNDATION.md раздел 1.

ШАГ 1 — Директории:
mkdir -p /opt/mn/{shared/config,shared/templates,backups}
mkdir -p /opt/mn/avito-bot/{src/api,src/services,src/workers,scripts,tests,data,logs}
mkdir -p /opt/mn/crm-core/{src/api,src/web/templates,src/services,src/workers,scripts,tests,data,logs}
touch /opt/mn/shared/healthcheck.sh && chmod +x /opt/mn/shared/healthcheck.sh

ШАГ 2 — Linux-пользователи (если ещё не существуют):
id mn-avito 2>/dev/null || useradd -r -s /bin/bash -d /opt/mn/avito-bot mn-avito
id mn-crm 2>/dev/null || useradd -r -s /bin/bash -d /opt/mn/crm-core mn-crm

ШАГ 3 — Права:
chown -R mn-avito:mn-avito /opt/mn/avito-bot && chmod 700 /opt/mn/avito-bot
chown -R mn-crm:mn-crm /opt/mn/crm-core && chmod 700 /opt/mn/crm-core
chown -R root:root /opt/mn/shared && chmod -R 755 /opt/mn/shared
chown root:root /opt/mn/backups && chmod 700 /opt/mn/backups

ШАГ 4 — Git init (в обоих сервисах):
sudo -u mn-avito bash -c "cd /opt/mn/avito-bot && git init && git config user.email 'bot@mn.local' && git config user.name 'MN Avito Bot'"
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && git init && git config user.email 'crm@mn.local' && git config user.name 'MN CRM Core'"

ШАГ 5 — Скопируй CLAUDE.md в сервисы:
cp /opt/mn/avito-bot-CLAUDE.md /opt/mn/avito-bot/CLAUDE.md && chown mn-avito:mn-avito /opt/mn/avito-bot/CLAUDE.md
cp /opt/mn/crm-core-CLAUDE.md /opt/mn/crm-core/CLAUDE.md && chown mn-crm:mn-crm /opt/mn/crm-core/CLAUDE.md

ШАГ 6 — Проверка изоляции:
sudo -u mn-avito ls /opt/mn/crm-core/  → ожидаем Permission denied
sudo -u mn-crm ls /opt/mn/avito-bot/   → ожидаем Permission denied
sudo -u mn-avito cat /opt/mn/shared/config/pricelist.json → ожидаем: читается
```

> Проверь вывод. Permission denied где надо? Git init прошёл? `/clear`

---

## Промпт 3: JSON-конфиги (3 мин)

```
Проверь, что в /opt/mn/shared/config/ лежат все 10 JSON-файлов:
1. pricelist.json
2. company.json
3. employees.json
4. work_hours.json
5. ai_models.json
6. tax_calendar.json
7. templates.json
8. objections.json
9. brand_voice.json
10. services_catalog.json

Для каждого файла выполни:
  python3.12 -c "import json; d=json.load(open('/opt/mn/shared/config/ФАЙЛ')); print('OK')" 
  → если ошибка — сообщи какой файл битый.

Также проверь наличие полей со значением "ЗАПОЛНИТЬ":
  grep -r "ЗАПОЛНИТЬ" /opt/mn/shared/config/ || echo "Нет незаполненных полей"

Проверь /opt/mn/shared/templates/:
  ls -la /opt/mn/shared/templates/  → есть .docx и .png/.jpg?

НЕ СОЗДАВАЙ НИЧЕГО. Только отчёт: что на месте, что нужно заполнить.
```

> Если JSON битый — исправь вручную. «ЗАПОЛНИТЬ» в company.json — ожидаемо, заполнишь позже. `/clear`

---

## Промпт 4: venv + FastAPI-каркас для Авито-бота (10 мин)

```
Все команды выполняй через sudo -u mn-avito bash -c "...".
Путь к python и pip — абсолютный через venv: /opt/mn/avito-bot/.venv/bin/python, /opt/mn/avito-bot/.venv/bin/pip.

ШАГ 1 — venv:
sudo -u mn-avito bash -c "python3.12 -m venv /opt/mn/avito-bot/.venv"

ШАГ 2 — requirements.txt:
Создай файл /opt/mn/avito-bot/requirements.txt:
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy[asyncio]==2.0.*
aiosqlite==0.20.*
httpx==0.28.*
loguru==0.7.*
apscheduler==3.10.*
pydantic-settings==2.7.*
python-dotenv==1.0.*

Установи:
sudo -u mn-avito bash -c "/opt/mn/avito-bot/.venv/bin/pip install -r /opt/mn/avito-bot/requirements.txt"

ШАГ 3 — .gitignore (ОБЯЗАТЕЛЬНО до первого коммита):
Создай /opt/mn/avito-bot/.gitignore:
.env
.env.*
*.db
*.db-wal
*.db-shm
__pycache__/
.venv/
logs/
*.pyc

ШАГ 4 — .env.example (шаблон, БЕЗ реальных ключей — этот файл коммитится):
Создай /opt/mn/avito-bot/.env.example:
AVITO_CLIENT_ID=
AVITO_CLIENT_SECRET=
AVITO_USER_ID=
OPENROUTER_API_KEY=
WHISPER_API_KEY=
DADATA_API_KEY=
DADATA_SECRET_KEY=
CRM_INTERNAL_KEY=
CRM_URL=http://localhost:8003
BOT_DB_PATH=data/bot.db
LOG_LEVEL=INFO
APP_VERSION=0.1.0

Скопируй .env.example → .env (этот файл НЕ попадёт в git благодаря .gitignore):
sudo -u mn-avito bash -c "cp /opt/mn/avito-bot/.env.example /opt/mn/avito-bot/.env"

ШАГ 5 — Минимальный каркас:
Создай файлы (все под пользователем mn-avito):
- src/__init__.py (пустой)
- src/settings.py: pydantic-settings, читает все переменные из .env (включая APP_VERSION)
- src/main.py: FastAPI app с lifespan. 
  GET /health → 200 {"service": "avito-bot", "status": "ok", "version": settings.APP_VERSION}
  Настрой loguru в lifespan: запись в logs/app.log, ротация 10MB, retention 7 дней.

ШАГ 6 — Проверка запуска:
sudo -u mn-avito bash -c "cd /opt/mn/avito-bot && .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8001 &"
sleep 2
curl http://127.0.0.1:8001/health
# Ожидаем: {"service":"avito-bot","status":"ok","version":"0.1.0"}
pkill -f "uvicorn src.main:app.*8001"

ШАГ 7 — Коммит:
sudo -u mn-avito bash -c "cd /opt/mn/avito-bot && git add -A && git commit -m 'init: каркас Авито-бота, FastAPI + health + loguru'"
```

> Проверь: health отвечает с version? .env НЕ в git (git status)? `/clear`

---

## Промпт 5: venv + FastAPI-каркас для CRM (10 мин)

```
Все команды выполняй через sudo -u mn-crm bash -c "...".
Путь к python и pip — абсолютный: /opt/mn/crm-core/.venv/bin/python, /opt/mn/crm-core/.venv/bin/pip.

ШАГ 1 — venv:
sudo -u mn-crm bash -c "python3.12 -m venv /opt/mn/crm-core/.venv"

ШАГ 2 — requirements.txt:
Создай /opt/mn/crm-core/requirements.txt:
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy[asyncio]==2.0.*
aiosqlite==0.20.*
httpx==0.28.*
loguru==0.7.*
apscheduler==3.10.*
pydantic-settings==2.7.*
python-dotenv==1.0.*
jinja2==3.1.*
docxtpl==0.18.*
python-multipart==0.0.*

Установи:
sudo -u mn-crm bash -c "/opt/mn/crm-core/.venv/bin/pip install -r /opt/mn/crm-core/requirements.txt"

ШАГ 3 — .gitignore:
Создай /opt/mn/crm-core/.gitignore:
.env
.env.*
*.db
*.db-wal
*.db-shm
__pycache__/
.venv/
logs/
*.pyc

ШАГ 4 — .env.example:
Создай /opt/mn/crm-core/.env.example:
AVITO_INTERNAL_KEY=
DADATA_API_KEY=
DADATA_SECRET_KEY=
TELEGRAM_BOT_TOKEN=
ADMIN_CHAT_ID=
CRM_DB_PATH=data/crm.db
AVITO_BOT_URL=http://localhost:8001
LOG_LEVEL=INFO
APP_VERSION=0.1.0

Скопируй → .env:
sudo -u mn-crm bash -c "cp /opt/mn/crm-core/.env.example /opt/mn/crm-core/.env"

ШАГ 5 — Каркас:
- src/__init__.py (пустой)
- src/settings.py: pydantic-settings из .env (включая APP_VERSION)
- src/main.py: FastAPI + lifespan.
  GET /health → 200 {"service": "crm-core", "status": "ok", "version": settings.APP_VERSION}
  loguru → logs/app.log, ротация 10MB, retention 7 дней.

ШАГ 6 — Проверка:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8003 &"
sleep 2
curl http://127.0.0.1:8003/health
pkill -f "uvicorn src.main:app.*8003"

ШАГ 7 — Коммит:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && git add -A && git commit -m 'init: каркас CRM-ядра, FastAPI + health + loguru'"
```

> Проверь: version в health? .env не в git? `/clear`

---

## Промпт 6: База данных Авито-бота (10 мин)

```
Все команды — через sudo -u mn-avito bash -c "...".
Python — через /opt/mn/avito-bot/.venv/bin/python.

ПРЕДУСЛОВИЕ — проверь что FOUNDATION.md доступен:
test -f /opt/mn/FOUNDATION.md || echo "СТОП: FOUNDATION.md не найден!"
Если не найден — остановись и сообщи.

Создай /opt/mn/avito-bot/scripts/init_db.py — инициализация bot.db.
Читай схему СТРОГО из FOUNDATION.md раздел 6 (bot.db). Не выдумывай таблиц.

ВАЖНО:
- Все CREATE TABLE — с IF NOT EXISTS (идемпотентность при повторном запуске)
- Перед созданием: если data/bot.db уже существует — сделать бэкап:
  shutil.copy("data/bot.db", f"data/bot.db.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}")

Таблицы (5 штук):
- leads (с consent_given_at, ai_enabled)
- messages (с ai_tokens_in/out, ai_cost_usd — прямо в этой таблице)
- employees
- topic_mapping
- outbox (с aggregate_key, idempotency_key UNIQUE)

Индексы (с IF NOT EXISTS):
- idx_outbox_pending (WHERE status='pending')
- idx_outbox_aggregate (WHERE status IN ('pending','failed'))
- idx_messages_lead
- idx_leads_status
- idx_leads_created

PRAGMA (выполнить ПОСЛЕ создания таблиц):
- journal_mode=WAL
- busy_timeout=5000

Также создай src/db.py:
- SQLAlchemy async engine (aiosqlite)
- async session factory
- PRAGMA WAL + busy_timeout при каждом подключении (через event listener)

Запусти init_db.py:
sudo -u mn-avito bash -c "cd /opt/mn/avito-bot && .venv/bin/python scripts/init_db.py"

Проверка:
sqlite3 /opt/mn/avito-bot/data/bot.db ".tables"  → ровно 5 таблиц
sqlite3 /opt/mn/avito-bot/data/bot.db "PRAGMA journal_mode;"  → wal
sqlite3 /opt/mn/avito-bot/data/bot.db ".schema leads"  → совпадает с FOUNDATION?
sqlite3 /opt/mn/avito-bot/data/bot.db ".schema messages"  → есть ai_tokens_in, ai_tokens_out, ai_cost_usd?
sqlite3 /opt/mn/avito-bot/data/bot.db ".schema outbox"  → есть aggregate_key, idempotency_key?

Коммит:
sudo -u mn-avito bash -c "cd /opt/mn/avito-bot && git add -A && git commit -m 'init: bot.db — 5 таблиц + db.py engine'"
```

> Проверь .tables (ровно 5). Сохрани вывод .schema outbox — понадобится для сверки с CRM. `/clear`

---

## Промпт 7: База данных CRM (10 мин)

```
Все команды — через sudo -u mn-crm bash -c "...".
Python — через /opt/mn/crm-core/.venv/bin/python.

ПРЕДУСЛОВИЕ:
test -f /opt/mn/FOUNDATION.md || echo "СТОП: FOUNDATION.md не найден!"

Создай /opt/mn/crm-core/scripts/init_db.py — инициализация crm.db.
Читай схему СТРОГО из FOUNDATION.md раздел 6 (crm.db). Не выдумывай таблиц.

ВАЖНО:
- Все CREATE TABLE — с IF NOT EXISTS
- Если data/crm.db существует — бэкап перед созданием
- Версия FOUNDATION: 4.9 (2026-02-27)

Таблицы (8 штук):
- clients (с drip_active, drip_campaign_step, drip_next_at, deleted_at, source_url, UNIQUE(source, source_id))
- employees (с status, substitute_id, max_clients)
- history (action, details JSON, auto flag)
- tasks (с deleted_at)
- onboarding_documents
- processed_keys
- outbox (с aggregate_key, idempotency_key UNIQUE)
- drip_events

Индексы (все с IF NOT EXISTS):
- idx_clients_responsible (WHERE deleted_at IS NULL)
- idx_clients_pipeline (WHERE deleted_at IS NULL)
- idx_clients_inn (WHERE deleted_at IS NULL)
- idx_clients_inn_unique — UNIQUE WHERE inn IS NOT NULL AND deleted_at IS NULL
- idx_history_client
- idx_history_action (WHERE action='stage_change')
- idx_tasks_client (WHERE deleted_at IS NULL)
- idx_tasks_employee_due (WHERE status='pending')
- idx_onboarding_client (WHERE is_received=0)
- idx_outbox_pending_crm
- idx_outbox_aggregate_crm
- idx_drip_events_client_step

PRAGMA: journal_mode=WAL, busy_timeout=5000.

Также создай src/db.py (SQLAlchemy async engine, аналогично avito-bot).

Запусти:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/python scripts/init_db.py"

Проверка:
sqlite3 /opt/mn/crm-core/data/crm.db ".tables"  → ровно 8 таблиц
sqlite3 /opt/mn/crm-core/data/crm.db ".schema clients"  → UNIQUE(source, source_id)?
sqlite3 /opt/mn/crm-core/data/crm.db "PRAGMA journal_mode;"  → wal
sqlite3 /opt/mn/crm-core/data/crm.db ".schema outbox"  → aggregate_key, idempotency_key?

Коммит:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && git add -A && git commit -m 'init: crm.db — 8 таблиц + db.py engine'"
```

> Проверь .tables (ровно 8). `/clear`

---

## Промпт 8: Финальная валидация Дня 1 (5 мин)

```
Проверь итоги Дня 1. По каждому пункту выведи ✅ или ❌:

СТРУКТУРА:
- ls -la /opt/mn/ — директории: shared/, backups/, avito-bot/, crm-core/?
- ls /opt/mn/shared/config/*.json | wc -l  → 10?
- ls /opt/mn/shared/templates/ → договор + логотип?

ИЗОЛЯЦИЯ:
- sudo -u mn-avito ls /opt/mn/crm-core/ 2>&1 | grep -q "Permission denied" && echo "✅" || echo "❌"
- sudo -u mn-crm ls /opt/mn/avito-bot/ 2>&1 | grep -q "Permission denied" && echo "✅" || echo "❌"
- sudo -u mn-avito cat /opt/mn/shared/config/pricelist.json > /dev/null 2>&1 && echo "✅ shared читается" || echo "❌"

СЕРВИСЫ:
- sudo -u mn-avito bash -c "cd /opt/mn/avito-bot && .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8001 &"
- sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8003 &"
- sleep 3
- curl -s http://127.0.0.1:8001/health | python3.12 -c "import sys,json; d=json.load(sys.stdin); print('✅' if d.get('version') else '❌ нет version')"
- curl -s http://127.0.0.1:8003/health | python3.12 -c "import sys,json; d=json.load(sys.stdin); print('✅' if d.get('version') else '❌ нет version')"
- pkill -f uvicorn

БАЗЫ:
- sqlite3 /opt/mn/avito-bot/data/bot.db ".tables" | wc -w  → 5?
- sqlite3 /opt/mn/crm-core/data/crm.db ".tables" | wc -w  → 8?
- sqlite3 /opt/mn/avito-bot/data/bot.db "PRAGMA journal_mode;"  → wal?
- sqlite3 /opt/mn/crm-core/data/crm.db "PRAGMA journal_mode;"  → wal?

OUTBOX-СВЕРКА (схемы outbox должны быть идентичны):
- echo "--- bot.db outbox ---" && sqlite3 /opt/mn/avito-bot/data/bot.db ".schema outbox"
- echo "--- crm.db outbox ---" && sqlite3 /opt/mn/crm-core/data/crm.db ".schema outbox"
→ Поля aggregate_key, idempotency_key, status, attempts — совпадают?

БЕЗОПАСНОСТЬ:
- test -f /opt/mn/avito-bot/.gitignore && echo "✅ .gitignore" || echo "❌"
- test -f /opt/mn/crm-core/.gitignore && echo "✅ .gitignore" || echo "❌"
- sudo -u mn-avito bash -c "cd /opt/mn/avito-bot && git status --porcelain .env" → пусто (не отслеживается)?
- sudo -u mn-crm bash -c "cd /opt/mn/crm-core && git status --porcelain .env" → пусто?

GIT:
- sudo -u mn-avito bash -c "cd /opt/mn/avito-bot && git log --oneline"
- sudo -u mn-crm bash -c "cd /opt/mn/crm-core && git log --oneline"

ЛОГИ:
- test -d /opt/mn/avito-bot/logs/ && echo "✅ logs/" || echo "❌"
- test -d /opt/mn/crm-core/logs/ && echo "✅ logs/" || echo "❌"

Выведи итоговый отчёт.
```

---

## Что делать после промпта 8

1. **Заполни .env вручную** (оба сервиса). Реальные ключи — только руками, не через Claude Code.
2. Сгенерируй internal keys: `openssl rand -hex 32` — для CRM_INTERNAL_KEY и AVITO_INTERNAL_KEY.
3. Проверь что все ✅.
4. Если есть ❌ — дай Claude Code конкретный промпт на исправление.
5. Выключи тестовые процессы: `pkill -f uvicorn`
6. Завтра — День 2: CRM приём лидов.

---

## Решения по ФЗ-152 и шифрованию БД

> Аудитор поднял вопрос F1-8: SQLite-базы содержат ПДн без шифрования at rest.
> **Решение:** На текущем этапе (MVP, один сервер, root-доступ) шифрование через sqlcipher
> избыточно — оно замедлит разработку и добавит зависимость. Защита обеспечивается:
> chmod 700 на директории сервисов, изоляция Linux-пользователями, бэкапы в /opt/mn/backups/ (chmod 700 root).
> При масштабировании (Фаза 4, PostgreSQL) — пересмотреть.
