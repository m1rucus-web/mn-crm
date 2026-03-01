# Журнал работ

Новые записи — сверху.

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
