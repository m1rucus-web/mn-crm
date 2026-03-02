# АУДИТ-3: Ошибки и расхождения в проекте

Дата: 2026-03-01
Проверено: весь код, конфиги, FOUNDATION.md, оба CLAUDE.md, init_db.py, settings.py, main.py

---

## КРИТИЧЕСКИЕ (исправить до начала разработки Дня 2)

### K1. Секреты в git-репозитории (avito-bot-CLAUDE.md — исходник)
**Файл:** `/opt/mn/avito-bot-CLAUDE.md` (корневой исходник)
**Проблема:** Содержит строку `└── health.py` в секции Структура — АУДИТ-1 шаг 8 исправил inner `avito-bot/CLAUDE.md`, но НЕ исправил корневой исходник `avito-bot-CLAUDE.md`. Аналогично для `crm-core-CLAUDE.md`.
**Влияние:** При копировании исходника в сервис — вернётся устаревшая информация.
**Решение:** Синхронизировать `avito-bot-CLAUDE.md` → `avito-bot/CLAUDE.md` (или наоборот, привести в единый вид).

### K2. Корневые исходники разъехались с внутренними CLAUDE.md
**Файлы:**
- `/opt/mn/avito-bot-CLAUDE.md` — НЕТ секций: «Обязательные проверки», «Запрещено (нарушение = баг)», «Перед написанием кода», «Если что-то сломалось», «Handoff»
- `/opt/mn/crm-core-CLAUDE.md` — НЕТ секций: «Обязательные проверки», «Запрещено (нарушение = баг)», «Перед написанием кода», «Если что-то сломалось», «Handoff», DADATA ключи
- `/opt/mn/avito-bot-progress.md` — устаревший (все чекбоксы пустые, «Ожидание старта»)
- `/opt/mn/crm-core-progress.md` — устаревший (все чекбоксы пустые, «Ожидание старта»)
**Решение:** Либо удалить корневые дубли (они не нужны — актуальные живут внутри сервисов), либо синхронизировать.

### K3. employees.json — потеряны обязательные поля при ручной правке
**Файл:** `/opt/mn/shared/config/employees.json`
**Проблема:** При заполнении реальными данными удалены поля из FOUNDATION.md:
- `id` — нужен для `responsible_id` в clients
- `telegram_user_id` — **обязателен** (NOT NULL в crm.db employees, нужен для Telegram-алертов)
- `max_clients` — нужен для SLA-мониторинга (>20 → задача, >23 → drip на паузу)
- `status` / `substitute_id` — для отпусков и замещений
**Влияние:** Импорт в crm.db упадёт (telegram_user_id NOT NULL). SLA-мониторинг не будет работать.
**Решение:** Дополнить employees.json недостающими полями по образцу из FOUNDATION.md.

### K4. crm-core/.gitignore — отсутствует `!.env.example`
**Файл:** `/opt/mn/crm-core/.gitignore`
**Проблема:** Паттерн `*.db` без `.env.example` — но `.env.example` не исключён через `!`. Смотрим: avito-bot имеет `!.env.example`, crm-core — нет. Хотя `.env.*` ловит `.env.example`, поэтому нужен `!.env.example`.
**Решение:** Добавить `!.env.example` в crm-core/.gitignore (аналогично avito-bot).

---

## СРЕДНИЕ (исправить до конца Дня 2)

### С1. db.py — модуль-уровневый код выполняется при импорте
**Файлы:** `avito-bot/src/db.py`, `crm-core/src/db.py`
**Проблема:** `engine = create_async_engine(...)` выполняется при `import src.db`. Если `BOT_DB_PATH` / `CRM_DB_PATH` указывает на несуществующий путь — ошибка при любом `import`. Это мешает тестированию и скриптам.
**Решение:** Обернуть в функцию `get_engine()` с ленивой инициализацией, или оставить как есть (для MVP допустимо, aiosqlite создаёт файл автоматически).

### С2. `unused import` в crm-core/src/db.py
**Файл:** `crm-core/src/db.py`
**Проблема:** `from sqlalchemy import event` — нет `text` в импорте (в avito-bot есть `text`). В обоих db.py `text` не используется, но в avito-bot он импортирован. Не критично, но неаккуратно.
**Решение:** Убрать `text` из avito-bot/src/db.py (не используется в этом файле).

### С3. bot.db employees.telegram_user_id = NOT NULL, но employees.json не содержит это поле
**Файл:** `avito-bot/scripts/init_db.py`, строка `telegram_user_id INTEGER UNIQUE NOT NULL`
**Проблема:** Таблица `employees` в bot.db требует `telegram_user_id NOT NULL`. Но начальный импорт из employees.json не содержит этого поля (после правки K3 появится). Если импорт запустить с текущим JSON — упадёт.
**Связь:** Зависит от K3.

