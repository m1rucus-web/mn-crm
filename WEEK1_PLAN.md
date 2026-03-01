# WEEK1_PLAN.md — План реализации Фазы 1 (7 рабочих дней)

> Код пишется с нуля. Старый код удалён.
> SSL настроен. Домен резолвится. Договор и логотип готовы.

---

## День 1 (Пн) — Инфраструктура + БД

```bash
sudo su
```

**Промпт Claude Code:**
"Создай структуру /opt/mn/ по FOUNDATION.md: пользователи mn-avito/mn-crm, chmod 700, shared/config/ и shared/templates/ (chmod 755). Инициализируй два FastAPI-проекта с venv (Python 3.12). Создай bot.db и crm.db со ВСЕМИ таблицами из раздела 6 FOUNDATION (включая outbox с aggregate_key, drip_events, processed_keys). PRAGMA journal_mode=WAL, busy_timeout=5000."

**Вручную:** Скопировать JSON-конфиги в `/opt/mn/shared/config/`, договор и логотип в `/opt/mn/shared/templates/`. Заполнить .env в обоих сервисах.

**Результат:** структура, пользователи, конфиги, пустые БД с правильными схемами, оба сервиса стартуют с GET /health → 200.

---

## День 2 (Вт) — CRM: приём лидов + идемпотентность

```bash
sudo -u mn-crm bash
cd /opt/mn/crm-core
```

**Промпт:**
"Напиши POST /api/v1/leads по FOUNDATION раздел 7:
- Проверка X-Internal-Key (== AVITO_INTERNAL_KEY из .env)
- idempotency_key → processed_keys (дубль? вернуть предыдущий результат)
- Дедупликация: phone ИЛИ inn совпадает → merge существующего → 200 {status: merged}
- UPSERT по ON CONFLICT (source, source_id) → 201 created / 200 updated
- Маппинг: API client_name → DB name
- КАЖДОЕ создание → history запись
- Тесты: дубликат, битый payload, неверный ключ, merge по phone, merge по inn."

**Результат:** CRM стабильно принимает лидов, не дублирует, мержит.

---

## День 3 (Ср) — CRM: CRUD + дашборд + воронка

```bash
sudo -u mn-crm bash
```

**Промпт:**
"Добавь в CRM:
1. GET/PATCH /api/v1/clients, GET /api/v1/clients/{id} — CRUD
2. GET /api/v1/tasks, POST /api/v1/tasks
3. GET /api/v1/employees/active — для Авито-бота
4. GET /api/v1/stats/funnel → JSON со счётчиками по pipeline_stage
5. HTMX-дашборд на /crm/ (Jinja2): список клиентов с фильтром по pipeline_stage, карточка клиента, список задач
6. pipeline.py: при PATCH clients → запись в history (action=stage_change, details=JSON from/to)
7. При переходе в contract/payment/active → запись в outbox для уведомления бота"

**Результат:** CRM полностью функциональна через браузер, воронка работает.

---

## День 4 (Чт) — Авито-бот: webhook + сохранение

```bash
sudo -u mn-avito bash
cd /opt/mn/avito-bot
```

**Промпт:**
"Напиши Авито-бот с нуля по FOUNDATION раздел 4 + CLAUDE.md:
1. POST /webhook/avito — приём сообщений от Авито API. Return 200 сразу.
2. Сохранение в messages (bot.db), создание/обновление leads
3. Дебаунс 8 сек (asyncio delayed task)
4. Фильтр системных сообщений ('Сообщение удалено' и т.п.)
5. Ночной режим (22-08 МСК): шаблонный ответ из work_hours.json, НЕ AI
6. Rate limiter: 10/мин, 60/час, 300/день
7. Whitelist (только авторизованные user_id)
8. ПДн-оферта в первом сообщении → consent_given_at при ответе
9. POST /api/v1/send-message — приём команд от CRM (для drip)
10. POST /api/v1/leads/{chat_id}/status — обновление статуса от CRM
БЕЗ AI пока — echo-бот (отвечает шаблоном). AI завтра."

**Результат:** webhook работает, данные в bot.db, бот принимает команды от CRM.

---

## День 5 (Пт) — Авито-бот: AI + outbox + связка

