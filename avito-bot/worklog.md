# Журнал работ

Новые записи — сверху.

---

## 2026-03-01 — ГОТОВО: scripts/dump.sh ✅
Что сделано: создан /opt/mn/scripts/dump.sh (chmod +x) — дамп всего проекта в /tmp/project_*.txt (без .venv, .git, .env, бинарников, БД)
Следующий: День 2

---

## 2026-03-01 — ГОТОВО: STATE.md + правила в CLAUDE.md ✅
Что сделано:
- Создан /opt/mn/STATE.md — единая точка входа для агентов (статус, проблемы, следующий шаг)
- В avito-bot/CLAUDE.md добавлены 2 правила: чтение STATE.md перед кодом + обновление после промпта
- В crm-core/CLAUDE.md добавлены те же 2 правила
- Нумерация обязательных проверок исправлена (0-5)
Следующий: День 2

---

## 2026-03-01 — ГОТОВО: CI проверка 6 — динамический /health ✅
Результат: добавлена проверка 6 в ci_validate.sh — запуск обоих сервисов на портах 18001/18003, curl /health, проверка всех 8 полей по FOUNDATION §7 (service, status, version, uptime_seconds, db, outbox_pending, outbox_failed, errors_last_hour). trap cleanup_servers EXIT. CI PASS.
Следующий: День 2

---

## 2026-03-01 — ГОТОВО: АУДИТ-3 Шаг 3 — CI-правило в CLAUDE.md обоих сервисов ✅
Результат: добавлен пункт 0 в «Обязательные проверки»: запуск ci_validate.sh перед push
Следующий: ФИНАЛ — локальный CI + git push

---

## 2026-03-01 — ГОТОВО: АУДИТ-3 Шаг 2 — .github/workflows/ci.yml ✅
Результат: создан .github/workflows/ci.yml — триггеры push/PR в main, python 3.12, pip install обоих requirements.txt, bash scripts/ci_validate.sh
Следующий: Шаг 3 — обновить CLAUDE.md обоих сервисов

---

## 2026-03-01 — ГОТОВО: АУДИТ-3 Шаг 1 — scripts/ci_validate.sh ✅
Результат: создан /opt/mn/scripts/ci_validate.sh (chmod +x), 5 проверок:
1. Утечка .env — git ls-files
2. bot.db — 7 таблиц через init_db.py в /tmp/
3. crm.db — 8 таблиц через init_db.py в /tmp/
4. py_compile всех .py обоих сервисов
5. .env.example полнота — diff ключей с settings.py
Локальный прогон: CI PASS
Следующий: Шаг 2 — .github/workflows/ci.yml

---

## 2026-03-01 — ГОТОВО: АУДИТ-2 Шаг 13 — задачи эксплуатации в progress.md ✅
Результат: avito-bot: +2 задачи (healthcheck.sh, SLA-монитор). crm-core: +3 задачи (healthcheck.sh, aiogram, SLA-монитор)
Следующий: ФИНАЛ — git push

---

## 2026-03-01 — ГОТОВО: АУДИТ-2 Шаг 12 — убрать unused text import из db.py ✅
Результат: `from sqlalchemy import event, text` → `from sqlalchemy import event`
Следующий: Шаг 13 — задачи эксплуатации в progress.md

---

## 2026-03-01 — ГОТОВО: АУДИТ-2 Шаг 9 — удалить дубли из корня ✅
Результат: удалены 4 файла-дубля (avito-bot-CLAUDE.md, avito-bot-progress.md, crm-core-CLAUDE.md, crm-core-progress.md)
Следующий: Шаг 10 — crm-core .gitignore !.env.example

---

## 2026-03-01 — ГОТОВО: АУДИТ-2 Шаг 3 — APP_VERSION в avito-bot CLAUDE.md ✅
Результат: добавлена APP_VERSION=0.1.0 в секцию .env переменные
Следующий: Шаг 4 — APP_VERSION в crm-core CLAUDE.md

---

## 2026-03-01 — ГОТОВО: АУДИТ-2 Шаг 0 — employees.json обязательные поля ✅
Результат: добавлены id, telegram_user_id (заглушка 0), max_clients (50), status (active), substitute_id (null)
Следующий: Шаг 3 — APP_VERSION в avito-bot CLAUDE.md

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 10 — задачи в progress.md ✅
Результат: добавлены 3 задачи в 1.5 Эксплуатация (WAL checkpoint, processed_keys TTL, Claude Code hooks). Отмечен 1.2.2 db.py как выполненный.
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

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 7 — Logo.png → logo.png ✅
Результат: переименовано shared/templates/Logo.png → logo.png (FOUNDATION требует строчную)
Следующий: Шаг 8 — убрать api/health.py из CLAUDE.md

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 5 — проверка БД при старте avito-bot ✅
Результат: lifespan делает SELECT 1 при старте, RuntimeError если БД недоступна
Следующий: Шаг 6 — то же для crm-core

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 3 — DADATA ключи в avito-bot CLAUDE.md ✅
Результат: добавлены DADATA_API_KEY и DADATA_SECRET_KEY в секцию .env переменные
Следующий: Шаг 4 — то же для crm-core

---

## 2026-03-01 — ГОТОВО: АУДИТ-1 Шаг 1 — /health полный контракт (avito-bot) ✅
Результат: /health теперь возвращает все 8 полей по FOUNDATION §7: service, status, version, uptime_seconds, db, outbox_pending, outbox_failed, errors_last_hour
Следующий: Шаг 2 — то же для crm-core

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
