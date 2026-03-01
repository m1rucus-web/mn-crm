# FOUNDATION.md — Фаза 1: Лидогенерация

> Версия: 4.9 | Дата: 2026-02-27
> Статус: Фаза 1 — к реализации (6 стресс-тестов + 2 итерации аудитора + launch review)
> v4.8: consent в CRM, DaData ключи, webhook /webhook/avito, backups в дереве
> v4.9: код с нуля (старый удалён), templates/ в структуре, SSL подтверждён,
>       ai_logs таблица в bot.db, stage_change в history, промпт «помощник» вместо «менеджер»

---

## Что это и зачем

**Компания:** «Метод Никифорова» — удалённое бухгалтерское сопровождение ИП и ООО. 5 бухгалтеров, 55 клиентов → 155 за 3-6 месяцев. Средний чек 15 000₽.

**Фаза 1** — минимум для получения новых клиентов: Авито-бот (лиды) + CRM-ядро (воронка) + связка через outbox. Всё остальное — в следующих фазах.

**Другие фазы (кратко):**
- Фаза 2: Мессенджер-хаб (Telegram + WhatsApp для бухгалтеров)
- Фаза 3: Аналитика + дашборды + утренние отчёты
- Фаза 4: Клиентский портал, биллинг, PostgreSQL-миграция

Архитектура: 7 изолированных микросервисов на одном сервере, SQLite WAL, HTTP + outbox-паттерн. В Фазе 1 работают только 2 из 7: Авито-бот (порт 8001) и CRM-ядро (порт 8003).

---

## 1. Инфраструктура

**Сервер:** Timeweb Cloud, Ubuntu 24.04, 4 ядра, 8 ГБ RAM. IP: 5.129.227.210. Домен: nikiforov-bots.ru.

```
/opt/mn/                        ← Корень системы
├── FOUNDATION.md               ← Этот документ
├── shared/config/              ← JSON-конфиги (read-only для сервисов)
│   ├── pricelist.json          ← Цены
│   ├── company.json            ← Реквизиты
│   ├── employees.json          ← Сотрудники (→ мигрирует в БД CRM)
│   ├── work_hours.json         ← Рабочие часы
│   ├── ai_models.json          ← AI-модели
│   ├── tax_calendar.json       ← Сроки отчётности
│   ├── templates.json          ← Шаблоны сообщений
│   ├── objections.json         ← Скрипты возражений
│   ├── brand_voice.json        ← Тон и стиль
│   └── services_catalog.json   ← Каталог услуг
├── shared/templates/           ← Шаблоны документов
│   ├── contract_template.docx  ← Шаблон договора (docxtpl)
│   └── logo.png                ← Логотип для КП
├── shared/healthcheck.sh       ← Мониторинг (cron */5)
├── avito-bot/                  ← Сервис 1 (порт 8001, пользователь mn-avito)
│   ├── .env, CLAUDE.md, data/bot.db
│   └── src/, scripts/, tests/
└── crm-core/                   ← Сервис 3 (порт 8003, пользователь mn-crm)
    ├── .env, CLAUDE.md, data/crm.db
    └── src/, scripts/, tests/
├── backups/                    ← Бэкапы SQLite (cron, chmod 700 root)
```

**Изоляция:** Каждый сервис — свой Linux-пользователь, chmod 700. Claude Code под `mn-avito` физически не видит `/opt/mn/crm-core/`. shared/ — chmod 755, только чтение.

```bash
# Создание (шаг 1.0)
useradd -r -s /bin/bash -d /opt/mn/avito-bot mn-avito
useradd -r -s /bin/bash -d /opt/mn/crm-core mn-crm
chown -R mn-avito:mn-avito /opt/mn/avito-bot && chmod 700 /opt/mn/avito-bot
chown -R mn-crm:mn-crm /opt/mn/crm-core && chmod 700 /opt/mn/crm-core
chown -R root:root /opt/mn/shared && chmod -R 755 /opt/mn/shared
```

**Стек:** Python 3.12, FastAPI, aiogram 3.x, SQLite WAL, SQLAlchemy async, httpx, loguru, APScheduler, Jinja2 + HTMX, pydantic-settings.

**Nginx:** `nikiforov-bots.ru/crm/` → CRM (8003), `/webhook/avito` → Авито-бот (8001). Webhook вынесен из /crm/ чтобы не путать при отладке.

**Бэкапы:** `sqlite3.Connection.backup()` каждые 6 часов → `/opt/mn/backups/`. 30 дней хранения. После бэкапа: `PRAGMA integrity_check;` на копии → ≠ 'ok' → алерт. **НЕ использовать cp — небезопасно при WAL.**

