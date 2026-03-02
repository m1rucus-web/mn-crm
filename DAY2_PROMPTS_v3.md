# День 2 — Промпты для Claude Code (v3 — финал)
# Дата: 2026-03-02
# Порядок: CRM сначала (приёмник → передатчик)
# Правила: код через sudo -u mn-crm, git от root (в /opt/mn/)
# Каждый промпт (кроме 0) — трёхфазный цикл: ДЕЛАЙ → /clear → ПРОВЕРЯЙ → /clear → ИСПРАВЛЯЙ
# Копируй по одному. После каждого блока — /clear.
# Не забывай /clear между промптами — это критично для чистоты контекста.

---

## Промпт -1: Трёхфазный цикл в crm-core CLAUDE.md (2 мин)

> Проверь: если в crm-core/CLAUDE.md уже есть секция «Трёхфазный цикл» — пропусти этот промпт.

```
Прочитай /opt/mn/crm-core/CLAUDE.md.

Если секции «Трёхфазный цикл» НЕТ — добавь её ПОСЛЕ секции «Обязательные проверки после каждого промпта»:

## Трёхфазный цикл (на каждый промпт)

### Фаза 1 — ДЕЛАЙ
- Выполни промпт строго по FOUNDATION.md
- Запиши в worklog.md: что сделал, какие файлы создал/изменил
- git add + commit
- В конце напиши: "ФАЗА 1 ЗАВЕРШЕНА. Сделай /clear и запусти Фазу 2."

### Фаза 2 — ПРОВЕРЯЙ (после /clear)
- Прочитай worklog.md → найди последнюю запись Фазы 1
- Прочитай FOUNDATION.md → найди соответствующий раздел
- Открой каждый файл из Фазы 1 и сверь с FOUNDATION построчно
- Запиши результат в audit_current.md:
  - ✅ что совпадает
  - ❌ что расходится (файл, строка, ожидание vs реальность)
- git add + commit
- В конце напиши: "ФАЗА 2 ЗАВЕРШЕНА. Сделай /clear и запусти Фазу 3."

### Фаза 3 — ИСПРАВЛЯЙ (после /clear)
- Прочитай audit_current.md
- Если всё ✅ → напиши "АУДИТ ПРОЙДЕН" в worklog.md, обнови progress.md, git push
- Если есть ❌ → исправь каждый пункт, запиши в worklog.md что исправил
- git add + commit + push
- В конце напиши: "ЦИКЛ ЗАВЕРШЁН. Переходи к следующему шагу."

Также проверь что avito-bot/CLAUDE.md уже содержит эту секцию. Если нет — добавь и туда.

cd /opt/mn && git add -A && git commit -m 'docs: трёхфазный цикл в CLAUDE.md обоих сервисов' && git push
```

> `/clear`

---

## Промпт 0: Патч — фиксы + решения (3 мин)

> Однофазный — мелкие правки, ревью не нужно.

