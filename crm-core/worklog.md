# Журнал работ

Новые записи — сверху.

---

## 2026-03-02 — АУДИТ ENDPOINT ПРОЙДЕН ✅
Результат аудита (Фаза 2): все 10 проверок пройдены, ручные тесты прошли.
- X-Internal-Key → 403: ✅
- Идемпотентность (check ДО работы с клиентом): ✅
- Дедупликация (find_duplicate ДО INSERT, 200 "merged"): ✅
- UPSERT (SELECT + INSERT/UPDATE по source+source_id): ✅
- Маппинг (client_name→name, last_message_at→source_last_message_at): ✅
- History (lead_created/lead_updated, auto=1): ✅
- responsible_id = NULL: ✅
- save_idempotency ПОСЛЕ flush: ✅
- Логирование trace_id: ✅
- Pydantic-схема (24 поля): ✅
- py_compile: OK
- Ручные тесты: создание 201, идемпотентность OK, без ключа 403
Действие (Фаза 3): исправлений не требуется. audit_current.md удалён. progress.md обновлён.
Следующий: Промпт 4 — Тесты POST /leads

---

## 2026-03-02 — НАЧИНАЮ: Промпт 3 Фаза 1 — POST /api/v1/leads endpoint
Что делаю: создаю src/api/leads.py (POST /api/v1/leads) с авторизацией, идемпотентностью, дедупликацией, UPSERT
Изменения: src/api/__init__.py (новый), src/api/leads.py (новый), src/main.py (подключение router)
Зависимости: models.py, idempotency.py, lead_merger.py, settings.py, db.py
Риски: неверный маппинг полей, неправильный порядок проверок

## 2026-03-02 — ГОТОВО: Промпт 3 Фаза 1 — POST /api/v1/leads endpoint ✅
Результат:
- LeadRequest Pydantic-схема (22 поля)
- POST /leads: X-Internal-Key → 403, idempotency check, find_duplicate (phone/inn), UPSERT (source+source_id)
- Маппинг: client_name→name, last_message_at→source_last_message_at
- responsible_id не назначается (NULL)
- History: lead_created (INSERT), lead_updated (UPSERT UPDATE), lead_merged (через lead_merger)
- Логирование: trace_id, source_id, результат
- Router подключён в main.py
- Проверка: сервер стартует, /api/v1/leads в OpenAPI
Коммит: feat: POST /api/v1/leads — endpoint с авторизацией, idempotency, merge, history

---

## 2026-03-02 — АУДИТ СЕРВИСОВ ПРОЙДЕН ✅
Результат аудита (Фаза 2): все 13 проверок пройдены.
- idempotency.py: check/save корректны, json.loads/json.dumps, ProcessedKey модель
- lead_merger.py: find_duplicate (phone ИЛИ inn, deleted_at IS NULL), merge_lead (не перезаписывает заполненные, history auto=1, updated_at)
- py_compile обоих файлов: OK
- Соответствие FOUNDATION §7: полное
Действие (Фаза 3): исправлений не требуется. audit_current.md удалён. progress.md обновлён.

---

## 2026-03-02 — НАЧИНАЮ: Промпт 2 Фаза 1 — Сервисы (idempotency + lead_merger)
Что делаю: создаю src/services/idempotency.py и src/services/lead_merger.py
Изменения: src/services/__init__.py, src/services/idempotency.py, src/services/lead_merger.py (новые файлы)
Зависимости: models.py (Client, ProcessedKey, History)
Риски: неверная логика merge (перезапись заполненных полей)

## 2026-03-02 — ГОТОВО: Промпт 2 Фаза 1 — Сервисы (idempotency + lead_merger) ✅
Результат:
- idempotency.py: check_idempotency (SELECT → json.loads), save_idempotency (json.dumps → INSERT)
- lead_merger.py: find_duplicate (phone ИЛИ inn, WHERE deleted_at IS NULL), merge_lead (обновляет только пустые поля, history action='lead_merged' auto=1)
- Проверка: `from src.services.idempotency import ...; from src.services.lead_merger import ... → Сервисы OK`
Коммит: feat: idempotency + lead_merger сервисы

---

## 2026-03-02 — АУДИТ ORM ПРОЙДЕН ✅
Результат аудита (Фаза 2): все 8 моделей, 96 полей — полностью совпадают с init_db.py и FOUNDATION.md §6.
Расхождений нет. Единственное примечание: max_clients=20 в models.py (решение 2 марта) vs 50 в init_db.py — осознанное решение, не расхождение.
Действие (Фаза 3): исправлений не требуется. audit_current.md удалён. progress.md обновлён.

---

## 2026-03-02 — НАЧИНАЮ: Промпт 1 Фаза 1 — ORM-модели
Что делаю: создаю src/models.py — 8 ORM-моделей строго по FOUNDATION §6 + init_db.py
Изменения: src/models.py (новый файл)
Зависимости: db.py, init_db.py, FOUNDATION.md
Риски: расхождение типов/DEFAULT между init_db.py и models.py

## 2026-03-02 — ГОТОВО: Промпт 1 Фаза 1 — ORM-модели ✅
Результат: 8 моделей (Client, Employee, History, Task, OnboardingDocument, ProcessedKey, OutboxMessage, DripEvent).
Все поля строго по init_db.py. max_clients=20 (решение 2 марта). JSON-поля → Text. UNIQUE(source, source_id) через __table_args__. ProcessedKey.idempotency_key = primary_key.
Проверка: `from src.models import ... → 8 моделей OK`

---

## 2026-03-02 — Трёхфазный цикл добавлен в CLAUDE.md
Что сделал: добавил секцию «Трёхфазный цикл (на каждый промпт)» после «Обязательные проверки после каждого промпта»
Файлы: CLAUDE.md
Результат: Фаза 1 (ДЕЛАЙ), Фаза 2 (ПРОВЕРЯЙ), Фаза 3 (ИСПРАВЛЯЙ) — протокол зафиксирован

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
Результат: добавлена проверка 6 в ci_validate.sh — запуск обоих сервисов на портах 18001/18003, curl /health, проверка всех 8 полей по FOUNDATION §7. CI PASS.
Следующий: День 2

---

## 2026-03-01 — ГОТОВО: АУДИТ-3 Шаг 3 — CI-правило в CLAUDE.md ✅
Результат: добавлен пункт 0 в «Обязательные проверки»: запуск ci_validate.sh перед push
Следующий: ФИНАЛ — локальный CI + git push

---

## 2026-03-01 — ГОТОВО: АУДИТ-2 Шаг 13 — задачи эксплуатации в progress.md ✅
Результат: добавлены задачи: healthcheck.sh, aiogram, SLA-монитор cron
Следующий: ФИНАЛ — git push

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