**Recovery:** остановить оба сервиса → восстановить DB из бэкапа → `UPDATE outbox SET status='failed' WHERE status='pending'` → запуск → проверка `/health`.

---

## 2. Outbox-паттерн (связь между сервисами)

Сервисы НЕ вызывают друг друга напрямую. Запись → outbox (своя БД) → фоновая задача (30 сек) → HTTP → подтверждение.

```sql
CREATE TABLE outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_url TEXT NOT NULL,
    method TEXT DEFAULT 'POST',
    payload TEXT NOT NULL,
    idempotency_key TEXT UNIQUE,
    trace_id TEXT,
    aggregate_key TEXT,  -- lead:42 / client:42 — для блокировки по клиенту
    status TEXT DEFAULT 'pending',  -- pending / sent / confirmed / failed
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 10,
    next_retry_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    sent_at TEXT, response_code INTEGER, error TEXT
);
CREATE INDEX idx_outbox_pending ON outbox(status) WHERE status='pending';
CREATE INDEX idx_outbox_aggregate ON outbox(aggregate_key, id) WHERE status IN ('pending','failed');
```

**Правила:**
- Обработка строго `ORDER BY id ASC`
- Блокировка по `aggregate_key`: если для одного ключа есть pending/failed с меньшим id — следующие ждут
- 10 попыток, backoff 1/2/4/8 мин. После 10 — status=failed, алерт в Telegram
- `POST /api/v1/admin/outbox/replay-failed` — ручной протолк застрявших
- Каждый запрос получает `trace_id` (UUID) в Авито-боте, проходит через всю цепочку

**Идемпотентность:** Каждый запрос содержит `idempotency_key`. Принимающий сервис хранит `processed_keys` — если ключ уже был, возвращает предыдущий результат без дублирования.

---

## 3. Безопасность

- **Анонимизация (ФЗ-152):** `anonymize_text()` перед каждым вызовом LLM. ФИО, ИНН, телефоны НЕ уходят в OpenRouter
- **Пост-проверка AI:** Regex: число + ₽/руб < 7000 → блокировка + алерт. Расширить на числительные прописью («пять тысяч», «шесть тысяч»). AI называет цены только словами: «от семи до пятнадцати тысяч»
- **Soft Deletes:** Бизнес-сущности (`clients`, `tasks`) имеют `deleted_at`. DELETE запрещён для них. SELECT фильтрует `WHERE deleted_at IS NULL`. Служебные таблицы (`employees`, `history`, `processed_keys`, `onboarding_documents`) — без soft delete
- **ПДн-оферта:** В первом сообщении бота — согласие на обработку ПДн. Фиксация: `leads.consent_given_at` заполняется при первом ответе клиента после оферты. Без согласия — AI не активируется
- **SQLite:** `PRAGMA busy_timeout=5000; PRAGMA journal_mode=WAL;` при инициализации
- **WAL checkpoint:** Ночная задача 03:00 МСК: `PRAGMA wal_checkpoint(PASSIVE);` (НЕ TRUNCATE — PASSIVE не блокирует записи). TRUNCATE только при graceful shutdown
- **Бэкап:** `sqlite3.Connection.backup()` каждые 6ч. После — `PRAGMA integrity_check;` на копии. Результат ≠ 'ok' → алерт
- **Semaphore:** `asyncio.Semaphore(3)` на все AI-вызовы
- **Таймауты:** `httpx.AsyncClient(timeout=15.0)` для AI, `timeout=30.0` для Whisper. При timeout → ответ из шаблона + retry
- **Авторизация между сервисами:** РАЗДЕЛЬНЫЕ ключи. Авито-бот хранит `CRM_INTERNAL_KEY`, CRM хранит `AVITO_INTERNAL_KEY`. Компрометация одного ≠ доступ к другому
- **processed_keys TTL:** Cron: `DELETE FROM processed_keys WHERE created_at < datetime('now', '-90 days');`

**Уроки инцидентов:**
- 96 спам-сообщений → whitelist + rate limiter + планировщики отключены по умолчанию
- «Сообщение удалено» → фильтрация системных сообщений Авито

---

## 4. Авито-бот (Сервис 1, порт 8001)

**Задача:** Лид с Авито → AI-квалификация → контакт → передача в CRM. Также принимает команды на отправку сообщений от CRM (drip, напоминания).

**AI:** gemini-2.5-flash ($0.15/$0.60), fallback deepseek-v3.2 ($0.14/$0.28). Async webhook: return 200 OK сразу, AI через `asyncio.create_task()`.
При switch на fallback → логировать. Промпт одинаковый, но в system добавить: `Strictly follow: ONE question per message, no lists, max 3 sentences.`