```
Прочитай STATE.md, потом выполни патч.

ШАГ 1 — employees.json: max_clients 50 → 20:
В /opt/mn/shared/config/employees.json замени "max_clients": 50 на "max_clients": 20 у ВСЕХ сотрудников (5 записей).
Проверка: grep -c '"max_clients": 20' /opt/mn/shared/config/employees.json → 5

ШАГ 2 — neuro-codex.html: убрать из git (если есть):
cd /opt/mn
git ls-files neuro-codex.html | grep -q . && git rm neuro-codex.html && echo "Удалён из git" || echo "Не в git, пропускаем"

ШАГ 3 — STATE.md: замени ВЕСЬ файл на:

# STATE.md — текущее состояние проекта
Обновляется в конце каждой рабочей сессии.
Любой агент читает этот файл ПЕРВЫМ перед началом работы.

## Последнее обновление
2026-03-02

## Где мы
День 1 завершён. Аудит-патч применён. Начинаем День 2.

## Что дальше
День 2 — CRM: POST /api/v1/leads (идемпотентность, дедупликация, merge).
Потом День 3 — CRM CRUD + HTMX-дашборд + воронка.
Потом День 4 — Авито-бот webhooks.

## Открытые проблемы
- telegram_user_id = 0 у всех сотрудников (нужны реальные ID, не блокер пока)
- ci.yml в .gitignore (OAuth без workflow scope)
- ПДн-оферта: текст не написан (День 5)
- Договор и логотип: заглушки в shared/templates/

## Решения 2 марта
- max_clients = 20 (не 50)
- Назначение бухгалтера — вручную Юрием
- Крупная рыба → responsible_id = 1 (Юрий)
- Drip стартует после handoff + молчание 3 дня (НЕ после первого сообщения)
- SLA-монитор = 30 мин (везде, унифицировано)
- aiogram = Фаза 2 (Telegram-алерты пока через httpx напрямую в Bot API)
- neuro-codex.html убран из git

## Завершённые этапы
- День 1: каркас, venv, БД (7+8 таблиц), /health (8 полей), settings, logging
- АУДИТ-1: employees.json, /health расширен, CLAUDE.md синхронизированы, дубли удалены, CI правила
- АУДИТ-2: ci_validate.sh (6 проверок), GitHub Actions workflow

## Стек
Python 3.12, FastAPI, SQLite WAL, SQLAlchemy async, HTMX, Nginx

## Ключевые файлы
- FOUNDATION.md — архитектура (источник истины)
- */CLAUDE.md — правила для Claude Code
- */progress.md — чеклисты задач
- */worklog.md — журнал действий
- scripts/ci_validate.sh — автопроверка

ШАГ 4 — git config (проверка):
cd /opt/mn
git config user.name || git config user.name "MN Project"
git config user.email || git config user.email "mn@nikiforov-bots.ru"

ШАГ 5 — Коммит (от root, в /opt/mn/):
cd /opt/mn && git add -A && git commit -m 'patch: max_clients=20, STATE.md обновлён, решения 2 марта' && git push
```

> Проверь: max_clients=20 у всех (5 штук)? STATE.md обновлён? git push прошёл? `/clear`

---

## Промпт 1 — Фаза 1: ORM-модели — ДЕЛАЙ (10 мин)

```
Все команды работы с кодом — через sudo -u mn-crm bash -c "...".
Все git-команды — от root в /opt/mn/.
Python — /opt/mn/crm-core/.venv/bin/python.

ПРЕДУСЛОВИЕ:
test -f /opt/mn/FOUNDATION.md || echo "СТОП: FOUNDATION.md не найден!"
test -f /opt/mn/crm-core/src/db.py || echo "СТОП: db.py не найден!"

Создай /opt/mn/crm-core/src/models.py — SQLAlchemy ORM-модели для ВСЕХ 8 таблиц из crm.db.
Читай схему СТРОГО из FOUNDATION.md раздел 6 (crm.db). Не выдумывай полей.

Таблицы (8 штук):
1. Client — clients (с UNIQUE(source, source_id), drip-поля, deleted_at, consent_given_at)
2. Employee — employees (с max_clients=20, status, substitute_id)
3. History — history (action, details JSON, auto flag)
4. Task — tasks (с deleted_at)
5. OnboardingDocument — onboarding_documents
6. ProcessedKey — processed_keys (idempotency_key PRIMARY KEY)
7. OutboxMessage — outbox (aggregate_key, idempotency_key UNIQUE)
8. DripEvent — drip_events

Используй:
- from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
- from sqlalchemy import String, Integer, Text, Float, ForeignKey
- Типы колонок — строго по init_db.py (TEXT → String, INTEGER → Integer и т.д.)
- Все DEFAULT значения — как в init_db.py
- Для JSON-полей (details в history, payload в outbox) — используй Text (SQLite не поддерживает JSON тип)

НЕ создавай миграции. НЕ меняй init_db.py. models.py — это ORM-зеркало существующей схемы.

Проверка (от mn-crm):
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/python -c 'from src.models import Client, Employee, History, Task, OnboardingDocument, ProcessedKey, OutboxMessage, DripEvent; print(\"8 моделей OK\")'"

Коммит (от root):
cd /opt/mn && git add -A && git commit -m 'feat: ORM-модели crm-core — 8 таблиц из FOUNDATION §6'

ФАЗА 1 ЗАВЕРШЕНА. Сделай /clear и запусти Фазу 2.
```

