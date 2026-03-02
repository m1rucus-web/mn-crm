# Аудит ORM-моделей — Промпт 1 Фаза 2

Дата: 2026-03-02

Источники: FOUNDATION.md §6, init_db.py, models.py

---

## 1. clients (36 полей)

- ✅ id: INTEGER PRIMARY KEY AUTOINCREMENT → mapped_column(primary_key=True, autoincrement=True)
- ✅ source: TEXT NOT NULL → String, nullable=False
- ✅ source_id: TEXT → String | None
- ✅ idempotency_key: TEXT UNIQUE → String, unique=True
- ✅ UNIQUE(source, source_id) → __table_args__ = (UniqueConstraint("source", "source_id"),)
- ✅ name: TEXT → String | None
- ✅ phone, telegram, email, inn, company_name, client_type, tax_system: TEXT → String | None
- ✅ has_employees: INTEGER DEFAULT 0 → Integer, default=0, server_default="0"
- ✅ employees_count: INTEGER DEFAULT 0 → Integer, default=0, server_default="0"
- ✅ need, marketplace, city, source_url: TEXT → String | None
- ✅ pipeline_stage: TEXT DEFAULT 'new' → String, default="new", server_default="new"
- ✅ responsible_id: INTEGER REFERENCES employees(id) → ForeignKey("employees.id")
- ✅ qualification_summary: TEXT → Text | None
- ✅ estimated_price: TEXT → String | None
- ✅ monthly_price: INTEGER → Integer | None
- ✅ notes: TEXT → Text | None
- ✅ is_waiting_docs: INTEGER DEFAULT 0 → Integer, default=0, server_default="0"
- ✅ is_vip_newcomer: INTEGER DEFAULT 0 → Integer, default=0, server_default="0"
- ✅ last_client_message_at: TEXT → String | None
- ✅ messages_count: INTEGER DEFAULT 0 → Integer, default=0, server_default="0"
- ✅ first_message_at: TEXT → String | None
- ✅ source_last_message_at: TEXT → String | None
- ✅ drip_campaign_step: INTEGER DEFAULT 0 → Integer, default=0, server_default="0"
- ✅ drip_next_at: TEXT → String | None
- ✅ drip_active: INTEGER DEFAULT 0 → Integer, default=0, server_default="0"
- ✅ consent_given_at: TEXT → String | None
- ✅ deleted_at: TEXT → String | None
- ✅ created_at: TEXT DEFAULT (datetime('now')) → server_default=text("(datetime('now'))")
- ✅ updated_at: TEXT DEFAULT (datetime('now')) → server_default=text("(datetime('now'))")

Полей в init_db.py: 36. Полей в models.py: 36. ✅ Совпадает.

---

## 2. employees (11 полей)

- ✅ id: PRIMARY KEY AUTOINCREMENT
- ✅ telegram_user_id: INTEGER UNIQUE NOT NULL
- ✅ name: TEXT NOT NULL
- ✅ short_name: TEXT → String | None
- ✅ username: TEXT → String | None
- ✅ role: TEXT DEFAULT 'accountant' → default="accountant", server_default="accountant"
- ✅ max_clients: models.py = default=20, server_default="20" (решение 2 марта: max_clients=20, НЕ 50)
  - Примечание: init_db.py и FOUNDATION имеют DEFAULT 50. models.py правильно использует 20 по решению.
- ✅ status: TEXT DEFAULT 'active' → default="active", server_default="active"
- ✅ substitute_id: INTEGER REFERENCES employees(id) → ForeignKey("employees.id")
- ✅ is_active: INTEGER DEFAULT 1 → default=1, server_default="1"
- ✅ created_at: TEXT DEFAULT (datetime('now'))

Полей в init_db.py: 11. Полей в models.py: 11. ✅ Совпадает.

---

## 3. history (7 полей)

- ✅ id: PRIMARY KEY AUTOINCREMENT
- ✅ client_id: INTEGER REFERENCES clients(id) → ForeignKey("clients.id")
- ✅ action: TEXT NOT NULL → nullable=False
- ✅ details: TEXT → Text | None
- ✅ employee_id: INTEGER → Integer | None
- ✅ auto: INTEGER DEFAULT 0 → default=0, server_default="0"
- ✅ created_at: TEXT DEFAULT (datetime('now'))