**Правила:** дебаунс 8 сек, ночной режим (22–08 МСК, шаблонный автоответ), rate limiter (10/мин, 60/час, 300/день), whitelist.
**Авито API limits:** ~60 req/min. При 429 → очередь исходящих с retry backoff. Не терять сообщения.

### Промпт Елизаветы

```text
Ты Елизавета, помощник бухгалтера в компании «Метод Никифорова».
Цель: квалифицировать лида и взять номер телефона для передачи бухгалтеру.

КРИТИЧЕСКИЕ ПРАВИЛА:
1. Не задавай больше 1 НОВОГО вопроса в сообщении.
   Можно: подтверждение + вопрос ("Понял, ИП на УСН. А сотрудники есть?")
   Нельзя: два новых вопроса подряд ("Какая система? И сотрудники есть?")
2. Живой, слегка неформальный язык. НЕ "Какая форма собственности?",
   А "Вы как ИП работаете или ООО открыли?"
3. Эмпатия: жалоба на штрафы → "Ох, знакомая история, налоговая лютует.
   А у вас УСН или Патент?"

ПОРЯДОК КВАЛИФИКАЦИИ (приоритет):
   Сначала узнай: ИП/ООО → система налогообложения → сотрудники.
   Только ПОСЛЕ квалификации → называй вилку цены и проси номер.
   Не проси номер, пока не знаешь хотя бы ИП/ООО.

4. Цена (после квалификации): "Базово от 7000 до 15000 руб,
   зависит от документов. Давайте бухгалтер прикинет точную
   смету? Напишите номер."
5. "Вы бот?": "Я AI-помощник. Помогаю собрать вводные, чтобы
   подключился нужный бухгалтер. Так что, сотрудники есть
   или пока один работаете?"

ПРАВИЛО ВЫХОДА (приоритет над квалификацией):
6. Если клиент дал номер телефона — ПРЕРВАТЬ любые вопросы.
   Ответить: "Отлично, передала профильному бухгалтеру,
   свяжется с вами для точного расчёта!"
   Внутренний статус → [HANDOFF_READY].

ГОЛОСОВЫЕ СООБЩЕНИЯ:
7. Если видишь префикс [Голосовое: ...] — это аудио от клиента.
   Всегда показывай, что прослушала: "Прослушала, поняла вас.
   Подскажите..." Никогда не игнорируй голосовые.

УЗКИЕ ВОПРОСЫ (налоги, ОКВЭД, специфика):
8. НЕ консультировать. Приём «перевод стрелок»:
   "Отличный вопрос, там есть нюансы. Давайте бухгалтер
   прямо сейчас это проверит — напишите номер?"

ДРУГОЙ ЯЗЫК:
9. Отвечать на языке клиента. Квалификацию собирать так же.

АГРЕССИЯ / ОСКОРБЛЕНИЯ:
10. Деэскалация: "Понимаю, ситуация неприятная. Давайте
    подключу руководителя, он поможет разобраться."
    Внутренний статус → [HANDOFF_READY].

ИНН ПЕРВЫМ СООБЩЕНИЕМ (happy-path):
11. Если клиент сразу прислал ИНН — сохранить. НЕ переспрашивай
    то, что уже известно из ИНН (код триггерит DaData-запрос,
    обогащает контекст: ИП/ООО, название). Спроси только то,
    чего DaData не знает: "Спасибо! А какая система
    налогообложения — УСН, патент?" При наличии телефона →
    сразу [HANDOFF_READY].

ЗАПРЕЩЕНО: списки вопросов маркерами, споры, цены вне pricelist.json,
давать конкретные суммы налогов/штрафов.

ДЛИНА ОТВЕТА: максимум 3 предложения. Авито-чат = как SMS.
Если нужно больше — разбей на несколько сообщений. + max_tokens: 200 в API-вызове.
```

**Пост-процессор (код, не промпт):** Перед отправкой AI-ответа — проверка количества `?`. Если больше 1 вопросительного знака → обрезать до первого вопроса. Страховка от нарушения правила «1 вопрос за раз».

⚠️ **Синхронизация:** В `brand_voice.json` обязательно `"max_questions_per_message": 1`. Если стоит `2` — промпт и конфиг будут конфликтовать.

**Ночной автоответ (22–08 МСК):** AI выключен, но клиент получает шаблонный ответ (не AI):
«Спасибо за обращение! Бухгалтер ответит утром до 9:00. А пока — вы как ИП работаете или ООО?»
Собирает квалификационную информацию даже ночью. Ответ обрабатывается утром.