> `/clear`, потом ↓

---

## Промпт 1 — Фаза 2: ORM-модели — ПРОВЕРЯЙ

```
Прочитай crm-core/worklog.md — найди последнюю запись.
Прочитай FOUNDATION.md раздел 6 (crm.db) — все CREATE TABLE.
Открой /opt/mn/crm-core/src/models.py.

Сверь КАЖДОЕ поле КАЖДОЙ таблицы:

1. clients — столько же полей, сколько в CREATE TABLE clients? Типы? DEFAULT?
   Особенно: UNIQUE(source, source_id), drip_active DEFAULT 0, deleted_at, consent_given_at.
2. employees — max_clients DEFAULT 20 (НЕ 50!)? status DEFAULT 'active'? substitute_id REFERENCES?
3. history — auto INTEGER DEFAULT 0?
4. tasks — deleted_at есть?
5. onboarding_documents — все поля?
6. processed_keys — idempotency_key это PRIMARY KEY (не просто UNIQUE)?
7. outbox — aggregate_key, idempotency_key UNIQUE, все поля?
8. drip_events — event_type, meta?

Также проверь init_db.py vs models.py: количество полей в каждой таблице совпадает?

Запиши результат в /opt/mn/crm-core/audit_current.md:
- ✅ что совпадает
- ❌ что расходится (модель, поле, ожидание vs реальность)

cd /opt/mn && git add -A && git commit -m 'audit: ревью ORM-моделей'

ФАЗА 2 ЗАВЕРШЕНА. Сделай /clear и запусти Фазу 3.
```

> `/clear`, потом ↓

---

## Промпт 1 — Фаза 3: ORM-модели — ИСПРАВЛЯЙ

```
Прочитай /opt/mn/crm-core/audit_current.md.

Если всё ✅ → напиши "АУДИТ ORM ПРОЙДЕН" в crm-core/worklog.md, обнови crm-core/progress.md, удали audit_current.md.
Если есть ❌ → исправь каждый пункт в models.py, запиши в worklog что исправил.

cd /opt/mn && git add -A && git commit -m 'fix: ORM-модели по результатам аудита' && git push

ЦИКЛ ЗАВЕРШЁН. Переходи к следующему шагу.
```

> `/clear`

---

## Промпт 2 — Фаза 1: Сервисы (idempotency + lead_merger) — ДЕЛАЙ (10 мин)

```
Код — через sudo -u mn-crm bash -c "...". Git — от root в /opt/mn/.

ПРЕДУСЛОВИЕ:
test -f /opt/mn/crm-core/src/models.py || echo "СТОП: models.py не найден!"

Прочитай FOUNDATION.md раздел 7 + crm-core/CLAUDE.md секцию «Приём лидов».

ШАГ 1 — /opt/mn/crm-core/src/services/__init__.py (пустой)

ШАГ 2 — /opt/mn/crm-core/src/services/idempotency.py:
- async def check_idempotency(session: AsyncSession, key: str) → dict | None
  Ищет key в processed_keys. Если найден → json.loads(response). Не найден → None.
- async def save_idempotency(session: AsyncSession, key: str, response: dict) → None
  Сохраняет key + json.dumps(response) в processed_keys.

ШАГ 3 — /opt/mn/crm-core/src/services/lead_merger.py:
- async def find_duplicate(session: AsyncSession, phone: str | None, inn: str | None) → Client | None
  Ищет существующего клиента (WHERE deleted_at IS NULL):
  - Если phone не пустой → ищет по phone
  - Если inn не пустой → ищет по inn
  - Возвращает первого найденного или None
- async def merge_lead(session: AsyncSession, existing: Client, new_data: dict) → Client
  Обновляет поля existing из new_data (только те, где new_data[field] не None И existing.field пустой/None).
  НЕ перезаписывает заполненные поля пустыми.
  Записывает в history: action='lead_merged', details=JSON {"updated_fields": [...], "source_id": "..."}, auto=1.
  Обновляет existing.updated_at.
  Возвращает обновлённого клиента.

Проверка:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/python -c 'from src.services.idempotency import check_idempotency, save_idempotency; from src.services.lead_merger import find_duplicate, merge_lead; print(\"Сервисы OK\")'"

cd /opt/mn && git add -A && git commit -m 'feat: idempotency + lead_merger сервисы'

ФАЗА 1 ЗАВЕРШЕНА. Сделай /clear и запусти Фазу 2.
```