Полей в init_db.py: 7. Полей в models.py: 7. ✅ Совпадает.

---

## 4. tasks (10 полей)

- ✅ id: PRIMARY KEY AUTOINCREMENT
- ✅ client_id: INTEGER REFERENCES clients(id) → ForeignKey("clients.id")
- ✅ employee_id: INTEGER → Integer | None
- ✅ type: TEXT NOT NULL → nullable=False
- ✅ description: TEXT → Text | None
- ✅ due_at: TEXT NOT NULL → nullable=False
- ✅ completed_at: TEXT → String | None
- ✅ status: TEXT DEFAULT 'pending' → default="pending", server_default="pending"
- ✅ deleted_at: TEXT → String | None
- ✅ created_at: TEXT DEFAULT (datetime('now'))

Полей в init_db.py: 10. Полей в models.py: 10. ✅ Совпадает.

---

## 5. onboarding_documents (8 полей)

- ✅ id: PRIMARY KEY AUTOINCREMENT
- ✅ client_id: INTEGER REFERENCES clients(id) → ForeignKey("clients.id")
- ✅ doc_type: TEXT NOT NULL → nullable=False
- ✅ doc_name: TEXT NOT NULL → nullable=False
- ✅ is_received: INTEGER DEFAULT 0 → default=0, server_default="0"
- ✅ received_at: TEXT → String | None
- ✅ last_reminder_at: TEXT → String | None
- ✅ created_at: TEXT DEFAULT (datetime('now'))

Полей в init_db.py: 8. Полей в models.py: 8. ✅ Совпадает.

---

## 6. processed_keys (3 поля)

- ✅ idempotency_key: TEXT PRIMARY KEY → primary_key=True (НЕ просто UNIQUE — правильно!)
- ✅ response: TEXT → Text | None
- ✅ created_at: TEXT DEFAULT (datetime('now'))

Полей в init_db.py: 3. Полей в models.py: 3. ✅ Совпадает.

---

## 7. outbox (15 полей)

- ✅ id: PRIMARY KEY AUTOINCREMENT
- ✅ target_url: TEXT NOT NULL → nullable=False
- ✅ method: TEXT DEFAULT 'POST' → default="POST", server_default="POST"
- ✅ payload: TEXT NOT NULL → Text, nullable=False
- ✅ idempotency_key: TEXT UNIQUE → unique=True
- ✅ trace_id: TEXT → String | None
- ✅ aggregate_key: TEXT → String | None
- ✅ status: TEXT DEFAULT 'pending' → default="pending", server_default="pending"
- ✅ attempts: INTEGER DEFAULT 0 → default=0, server_default="0"
- ✅ max_attempts: INTEGER DEFAULT 10 → default=10, server_default="10"
- ✅ next_retry_at: TEXT → String | None
- ✅ created_at: TEXT DEFAULT (datetime('now'))
- ✅ sent_at: TEXT → String | None
- ✅ response_code: INTEGER → Integer | None
- ✅ error: TEXT → Text | None

Полей в init_db.py: 15. Полей в models.py: 15. ✅ Совпадает.

---

## 8. drip_events (6 полей)

- ✅ id: PRIMARY KEY AUTOINCREMENT
- ✅ client_id: INTEGER NOT NULL → nullable=False
- ✅ step: INTEGER NOT NULL → nullable=False
- ✅ event_type: TEXT NOT NULL → nullable=False
- ✅ event_at: TEXT DEFAULT (datetime('now')) → server_default=text("(datetime('now'))")
- ✅ meta: TEXT → Text | None

Полей в init_db.py: 6. Полей в models.py: 6. ✅ Совпадает.

---

## Итого

| Таблица | Полей init_db | Полей models | Совпадает |
|---------|--------------|-------------|-----------|
| clients | 36 | 36 | ✅ |
| employees | 11 | 11 | ✅ |
| history | 7 | 7 | ✅ |
| tasks | 10 | 10 | ✅ |
| onboarding_documents | 8 | 8 | ✅ |
| processed_keys | 3 | 3 | ✅ |
| outbox | 15 | 15 | ✅ |
| drip_events | 6 | 6 | ✅ |

**Все 8 моделей — 96 полей — полностью совпадают с init_db.py и FOUNDATION.md §6.**

Примечание: max_clients в init_db.py = 50, в models.py = 20. Это осознанное решение от 2 марта (не расхождение).
