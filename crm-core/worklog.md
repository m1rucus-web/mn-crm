# Журнал работ

Новые записи — сверху.

---

## 2026-03-01 — ГОТОВО: АУДИТ-2 Шаг 10 — crm-core .gitignore !.env.example ✅
Результат: добавлена строка !.env.example — теперь .env.example не игнорируется
Следующий: Шаг 12 — убрать unused text import из avito-bot db.py

---

## 2026-03-01 — ГОТОВО: АУДИТ-2 Шаг 4 — APP_VERSION в crm-core CLAUDE.md ✅
Результат: добавлена APP_VERSION=0.1.0 в секцию .env переменные
Следующий: Шаг 9 — удалить дубли из корня

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 10 — задачи в progress.md ✅
Результат: добавлены 3 задачи в 1.6 Эксплуатация (WAL checkpoint, processed_keys TTL, Claude Code hooks). Отмечены 1.2.1, 1.2.2, 1.3.7 как выполненные.
Следующий: ФИНАЛ — git push

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 9 — создать .claude/handoff.md ✅
Результат: создан .claude/handoff.md, добавлено правило в CLAUDE.md
Следующий: Шаг 10 — добавить задачи в progress.md

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 8 — убрать api/health.py из CLAUDE.md ✅
Результат: удалена строка health.py из секции Структура (health живёт в main.py)
Следующий: Шаг 9 — создать .claude/handoff.md

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 6 — проверка БД при старте crm-core ✅
Результат: lifespan делает SELECT 1 при старте, RuntimeError если crm.db недоступна
Следующий: Шаг 7 — переименовать Logo.png → logo.png

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 4 — DADATA ключи в crm-core CLAUDE.md ✅
Результат: добавлены DADATA_API_KEY и DADATA_SECRET_KEY в секцию .env переменные
Следующий: Шаг 5 — проверка БД при старте avito-bot

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 2 — /health полный контракт (crm-core) ✅
Результат: /health теперь возвращает все 8 полей по FOUNDATION §7
Следующий: Шаг 3 — DADATA ключи в avito-bot CLAUDE.md

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

## 2026-03-01 — ГОТОВО: Промпт 7 — База данных CRM ✅
Что сделано:
- scripts/init_db.py — 8 таблиц (clients, employees, history, tasks, onboarding_documents, processed_keys, outbox, drip_events)
- 12 индексов (включая UNIQUE idx_clients_inn_unique)
- PRAGMA journal_mode=WAL, busy_timeout=5000
- src/db.py — SQLAlchemy async engine + session factory (аналог avito-bot)
- UNIQUE(source, source_id) на clients — для UPSERT двухэтапной передачи лидов
Следующий: Промпт 8 — Финальная валидация Дня 1

---

## 2026-03-01 13:36 — ГОТОВО: Промпт 5 — venv + FastAPI-каркас CRM ✅
Что сделано:
- Создан venv (Python 3.12.3)
- requirements.txt: fastapi, uvicorn, sqlalchemy, aiosqlite, httpx, loguru, apscheduler, pydantic-settings, python-dotenv, jinja2, docxtpl, python-multipart
- Все зависимости установлены через pip
- .gitignore создан (crm-core-level)
- .env.example + .env (копия шаблона)
- src/__init__.py, src/settings.py (pydantic-settings), src/main.py (FastAPI + loguru + health)
- Health проверен: {"service":"crm-core","status":"ok","version":"0.1.0"}
Следующий: Промпт 6 — База данных Авито-бота

---

## 2026-03-01 | Промпт 3 — Проверка JSON
- Проверил 10 JSON-конфигов
- Все валидны, company.json и employees.json содержат заглушки
- Коммит: 21954e3
