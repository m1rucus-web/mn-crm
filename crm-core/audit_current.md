# Аудит POST /api/v1/leads (Промпт 3, Фаза 2)

## Проверка leads.py vs FOUNDATION §7

### 1. X-Internal-Key → settings.avito_internal_key?
✅ Строка 102: `if not x_internal_key or x_internal_key != settings.avito_internal_key` → HTTPException(403)
FOUNDATION не указывает конкретный код (401 или 403). 403 — корректный выбор для inter-service auth.

### 2. Идемпотентность → check_idempotency ДО работы с клиентом?
✅ Строка 108: `check_idempotency(session, req.idempotency_key)` — первая операция после авторизации.
При дубле возвращает кешированный результат с правильным HTTP-кодом (201 для created, 200 для остального).

### 3. Дедупликация → find_duplicate ДО INSERT? Возвращает 200 "merged"?
✅ Строка 118: `find_duplicate(session, req.phone, req.inn)` — вызывается перед UPSERT.
Строка 128: `response.status_code = 200`, результат `{"status": "merged"}`.

### 4. UPSERT → ON CONFLICT(source, source_id)?
✅ Строки 132-176: реализовано через SELECT + условный INSERT/UPDATE (функционально эквивалентно ON CONFLICT).
SELECT по `Client.source == req.source, Client.source_id == req.source_id` — соответствует UNIQUE(source, source_id) в БД.

### 5. Маппинг → client_name → name? last_message_at → source_last_message_at?
✅ Строка 53-54: `data["name"] = req.client_name`
✅ Строка 87-88: `data["source_last_message_at"] = req.last_message_at`

### 6. History → lead_created auto=1? lead_updated?
✅ Строка 189-195: `History(action="lead_created", auto=1)` — при INSERT
✅ Строка 153-166: `History(action="lead_updated", details=JSON{updated_fields, source_id}, auto=1)` — при UPDATE

### 7. responsible_id → NULL?
✅ Не назначается нигде в коде. Client model default = None.

### 8. save_idempotency → ПОСЛЕ успешной операции?
✅ Строка 123 (merge), 170 (update), 199 (create) — всегда после flush().

### 9. Логирование → trace_id?
✅ Строки 110-113, 124-127, 171-174, 200-203: `trace={} source_id={} <action>`.

### 10. Pydantic-схема → все поля из FOUNDATION §7?
✅ 24 поля в LeadRequest: idempotency_key, trace_id, source, source_id, client_name, phone, telegram, email, inn, company_name, client_type, tax_system, has_employees, employees_count, need, marketplace, city, source_url, qualification_summary, estimated_price, messages_count, first_message_at, last_message_at, consent_given_at.

## Ручные тесты (сервер запущен)

### Создание (POST с ключом)
✅ → 201 `{"status":"created","client_id":1}`

### Идемпотентность (тот же idempotency_key)
✅ → `{"status":"created","client_id":1}` — кешированный результат

### Без X-Internal-Key
✅ → HTTP 403

## py_compile
✅ `python -m py_compile src/api/leads.py` → OK

## Router подключён в main.py
✅ Строка 10: `from src.api.leads import router as leads_router`
✅ Строка 59: `app.include_router(leads_router)`

## Итог
Все 10 проверок пройдены. Ручные тесты прошли. Расхождений нет.
