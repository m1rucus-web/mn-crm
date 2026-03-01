# Журнал работ

Новые записи — сверху.

---

## 2026-03-01 14:25 — ГОТОВО: Промпт 8 — Финальная валидация Дня 1 ✅
Что сделано:
- Проверена структура /opt/mn/ (shared/, backups/, avito-bot/, crm-core/)
- 10 JSON-конфигов на месте, templates (договор + логотип) на месте
- Изоляция: mn-avito не видит crm-core, mn-crm не видит avito-bot, shared читается
- Сервисы запущены, health ОК (оба version=0.1.0)
- bot.db: 7 таблиц, WAL; crm.db: 8 таблиц, WAL
- Outbox-схемы идентичны (aggregate_key, idempotency_key, status, attempts)
- .gitignore на месте, .env не в git
- logs/ директории на месте
- 17 коммитов в git

Результат: 16/16 ✅ — День 1 полностью завершён
Следующий: Заполнение .env (вручную), генерация internal keys, День 2

---

## 2026-03-01 — ГОТОВО: Промпт 6 — База данных Авито-бота ✅
Что сделано:
- scripts/init_db.py — создание всех таблиц и индексов (IF NOT EXISTS, бэкап если БД уже есть)
- src/db.py — SQLAlchemy async engine (aiosqlite), session factory, PRAGMA WAL+busy_timeout через event listener
- data/bot.db создана и проверена

Результат:
- 7 таблиц: leads, messages, employees, topic_mapping, settings, outbox, ai_logs
- 7 индексов: idx_outbox_pending, idx_outbox_aggregate, idx_messages_lead, idx_leads_status, idx_leads_created, idx_ai_logs_lead, idx_ai_logs_date
- PRAGMA journal_mode=WAL
- Схема полностью совпадает с FOUNDATION.md v4.9 раздел 6
- Повторный запуск идемпотентен (бэкап + IF NOT EXISTS)
Следующий: Промпт 7 — База данных CRM

---

## 2026-03-01 13:14 — ГОТОВО: Промпт 4 — venv + FastAPI-каркас ✅
Что сделано:
- Создан venv (Python 3.12.3)
- requirements.txt: fastapi, uvicorn, sqlalchemy, aiosqlite, httpx, loguru, apscheduler, pydantic-settings, python-dotenv
- Все зависимости установлены через pip
- .gitignore создан (avito-bot-level)
- .env.example + .env (копия шаблона)
- src/__init__.py, src/settings.py (pydantic-settings), src/main.py (FastAPI + loguru + health)
- Исправлены права на logs/ (были root → mn-avito)
- Health проверен: {"service":"avito-bot","status":"ok","version":"0.1.0"}
- Добавлена секция «Логирование» в CLAUDE.md обоих сервисов
Коммиты: 33a4b72, 65a4be5
Следующий: Промпт 5 — venv + FastAPI-каркас для CRM

---

## 2026-03-01 | Промпт 3 — Проверка JSON
- Проверил 10 JSON-конфигов
- Все валидны, company.json и employees.json содержат заглушки
- Коммит: 21954e3