### Возражения (objections.json)

| Триггер | Ответ |
|---------|-------|
| Конкуренты (кнопка, моё дело, точка) | «Сервисы при банках — калькуляторы, не несут ответственность за ошибки. У нас живой бухгалтер, который берёт риски на себя.» |
| Дорого | «За 2000₽ — один человек, бросит при болезни. У нас закреплённый бухгалтер + материальная ответственность. Давайте посчитаем ваш вариант?» |
| Подумаю | «Конечно. Пока скину чеклист по вашей системе. Оставите номер для WhatsApp?» |

### Голосовые (Whisper)

Сообщение < 2 мин → скачать → Whisper API → `[Голосовое: <текст>]` → AI как обычный текст. Строители/водители не печатают.
Сообщение > 2 мин → обрезать первые 2 мин → Whisper → ответ: «Получила ваше голосовое! Обработала первую часть. Если что-то важное было дальше — продублируйте текстом 🙏»
**Fallback:** Whisper недоступен → «Извините, не удалось прослушать голосовое. Можете продублировать текстом?»

### AI-саммари при handoff

Статус «передано бухгалтеру» → GPT-4o-mini **через OpenRouter** (не прямое OpenAI API): «Выжимка в 3 строки: кто, налоги, боль» → `qualification_summary`. Все AI-модели идут через OpenRouter — один ключ, одна точка входа, прописано в `ai_models.json`.

### Drip-кампания (ИЗОЛИРОВАННЫЙ МОДУЛЬ)

⚠️ Отдельный модуль, НЕ часть основной логики. Rate limit: 1 msg / 2 min.

Статусы: `lost_thinking` / `lost_silent` / `lost_competitor`. Drip управляется из CRM, сообщения отправляются через `POST /api/v1/send-message` Авито-бота.

**Триггер старта:** 3 дня после `last_client_message_at` (НЕ после смены статуса). Если клиент написал «отложу на месяц» — drip начнётся через 3 дня после этого сообщения.

**Обработка блокировки:** Если бот вернул 403 (blocked_by_user) — CRM мгновенно ставит `lost_banned`, обнуляет drip_campaign_step, `drip_active=0`, отменяет pending outbox.

**State-machine:** При любом входящем ответе клиента на drip-сообщение: `drip_active=0`, `pipeline_stage=contacted`, задача менеджеру. Лид НЕ может быть одновременно в drip и в ручной работе.

Ответил → возвращается в воронку. 7-й без ответа → `lost_final`.

**Аналитика drip:** Таблица `drip_events` в crm.db (см. раздел 6). KPI по шагу: reply_rate = replied / sent, conversion_rate = converted / sent.

| Шаг | День | Суть |
|-----|------|------|
| 1 | 3 | Польза: «3 способа снизить налог на {tax_system}» |
| 2 | 7 | Кейс: «Нашли переплату ПФР 40к. Можем заглянуть в вашу 1С?» |
| 3 | 14 | Срок: «До {дедлайн} нужно сдать {отчёт}. Можем взять как разовое» |
| 4 | 21 | От руководителя: «Не устроила цена или отложили?» |
| 5 | 30 | Закрытие: «Удалось решить вопрос с бухгалтерией? Да или нет — и закрою заявку» |
| 6 | 45 | Закон: «Меняются правила уведомлений, вот разбор» |
| 7 | 60 | Прощание: «Закрываем заявку. Удачи, контакт у вас есть» |

### Тег «Крупная рыба»

ООО или ОСНО → 🍒 КРУПНЫЙ КЛИЕНТ → handoff на сильного менеджера. ООО ОСНО НДС = чек 24 000₽+.

### Код-триггер ИНН → DaData

При обнаружении паттерна ИНН (10 или 12 цифр) в сообщении клиента → автоматический запрос DaData → обогащение контекста AI (ИП/ООО, название, адрес). AI не переспрашивает то, что уже известно.

### Двухэтапная передача в CRM

Лид уходит в CRM **дважды** через outbox:
1. **Первое сообщение клиента** → пустая карточка (имя, avito_chat_id). Бухгалтер сразу видит нового лида
2. **При handoff** → UPSERT: квалификация, контакты, тег 🍒, estimated_price

**Уведомление клиенту при handoff:** Бот отправляет: «Передала вашу заявку бухгалтеру {short_name}. Позвонит в течение часа. Если не дозвонится — напишет сюда.» Клиент не висит в тишине.

CRM принимает через `ON CONFLICT (source_id) DO UPDATE`.

---

## 5. CRM-ядро (Сервис 3, порт 8003)