> `/clear`, потом ↓

---

## Промпт 2 — Фаза 2: Сервисы — ПРОВЕРЯЙ

```
Прочитай crm-core/worklog.md — последняя запись.
Прочитай FOUNDATION.md раздел 7 — секции про дедупликацию и идемпотентность.
Открой idempotency.py и lead_merger.py.

Проверь:
1. idempotency.py: check → ищет в processed_keys? save → json.dumps при записи?
2. lead_merger.py: find_duplicate → фильтрует deleted_at IS NULL? Ищет по phone ИЛИ inn (не AND)?
3. lead_merger.py: merge_lead → НЕ перезаписывает заполненные поля пустыми? Пишет в history с auto=1?
4. Импорты: используют модели из src.models? AsyncSession из sqlalchemy.ext.asyncio?
5. py_compile:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/python -m py_compile src/services/idempotency.py && echo OK"
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/python -m py_compile src/services/lead_merger.py && echo OK"

Запиши в /opt/mn/crm-core/audit_current.md. Коммит.

ФАЗА 2 ЗАВЕРШЕНА. Сделай /clear и запусти Фазу 3.
```

> `/clear`, потом ↓

---

## Промпт 2 — Фаза 3: Сервисы — ИСПРАВЛЯЙ

```
Прочитай /opt/mn/crm-core/audit_current.md.

Если всё ✅ → "АУДИТ СЕРВИСОВ ПРОЙДЕН" в worklog.md, обнови progress.md, удали audit_current.md, коммит + push.
Если есть ❌ → исправь, запиши в worklog, коммит + push.

ЦИКЛ ЗАВЕРШЁН.
```

> `/clear`

---

## Промпт 3 — Фаза 1: POST /api/v1/leads endpoint — ДЕЛАЙ (15 мин)