```bash
sudo -u mn-avito bash
```

**Промпт:**
"Добавь в Авито-бот:
1. ai_client.py: OpenRouter (gemini-2.5-flash, fallback deepseek-v3.2). httpx timeout=15s. Semaphore(3).
2. prompt.py: промпт Елизаветы из FOUNDATION раздел 4. Context builder: подставляет данные лида.
3. anonymize_text(): regex замена ФИО, ИНН, телефонов → плейсхолдеры ПЕРЕД отправкой в AI
4. post_check.py: >1 вопрос → обрезка. Цена < 7000₽ → блокировка. Числительные прописью.
5. whisper.py: голосовые < 2мин → Whisper API. >2мин → обрезка. Fallback → просьба текстом.
6. dadata.py: ИНН (10/12 цифр) → DaData запрос + кэш. Обогащение контекста.
7. outbox_writer.py + outbox_worker.py: при handoff → outbox → POST localhost:8003/api/v1/leads
   Двухэтапно: первое сообщение → пустая карточка, handoff → UPSERT.
   ORDER BY id ASC, aggregate_key блокировка, backoff, X-Trace-Id.
8. Алерт в Telegram (ADMIN_CHAT_ID): при handoff → саммари + телефон
Тесты: E2E webhook → AI → outbox → crm.clients."

**Результат:** полная цепочка работает. Лид с Авито → AI-квалификация → CRM-карточка.

---

## День 6 (Пн неделя 2) — Ops + Nginx + мониторинг

```bash
sudo su
```

**Промпт:**
"Настрой production-окружение:
1. Скопируй systemd-юниты из /opt/mn/shared/ → /etc/systemd/system/, enable + start
2. Скопируй nginx.conf → /etc/nginx/sites-available/, symlink, nginx -t, reload
3. healthcheck.sh → /opt/mn/shared/, chmod +x
4. Cron: */5 healthcheck, */6h backup обоих БД, 03:00 WAL checkpoint (PASSIVE)
5. Создай /opt/mn/backups/ (chmod 700 root). Backup script: .backup() + integrity_check
6. 10 тестовых диалогов через Авито: проверить дубли, outbox ретраи, merge по phone, ночной режим"

**Вручную:** Зарегистрировать webhook URL `https://nikiforov-bots.ru/webhook/avito` в настройках Авито API.

**Результат:** production-ready. Автозапуск, мониторинг, бэкапы.

---

## День 7 (Вт неделя 2) — Drip + КП + SLA + боевой запуск

```bash
sudo -u mn-crm bash
```

**Промпт:**
"Добавь в CRM:
1. drip_scheduler.py: проверка drip_next_at каждые 30 мин. Отправка через outbox → POST /api/v1/send-message. Логирование в drip_events.
2. При ответе клиента на drip → drip_active=0, pipeline_stage=contacted, задача бухгалтеру.
3. 403 от бота → lost_banned, drip стоп.
4. cp_generator.py: docxtpl + contract_template.docx + logo.png → PDF. POST /leads/{id}/generate-cp.
5. sla_monitor.py (cron 10 мин): new > 1ч → алерт. КП > 48ч → задача.
6. task_generator.py: по tax_calendar.json → задачи на 1-е число.
7. churn_detector.py: нет контактов 30+ дней → задача."

**Результат:** Полная Фаза 1 работает. Можно принимать реальных клиентов.

---

## Чеклист запуска (после дня 7)

- [ ] Webhook зарегистрирован в Авито
- [ ] .env заполнены реальными ключами (Авито, OpenRouter, Whisper, DaData, Telegram)
- [ ] Internal keys сгенерированы (`openssl rand -hex 32`)
- [ ] Договор и логотип в /opt/mn/shared/templates/
- [ ] JSON-конфиги с реальными данными (особенно employees, pricelist, company)
- [ ] Systemd enable + start обоих сервисов
- [ ] Nginx reload, HTTPS проверен
- [ ] Cron настроен (healthcheck, backup, WAL)
- [ ] Тестовый диалог в Авито → карточка в CRM → алерт в Telegram
- [ ] Бухгалтерам показан дашборд, объяснена воронка