**Задача:** Карточка клиента, воронка, задачи, назначение бухгалтеров.

**Воронка (`pipeline_stage` — единственное поле статуса):** new → contacted → cp → contract → payment → onboarding → active / lost_* / lost_banned

**Правило:** КАЖДОЕ изменение `pipeline_stage` → запись в `history`: `action='stage_change'`, `details=JSON {"from": "new", "to": "contacted"}`, `auto=1` если автоматическое. Это питает `GET /api/v1/stats/funnel` и позволяет считать конверсию между этапами. CRM также шлёт обновление в Авито-бот через outbox при переходе в `contract`/`payment`/`active` (→ `POST /api/v1/leads/{chat_id}/status`).

**Ключевые фичи Фазы 1:**
- **SLA-монитор** (cron 10 мин): new > 1 час → алерт. КП > 48 часов → задача. Event-driven альтернатива: при создании клиента → `APScheduler.add_job(check_sla, run_date=created_at + 1h)`
- **Генератор КП:** `POST /leads/{id}/generate-cp` → PDF с логотипом за 10 секунд. Доставка: ссылка в Авито/WhatsApp. Если не ответил 24ч → авто-напоминание
- **Onboarding-бот:** чеклист документов, напоминания каждые 2 дня
- **Замещение:** `employees.status` + `substitute_id`. Отпуск → сообщения идут заместителю. **При fired** → все клиенты → substitute_id или руководитель
- **task_generator.py** (cron 1-е число): авто-задачи по tax_calendar
- **Триггер найма:** > 20 клиентов на бухгалтера → задача руководителю «начать поиск». > 23 → drip-кампания на паузу, новые лиды в очередь
- **VIP-новичок:** created_at < 30 дней → 🚨 приоритет + авто-сообщение день 3
- **Churn detector** (cron ежедневно): нет контактов 30+ дней → задача руководителю
- **Авто-договоры:** docxtpl + SLA-пункт: «документы за 3 дня до дедлайна»
- **Проверка контрагентов:** DaData → реквизиты, ликвидация, массовый адрес

---

## 6. Схемы БД

### bot.db (Авито-бот)

```sql
CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avito_chat_id TEXT UNIQUE NOT NULL,
    client_name TEXT, phone TEXT, telegram TEXT, email TEXT,
    inn TEXT, company_name TEXT, client_type TEXT, tax_system TEXT,
    has_employees INTEGER DEFAULT 0, employees_count INTEGER DEFAULT 0,
    need TEXT, marketplace TEXT, city TEXT,
    status TEXT DEFAULT 'new',  -- new/ai_active/handoff (все lost_* статусы ТОЛЬКО в CRM)
    ai_enabled INTEGER DEFAULT 1,
    qualification_summary TEXT, estimated_price TEXT,
    avito_url TEXT, source_ad TEXT,
    consent_given_at TEXT,       -- ФЗ-152: фиксация времени согласия на обработку ПДн
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    avito_msg_id TEXT UNIQUE NOT NULL,
    lead_id INTEGER REFERENCES leads(id),
    direction TEXT CHECK(direction IN ('in','out')),
    content TEXT, msg_type TEXT DEFAULT 'text',
    is_ai_response INTEGER DEFAULT 0, ai_model TEXT,
    ai_tokens_in INTEGER,        -- логирование расхода AI
    ai_tokens_out INTEGER,
    ai_cost_usd REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL, short_name TEXT, username TEXT,
    role TEXT DEFAULT 'accountant', is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE topic_mapping (avito_chat_id TEXT PRIMARY KEY, telegram_topic_id INTEGER NOT NULL);  -- используется при подключении Telegram-моста
CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT);

-- Outbox (межсервисное общение, схема из раздела 2)
CREATE TABLE outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_url TEXT NOT NULL, method TEXT DEFAULT 'POST',
    payload TEXT NOT NULL, idempotency_key TEXT UNIQUE, trace_id TEXT,
    aggregate_key TEXT,
    status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 10, next_retry_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    sent_at TEXT, response_code INTEGER, error TEXT
);
CREATE INDEX idx_outbox_pending ON outbox(status) WHERE status='pending';
CREATE INDEX idx_outbox_aggregate ON outbox(aggregate_key, id) WHERE status IN ('pending','failed');

CREATE INDEX idx_messages_lead ON messages(lead_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created ON leads(created_at);

-- AI-логирование: аудит-трейл решений и расходов
CREATE TABLE ai_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER REFERENCES leads(id),
    model TEXT NOT NULL,           -- gemini-2.5-flash / deepseek-v3.2
    prompt_hash TEXT,              -- SHA256 первых 100 символов (для группировки)
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0,      -- стоимость вызова
    response_summary TEXT,         -- первые 100 символов ответа
    is_fallback INTEGER DEFAULT 0, -- 1 если сработал fallback на DeepSeek
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_ai_logs_lead ON ai_logs(lead_id);
CREATE INDEX idx_ai_logs_date ON ai_logs(created_at);
```