```
Код — через sudo -u mn-crm bash -c "...". Git — от root в /opt/mn/.

ПРЕДУСЛОВИЕ:
test -f /opt/mn/crm-core/src/services/idempotency.py || echo "СТОП!"
test -f /opt/mn/crm-core/src/services/lead_merger.py || echo "СТОП!"
test -f /opt/mn/crm-core/src/models.py || echo "СТОП!"

Прочитай FOUNDATION.md раздел 7 (API-контракты) — ВЕСЬ раздел «Авито-бот → CRM».

ШАГ 1 — /opt/mn/crm-core/src/api/__init__.py (пустой, если нет)

ШАГ 2 — /opt/mn/crm-core/src/api/leads.py:
- router = APIRouter(prefix="/api/v1", tags=["leads"])

Pydantic-схема запроса LeadRequest:
- idempotency_key: str
- trace_id: str | None = None
- source: str = "avito"
- source_id: str
- client_name: str | None = None  ← маппинг в DB: Client.name
- phone: str | None = None
- telegram: str | None = None
- email: str | None = None
- inn: str | None = None
- company_name: str | None = None
- client_type: str | None = None
- tax_system: str | None = None
- has_employees: bool = False
- employees_count: int = 0
- need: str | None = None
- marketplace: str | None = None
- city: str | None = None
- source_url: str | None = None
- qualification_summary: str | None = None
- estimated_price: str | None = None
- messages_count: int | None = None
- first_message_at: str | None = None
- last_message_at: str | None = None  ← маппинг в DB: Client.source_last_message_at
- consent_given_at: str | None = None

POST /leads логика (строго по FOUNDATION §7):
1. Проверить X-Internal-Key (Header) == settings.avito_internal_key. Если нет или не совпадает — верни ошибку. Прочитай FOUNDATION §7 чтобы определить правильный HTTP-код ответа (401 или 403 — сделай как в FOUNDATION).
2. check_idempotency(idempotency_key) → если дубль → вернуть предыдущий результат
3. find_duplicate(phone, inn) → если найден → merge_lead → save_idempotency → 200 {"status": "merged", "client_id": N}
4. Попытка INSERT. ON CONFLICT(source, source_id):
   - Нет конфликта → INSERT → history action='lead_created' auto=1 → save_idempotency → 201 {"status": "created", "client_id": N}
   - Конфликт → UPDATE → history action='lead_updated' auto=1 details=JSON → save_idempotency → 200 {"status": "updated", "client_id": N}
5. Маппинг: request.client_name → Client.name. request.last_message_at → Client.source_last_message_at.
6. responsible_id НЕ назначать (оставить NULL).
7. Логировать через loguru: trace_id, source_id, результат.

ШАГ 3 — Подключить router в main.py:
from src.api.leads import router as leads_router
app.include_router(leads_router)

ШАГ 4 — Проверка запуска:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8003 &"
sleep 2
curl -s http://127.0.0.1:8003/health
curl -s http://127.0.0.1:8003/docs | grep -q "leads" && echo "✅ /leads в docs" || echo "❌"
pkill -f "uvicorn src.main:app.*8003"

cd /opt/mn && git add -A && git commit -m 'feat: POST /api/v1/leads — endpoint с авторизацией, idempotency, merge, history'

ФАЗА 1 ЗАВЕРШЕНА. Сделай /clear и запусти Фазу 2.
```

> `/clear`, потом ↓

---

## Промпт 3 — Фаза 2: POST /leads — ПРОВЕРЯЙ

```
Прочитай crm-core/worklog.md — последняя запись.
Прочитай FOUNDATION.md раздел 7 — ВЕСЬ раздел API-контрактов.
Открой /opt/mn/crm-core/src/api/leads.py.

Сверь ПОСТРОЧНО:
1. X-Internal-Key → сравнивается с settings.avito_internal_key? HTTP-код при ошибке соответствует FOUNDATION?
2. Идемпотентность → check_idempotency вызывается ДО любой работы с клиентом?
3. Дедупликация → find_duplicate вызывается ДО INSERT? Возвращает 200 "merged" (не 201)?
4. UPSERT → ON CONFLICT(source, source_id)? Или через код (SELECT → INSERT/UPDATE)?
5. Маппинг → client_name → name? last_message_at → source_last_message_at?
6. History → при создании action='lead_created' auto=1? При обновлении action='lead_updated'?
7. responsible_id → остаётся NULL (НЕ авто-назначается)?
8. save_idempotency → вызывается ПОСЛЕ успешной операции?
9. Логирование → trace_id логируется?
10. Pydantic-схема → все поля из FOUNDATION §7?

Запусти сервер и проверь руками:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8003 &"
sleep 2

INTERNAL_KEY=$(grep AVITO_INTERNAL_KEY /opt/mn/crm-core/.env | cut -d= -f2)

# Создание
curl -s -X POST http://127.0.0.1:8003/api/v1/leads \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: $INTERNAL_KEY" \
  -d '{"idempotency_key":"audit-test-001","source":"avito","source_id":"chat_audit_1","client_name":"Аудит Тестов"}'

# Идемпотентность
curl -s -X POST http://127.0.0.1:8003/api/v1/leads \
  -H "Content-Type: application/json" \
  -H "X-Internal-Key: $INTERNAL_KEY" \
  -d '{"idempotency_key":"audit-test-001","source":"avito","source_id":"chat_audit_1","client_name":"Аудит Тестов"}'

# Без ключа
curl -s -o /dev/null -w "HTTP %{http_code}" -X POST http://127.0.0.1:8003/api/v1/leads \
  -H "Content-Type: application/json" \
  -d '{"idempotency_key":"no-key","source":"avito","source_id":"x"}'

pkill -f "uvicorn src.main:app.*8003"

# Очистка
sqlite3 /opt/mn/crm-core/data/crm.db "DELETE FROM history WHERE client_id IN (SELECT id FROM clients WHERE name='Аудит Тестов'); DELETE FROM processed_keys WHERE idempotency_key='audit-test-001'; DELETE FROM clients WHERE name='Аудит Тестов';"

Запиши в /opt/mn/crm-core/audit_current.md.
cd /opt/mn && git add -A && git commit -m 'audit: ревью POST /api/v1/leads'

ФАЗА 2 ЗАВЕРШЕНА. Сделай /clear и запусти Фазу 3.
```