### С4. avito-bot .gitignore — `.env.*` ловит `.env.production`, `.env.local` и т.д.
**Файл:** `avito-bot/.gitignore`
**Проблема:** Паттерн `.env.*` + `!.env.example` корректно исключает `.env.example`. Но `crm-core/.gitignore` имеет `.env` без `.env.*` паттерна — а значит `.env.production` попадёт в git.
**Решение:** Унифицировать .gitignore обоих сервисов. Рекомендация:
```
.env
.env.*
!.env.example
```

### С5. healthcheck.sh — пустой файл
**Файл:** `/opt/mn/shared/healthcheck.sh`
**Проблема:** FOUNDATION §8 требует `healthcheck.sh` для cron */5, но файл существует без содержимого (или с минимальным). Это задача Дня 6, но стоит учесть при планировании.

### С6. crm.db employees — двойное поле is_active + status
**Файл:** `crm-core/scripts/init_db.py`
**Проблема:** Таблица employees имеет И `status TEXT DEFAULT 'active'` И `is_active INTEGER DEFAULT 1`. Это избыточно — можно запутаться какое поле проверять. FOUNDATION содержит оба, но при написании кода нужно решить: использовать `is_active` или `status`?
**Решение:** Задокументировать: `is_active` — для быстрых фильтров, `status` — для полного состояния (active/vacation/fired). Или убрать одно из полей.

---

## НИЗКИЕ (исправить когда-нибудь)

### Н1. Логи пишутся от root, но сервисы работают от mn-avito/mn-crm
**Проблема:** Если логи создались от root (первый запуск при отладке), mn-avito/mn-crm не смогут писать в них.
**Решение:** `chown -R mn-avito:mn-avito /opt/mn/avito-bot/logs/` после каждого запуска от root. Или проверять права в lifespan.

### Н2. `APP_VERSION` в .env.example, но не в CLAUDE.md секции .env
**Файлы:** `avito-bot/.env.example` (есть `APP_VERSION=0.1.0`), `avito-bot/CLAUDE.md` секция .env (нет `APP_VERSION`)
**Проблема:** Рассинхрон. `settings.py` читает `app_version` с дефолтом `"0.1.0"`, но в документации переменная не упомянута.
**Решение:** Добавить `APP_VERSION=0.1.0` в секцию .env обоих CLAUDE.md.

### Н3. crm-core settings.py — нет `app_version`... нет, есть. ОК.
*(перепроверено — crm-core/src/settings.py содержит `app_version: str = "0.1.0"`, корректно)*

### Н4. Дубликаты документации
**Проблема:** 4 файла дублируют содержимое:
- `avito-bot-CLAUDE.md` ≈ `avito-bot/CLAUDE.md` (но разъехались)
- `avito-bot-progress.md` ≈ `avito-bot/progress.md` (сильно устарел)
- `crm-core-CLAUDE.md` ≈ `crm-core/CLAUDE.md` (разъехались)
- `crm-core-progress.md` ≈ `crm-core/progress.md` (сильно устарел)
**Решение:** Удалить корневые дубли или заменить на симлинки.

### Н5. `.cache/` директории в сервисах
**Проблема:** `.cache/` в `.gitignore`, но может накапливаться на диске. Нет cron для очистки.
**Решение:** Добавить в backup.sh или отдельный cron.

---

## ИНФОРМАЦИОННЫЕ (не ошибки, а наблюдения)

### И1. Структура пока минимальна — это ОК
Пустые директории `api/`, `services/`, `workers/`, `tests/` — нормально для конца Дня 1. Код появится в Днях 2-7.

### И2. outbox_pending/failed в /health — работает
Проверено: SELECT SUM(CASE WHEN...) корректно возвращает 0 для пустой таблицы (через `or 0`).

### И3. FOUNDATION sla_monitor — "cron 10 мин" vs "cron 30 мин"
FOUNDATION §8 говорит "cron 30 мин", но CLAUDE.md crm-core говорит "cron 10 мин". Нужно уточнить с Юрием.

---

## Приоритеты исправления

1. **K3** — employees.json (без этого импорт упадёт)
2. **K2 + K1** — синхронизация или удаление корневых дублей
3. **K4** — .gitignore crm-core
4. **С4** — унификация .gitignore
5. **С6** — решение по is_active vs status
6. **Н2** — APP_VERSION в CLAUDE.md
7. **Н4** — удалить дубли