### crm.db (CRM-ядро)

```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL, source_id TEXT, idempotency_key TEXT UNIQUE,
    UNIQUE(source, source_id),  -- для UPSERT при двухэтапной передаче лида
    name TEXT,  -- маппинг: API client_name → DB name
    phone TEXT, telegram TEXT, email TEXT,
    inn TEXT, company_name TEXT, client_type TEXT, tax_system TEXT,
    has_employees INTEGER DEFAULT 0, employees_count INTEGER DEFAULT 0,
    need TEXT, marketplace TEXT, city TEXT,
    source_url TEXT,                     -- ссылка на объявление Авито (контекст для бухгалтера)
    pipeline_stage TEXT DEFAULT 'new',  -- new→contacted→cp→contract→payment→onboarding→active→lost_*/lost_banned
    responsible_id INTEGER REFERENCES employees(id),
    qualification_summary TEXT, estimated_price TEXT, monthly_price INTEGER, notes TEXT,
    is_waiting_docs INTEGER DEFAULT 0,
    is_vip_newcomer INTEGER DEFAULT 0,
    last_client_message_at TEXT,
    messages_count INTEGER DEFAULT 0,    -- из API: кол-во сообщений в чате Авито
    first_message_at TEXT,               -- из API: время первого сообщения
    source_last_message_at TEXT,         -- из API: время последнего сообщения на площадке
    drip_campaign_step INTEGER DEFAULT 0,
    drip_next_at TEXT,
    drip_active INTEGER DEFAULT 0,       -- 0=не в кампании, 1=активная drip-цепочка
    consent_given_at TEXT,               -- ФЗ-152: из bot.db, передаётся в API при handoff
    deleted_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_user_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL, short_name TEXT,
    username TEXT,                        -- Telegram @username (для упоминания в топиках)
    role TEXT DEFAULT 'accountant', max_clients INTEGER DEFAULT 50,
    status TEXT DEFAULT 'active',  -- active/vacation/sick/fired
    substitute_id INTEGER REFERENCES employees(id),
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER REFERENCES clients(id),
    action TEXT NOT NULL, details TEXT,
    employee_id INTEGER, auto INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER REFERENCES clients(id),
    employee_id INTEGER, type TEXT NOT NULL,
    description TEXT, due_at TEXT NOT NULL,
    completed_at TEXT, status TEXT DEFAULT 'pending',
    deleted_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE onboarding_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER REFERENCES clients(id),
    doc_type TEXT NOT NULL, doc_name TEXT NOT NULL,
    is_received INTEGER DEFAULT 0, received_at TEXT, last_reminder_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE processed_keys (
    idempotency_key TEXT PRIMARY KEY, response TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_clients_responsible ON clients(responsible_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_clients_pipeline ON clients(pipeline_stage) WHERE deleted_at IS NULL;
CREATE INDEX idx_clients_inn ON clients(inn) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX idx_clients_inn_unique ON clients(inn) WHERE inn IS NOT NULL AND deleted_at IS NULL;  -- дедупликация: один ИНН = один клиент
CREATE INDEX idx_history_client ON history(client_id);
CREATE INDEX idx_history_action ON history(action) WHERE action='stage_change';  -- для funnel stats
CREATE INDEX idx_tasks_client ON tasks(client_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_tasks_employee_due ON tasks(employee_id, due_at) WHERE status='pending';
CREATE INDEX idx_onboarding_client ON onboarding_documents(client_id) WHERE is_received=0;

-- Outbox (межсервисное общение)
CREATE TABLE outbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_url TEXT NOT NULL, method TEXT DEFAULT 'POST',
    payload TEXT NOT NULL, idempotency_key TEXT UNIQUE, trace_id TEXT,
    aggregate_key TEXT,
    status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 10, next_retry_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    sent_at TEXT, response_code INTEGER, error TEXT
);
CREATE INDEX idx_outbox_pending_crm ON outbox(status) WHERE status='pending';
CREATE INDEX idx_outbox_aggregate_crm ON outbox(aggregate_key, id) WHERE status IN ('pending','failed');

-- Аналитика drip-кампании
CREATE TABLE drip_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    step INTEGER NOT NULL,
    event_type TEXT NOT NULL,  -- scheduled/sent/delivered/replied/converted/failed
    event_at TEXT DEFAULT (datetime('now')),
    meta TEXT
);
CREATE INDEX idx_drip_events_client_step ON drip_events(client_id, step);
```