> `/clear`, потом ↓

---

## Промпт 3 — Фаза 3: POST /leads — ИСПРАВЛЯЙ

```
Прочитай /opt/mn/crm-core/audit_current.md.

Если всё ✅ → "АУДИТ ENDPOINT ПРОЙДЕН" в worklog.md, обнови progress.md, удали audit_current.md, коммит + push.
Если есть ❌ → исправь, запиши в worklog, коммит + push.

ЦИКЛ ЗАВЕРШЁН.
```

> `/clear`

---

## Промпт 4: Тесты POST /leads (10 мин)

> Однофазный — тесты = проверка.

```
Код — через sudo -u mn-crm bash -c "...". Git — от root в /opt/mn/.

ПРЕДУСЛОВИЕ:
test -f /opt/mn/crm-core/src/api/leads.py || echo "СТОП: leads.py не найден!"

Установи pytest (если ещё нет):
sudo -u mn-crm bash -c "/opt/mn/crm-core/.venv/bin/pip install pytest pytest-asyncio"

Создай /opt/mn/crm-core/tests/__init__.py (пустой, если нет)
Создай /opt/mn/crm-core/tests/test_leads.py:

Используй httpx.AsyncClient + FastAPI app. Каждый тест — чистая БД (fixture: init_db.py в /tmp/).

10 тестов:

1. test_create_lead_success:
   POST с валидным payload + X-Internal-Key → 201, client_id в ответе

2. test_create_lead_wrong_key:
   POST с неверным X-Internal-Key → ожидаемый код ошибки (прочитай из leads.py какой код используется)

3. test_create_lead_missing_key:
   POST без заголовка → тот же код ошибки

4. test_idempotency_duplicate:
   POST одинаковый idempotency_key дважды → оба возвращают тот же client_id, в БД 1 клиент

5. test_merge_by_phone:
   POST лид с phone="79001234567" → 201.
   POST другой (другой source_id, другой idempotency_key) с тем же phone → 200 "merged".
   В БД 1 клиент.

6. test_merge_by_inn:
   POST лид с inn="1234567890" → 201.
   POST другой с тем же inn → 200 "merged".

7. test_client_name_mapping:
   POST с client_name="Иван" → в БД clients.name = "Иван"

8. test_history_created_on_new_lead:
   POST новый лид → в history запись action='lead_created', auto=1

9. test_upsert_same_source:
   POST source="avito", source_id="chat_123" → 201.
   POST source="avito", source_id="chat_123" (ДРУГОЙ idempotency_key, phone добавлен) → 200 "updated".
   В БД 1 клиент, phone обновился.

10. test_bad_payload:
    POST с пустым body → 422

Запуск:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/python -m pytest tests/test_leads.py -v --tb=short"

Если тесты падают — ИСПРАВЬ КОД до зелёного. Не xfail. Не skip.

cd /opt/mn && git add -A && git commit -m 'test: 10 тестов POST /api/v1/leads — все зелёные'
```

> Все 10 зелёные? `/clear`

---

## Промпт 5: Финальная валидация Дня 2 + push (5 мин)

