# Аудит Промпт 2 — Сервисы (idempotency + lead_merger)
Дата: 2026-03-02

## idempotency.py

### 1. check_idempotency → ищет в processed_keys?
✅ Да. `select(ProcessedKey).where(ProcessedKey.idempotency_key == key)`, `scalar_one_or_none()`. Найден → `json.loads(row.response)`. Не найден → `None`.

### 2. save_idempotency → json.dumps при записи?
✅ Да. `response=json.dumps(response, ensure_ascii=False)`. Создаёт `ProcessedKey(idempotency_key=key, response=...)`, `session.add()`, `session.flush()`.

### 3. Импорты
✅ `from src.models import ProcessedKey`, `from sqlalchemy.ext.asyncio import AsyncSession`, `import json`.

### 4. py_compile
✅ `python -m py_compile src/services/idempotency.py` → OK

---

## lead_merger.py

### 5. find_duplicate → фильтрует deleted_at IS NULL?
✅ Да. Оба запроса содержат `Client.deleted_at.is_(None)`.

### 6. find_duplicate → ищет по phone ИЛИ inn (не AND)?
✅ Да. Два отдельных SELECT: сначала по phone (если не пустой), потом по inn (если не пустой). Возвращает первого найденного.

### 7. merge_lead → НЕ перезаписывает заполненные поля пустыми?
✅ Да. Строка 64: `if new_value is None: continue`. Строка 68: `if current_value is not None and current_value != "" and current_value != 0: continue`. Заполненные поля сохраняются.

### 8. merge_lead → пишет в history с auto=1?
✅ Да. `History(client_id=existing.id, action="lead_merged", details=json.dumps({"updated_fields": [...], "source_id": "..."}), auto=1)`.

### 9. merge_lead → обновляет updated_at?
✅ Да. `existing.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")`.

### 10. Импорты
✅ `from src.models import Client, History`, `from sqlalchemy.ext.asyncio import AsyncSession`, `import json`, `from datetime import datetime, timezone`.

### 11. py_compile
✅ `python -m py_compile src/services/lead_merger.py` → OK

### 12. _MERGEABLE_FIELDS — полный список?
✅ 21 поле: name, phone, telegram, email, inn, company_name, client_type, tax_system, has_employees, employees_count, need, marketplace, city, source_url, qualification_summary, estimated_price, messages_count, first_message_at, source_last_message_at, consent_given_at. Все релевантные поля из LeadRequest покрыты. Маппинг client_name→name и last_message_at→source_last_message_at отражён корректно (поля в _MERGEABLE_FIELDS по DB-именам).

### 13. Соответствие FOUNDATION.md §7
✅ Дедупликация: «если phone ИЛИ inn совпадает с существующим клиентом → обновить существующего» — реализовано.
✅ Идемпотентность: «idempotency_key в теле» → проверяется в processed_keys — реализовано.

---

## Итого
Все 13 проверок: ✅
Расхождений не обнаружено.