---

## 7. API-контракты Фазы 1

**Авторизация:** `X-Internal-Key`. **Trace:** `X-Trace-Id` (UUID). **Идемпотентность:** `idempotency_key` в теле.

### Авито-бот → CRM: Новая заявка (двухэтапная)

Лид отправляется в CRM **дважды**:
1. **При первом сообщении** — создаётся пустая карточка (имя + avito_chat_id)
2. **При handoff** — UPSERT с полной квалификацией, тегом 🍒, estimated_price

CRM обрабатывает через `ON CONFLICT (source_id) DO UPDATE SET qualification_summary = excluded.qualification_summary, ...`

**Дедупликация по phone/inn:** При POST /api/v1/leads — если phone ИЛИ inn совпадает с существующим клиентом → обновить существующего, вернуть `{"status": "merged", "client_id": ...}`. Не создавать дубль. Это критично: один клиент может писать по разным объявлениям.

```
POST http://localhost:8003/api/v1/leads
{
  "idempotency_key": "avito-lead-{chat_id}",  // стабильный, НЕ меняется по дате
  "trace_id": "uuid",
  "source": "avito", "source_id": "avito_chat_id",
  "client_name",  // → маппинг в DB: clients.name
  "phone", "telegram", "email",  // email опционален
  "inn", "company_name",
  "client_type", "tax_system", "has_employees", "employees_count",
  "need", "marketplace", "city",
  "source_url",  // ссылка на объявление Авито
  "qualification_summary", "estimated_price",
  "messages_count", "first_message_at", "last_message_at",
  "consent_given_at"  // ФЗ-152: время согласия на обработку ПДн
}
→ 201: {"client_id": 142, "status": "created"}
→ 200: {"client_id": 142, "status": "updated"}
```

### CRM → Авито-бот: Отправить сообщение клиенту

⚠️ Критически важно для Drip-кампании. CRM управляет статусами и решает КОГДА писать, но отправлять в Авито может только бот.

```
POST http://localhost:8001/api/v1/send-message
{
  "idempotency_key": "drip-{client_id}-step{N}-{date}",
  "avito_chat_id": "u2i-...",
  "text": "Текст сообщения",
  "trace_id": "uuid"
}
→ 200: {"message_id": 445, "delivered": true}
→ 403: {"error": "blocked_by_user"}  // Клиент заблокировал
```

При ответе 403 — CRM меняет статус на `lost_banned`, drip останавливается.

### CRM → Авито-бот: Обновить статус лида

⚠️ Критически важно: без этого бот продолжает AI-квалификацию для клиента, который уже подписал договор.

```
POST http://localhost:8001/api/v1/leads/{avito_chat_id}/status
{
  "ai_enabled": false,     // отключить AI для этого чата
  "crm_stage": "active",   // текущий статус в CRM (для логирования)
  "trace_id": "uuid"
}
→ 200: {"updated": true}
→ 404: {"error": "lead_not_found"}
```

**Когда вызывать:** CRM отправляет через свой outbox при переходе в `contract`, `payment`, `active`. Бот ставит `ai_enabled=0`, при новых сообщениях отвечает шаблоном: «Ваш бухгалтер {short_name} уже ведёт вашу компанию. Напишите ему напрямую: @{username}»

**Маппинг статусов bot→CRM:** bot.db `handoff` → CRM создаёт карточку с `pipeline_stage = new`. Дальнейшие статусы (`contacted`, `cp`, `contract`, `active`) — только в CRM.

### Healthcheck (оба сервиса)

```
GET /health
→ 200: {"service", "status", "version", "uptime_seconds", "db", "outbox_pending", "outbox_failed", "errors_last_hour"}
```

### CRM Internal API (для HTMX-дашборда)

```
GET  /api/v1/clients?pipeline_stage=new&page=1
GET  /api/v1/clients/{id}
PATCH /api/v1/clients/{id}  {"pipeline_stage": "contacted", "responsible_id": 3}
GET  /api/v1/tasks?employee_id=3&status=pending
POST /api/v1/tasks  {"client_id": 42, "type": "call", "due_at": "..."}
GET  /api/v1/employees/active  -- для Авито-бота (кэширование)
GET  /api/v1/stats/funnel  → {"new": 12, "contacted": 8, "cp": 5, "contract": 3, ...}
```

### .env переменные