```
Проверь итоги Дня 2. По каждому пункту — ✅ или ❌:

МОДЕЛИ:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/python -c 'from src.models import Client, Employee, History, Task, OnboardingDocument, ProcessedKey, OutboxMessage, DripEvent; print(\"8 моделей OK\")'"

API:
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8003 &"
sleep 2

INTERNAL_KEY=$(grep AVITO_INTERNAL_KEY /opt/mn/crm-core/.env | cut -d= -f2)

# health
curl -s http://127.0.0.1:8003/health | python3.12 -c "import sys,json; d=json.load(sys.stdin); print('✅ health' if d.get('status')=='ok' else '❌')"

# создание
curl -s -X POST http://127.0.0.1:8003/api/v1/leads \
  -H "Content-Type: application/json" -H "X-Internal-Key: $INTERNAL_KEY" \
  -d '{"idempotency_key":"final-001","source":"avito","source_id":"chat_final_1","client_name":"Финал","phone":"79009999999"}' \
  | python3.12 -c "import sys,json; d=json.load(sys.stdin); print('✅ создание' if d.get('client_id') else '❌', d)"

# идемпотентность
curl -s -X POST http://127.0.0.1:8003/api/v1/leads \
  -H "Content-Type: application/json" -H "X-Internal-Key: $INTERNAL_KEY" \
  -d '{"idempotency_key":"final-001","source":"avito","source_id":"chat_final_1","client_name":"Финал"}' \
  | python3.12 -c "import sys,json; d=json.load(sys.stdin); print('✅ идемпотентность' if d.get('client_id') else '❌', d)"

# merge
curl -s -X POST http://127.0.0.1:8003/api/v1/leads \
  -H "Content-Type: application/json" -H "X-Internal-Key: $INTERNAL_KEY" \
  -d '{"idempotency_key":"final-002","source":"avito","source_id":"chat_final_2","client_name":"Другой","phone":"79009999999"}' \
  | python3.12 -c "import sys,json; d=json.load(sys.stdin); print('✅ merge' if d.get('status')=='merged' else '❌', d)"

# без ключа
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8003/api/v1/leads \
  -H "Content-Type: application/json" -d '{"idempotency_key":"x","source":"avito","source_id":"x"}')
echo "Код без ключа: $HTTP_CODE (ожидаем 401 или 403 по FOUNDATION)"

pkill -f "uvicorn src.main:app.*8003"

# Очистка
sqlite3 /opt/mn/crm-core/data/crm.db "DELETE FROM history WHERE client_id IN (SELECT id FROM clients WHERE name IN ('Финал','Другой')); DELETE FROM processed_keys WHERE idempotency_key LIKE 'final-%'; DELETE FROM clients WHERE name IN ('Финал','Другой');"

# pytest
sudo -u mn-crm bash -c "cd /opt/mn/crm-core && .venv/bin/python -m pytest tests/test_leads.py -v --tb=short"

# CI
bash /opt/mn/scripts/ci_validate.sh

ОБЯЗАТЕЛЬНО:
1. STATE.md:
   Где мы: День 2 завершён. POST /api/v1/leads работает (идемпотентность, дедупликация, merge, 10 тестов).
   Что дальше: День 3 — CRM CRUD + HTMX-дашборд + воронка.
2. Обнови crm-core/progress.md
3. Запиши итог в crm-core/worklog.md
4. cd /opt/mn && git add -A && git commit -m 'day2: POST /api/v1/leads — полный цикл, 10 тестов, CI green' && git push
```

---

## Итого: порядок запуска

| # | Промпт | Фазы | Запусков CC |
|---|--------|------|------------|
| -1 | Трёхфазный цикл в CLAUDE.md | 1 | 1 |
| 0 | Патч (max_clients, STATE.md) | 1 | 1 |
| 1 | ORM-модели | 3 | 3 |
| 2 | Сервисы (idempotency + merger) | 3 | 3 |
| 3 | POST /leads endpoint | 3 | 3 |
| 4 | Тесты | 1 | 1 |
| 5 | Финальная валидация + push | 1 | 1 |

Всего: 7 шагов, 13 запусков Claude Code, ~60 минут.

## Что делать после Дня 2

1. Убедись что все ✅
2. Если есть ❌ — дай Claude Code конкретный промпт на исправление
3. Завтра — День 3: CRM CRUD + HTMX-дашборд + воронка