**avito-bot/.env:**
```
AVITO_CLIENT_ID=, AVITO_CLIENT_SECRET=, AVITO_USER_ID=
OPENROUTER_API_KEY=, WHISPER_API_KEY=
DADATA_API_KEY=, DADATA_SECRET_KEY=
CRM_INTERNAL_KEY=
CRM_URL=http://localhost:8003
BOT_DB_PATH=data/bot.db
LOG_LEVEL=INFO
```

**crm-core/.env:**
```
AVITO_INTERNAL_KEY=
DADATA_API_KEY=, DADATA_SECRET_KEY=
TELEGRAM_BOT_TOKEN=, ADMIN_CHAT_ID=
CRM_DB_PATH=data/crm.db
AVITO_BOT_URL=http://localhost:8001
LOG_LEVEL=INFO
```

---

## 8. Порядок реализации Фазы 1

| Шаг | Задача | Результат |
|-----|--------|-----------|
| 1.0 | `/opt/mn/`, Linux-пользователи, shared/config/ | Инфраструктура |
| 1.1 | Заполнить 10 JSON-конфигов | Единый источник правды |
| 1.2 | Авито-бот: написать с нуля по FOUNDATION + CLAUDE.md | Сервис 1 работает |
| 1.2a | Скрипт миграции: если найдена старая БД — экспорт leads → import в новую | Данные сохранены |
| 1.3 | CRM-ядро: карточки + воронка + HTMX-дашборд | Сервис 3 работает |
| 1.3a | task_generator.py (cron 1-е число) | Авто-задачи |
| 1.3b | sla_monitor.py (cron 30 мин) | Контроль воронки |
| 1.3c | churn_detector.py (cron ежедневно) | Обнаружение ухода |
| 1.4 | Связать через outbox | Заявки в CRM |
| 1.4a | ⚠️ Зарегистрировать webhook URL в Авито API: `https://nikiforov-bots.ru/webhook/avito` | Бот получает сообщения |
| 1.5 | Healthcheck + бэкапы + cron + Nginx роутинг | Мониторинг |

**Код пишется с нуля.** Старый код (`/root/crm/`) удалён — был некачественный и небезопасный. Claude Code создаёт все модули по этому документу + CLAUDE.md в каждом сервисе. Промпт Елизаветы, логика квалификации, возражения — всё описано выше.

**Шаблоны и ресурсы:**

| Что | Расположение |
|-----|-------------|
| Шаблон договора (.docx) | /opt/mn/shared/templates/contract_template.docx |
| Логотип (.png) | /opt/mn/shared/templates/logo.png |
| JSON-конфиги (10 шт.) | /opt/mn/shared/config/ |

---

## 9. Работа с Claude Code

**Запуск:** `sudo -u mn-avito bash && cd /opt/mn/avito-bot` — Claude Code видит ТОЛЬКО этот сервис.

**CLAUDE.md** в каждом сервисе (60-100 строк). Шаблон:
```
# Что делает этот сервис
# Структура файлов
# Как запустить (dev / prod)
# Правила кода (стиль, типы, тесты)
# Критические файлы (не трогать без понимания)
# Известные баги
# Запрещено (DROP, DELETE, rm -rf, прямые вызовы другого сервиса)
```

**Команды:** `/deploy` (тесты → рестарт → healthcheck), `/check` (здоровье), `/review` (безопасность), `/test`.

**Handoff:** `.claude/handoff.md` — обновлять в конце каждой сессии. Формат: что сделано, что дальше, проблемы.

**Hooks:** PostToolUse → `validate.sh`, PreToolUse → блокировка DROP/DELETE/rm, Stop → уведомление в Telegram.

---

## 10. Финансовые ориентиры

- **LTV:** 36 мес × 15 000₽ = 540 000₽. **CAC допустим:** до 15 000₽
- **Нагрузка:** 20-25 клиентов на бухгалтера. Для 155 = 6-8 человек
- **Мотивация:** оклад 40k + 20% от чека. 25 клиентов × 15k = 115k₽
- **Если чек = 10 000₽:** LTV = 360k₽, ФОТ бухгалтера = 36% выручки (терпимо, аутсорс живёт до 45%)
- **Если чек = 12 000₽ (реалистичный сценарий):** выручка 155 × 12k = 1 860k₽, маржа ~56%. Бизнес стабилен, но CAC нужно держать до 10k₽
- **⚠️ Cashflow-яма:** При CAC 10k₽ × 100 клиентов = 1 000 000₽ расходов на рекламу ДО получения оплат. Нужен оборотный капитал ~1 млн₽
- **Инфраструктура:** ~2 000₽/мес (сервер 1k + OpenRouter ~$10 + Whisper ~$1.2)
