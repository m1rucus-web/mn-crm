# Прогресс: CRM-ядро (Сервис 3)
Последнее обновление: 2026-03-01

## Текущий шаг
➡️ Промпт 5 — venv + FastAPI-каркас для CRM

## Чеклист Фазы 1

### 1.0 Инфраструктура (совместно с Авито-ботом, под root)
- [x] → см. avito-bot/progress.md (промпты 1-3 выполнены)

### 1.1 База данных
- [ ] 1.1.1 Создать scripts/init_db.py
- [ ] 1.1.2 Создать crm.db со всеми таблицами (clients, employees, history, tasks, onboarding_documents, processed_keys, outbox, drip_events)
- [ ] 1.1.3 Проверить PRAGMA WAL + busy_timeout
- [ ] 1.1.4 Проверить все индексы (включая UNIQUE на inn)
- [ ] 1.1.5 seed_test_data.py (тестовые данные для разработки)

### 1.2 Приём лидов (POST /api/v1/leads)
- [ ] 1.2.1 settings.py (pydantic-settings из .env)
- [ ] 1.2.2 db.py (SQLAlchemy async engine)
- [ ] 1.2.3 models.py (ORM-модели)
- [ ] 1.2.4 idempotency.py (проверка idempotency_key в processed_keys)
- [ ] 1.2.5 lead_merger.py (дедупликация по phone/inn → merge)
- [ ] 1.2.6 leads.py endpoint (X-Internal-Key, UPSERT, маппинг client_name→name)
- [ ] 1.2.7 Тесты: дубликат, битый payload, неверный ключ, merge по phone

### 1.3 Воронка и управление клиентами
- [ ] 1.3.1 pipeline.py (смена pipeline_stage + history + outbox→бот)
- [ ] 1.3.2 assignment.py (назначение бухгалтера, round-robin по нагрузке)
- [ ] 1.3.3 clients.py (GET/PATCH /api/v1/clients)
- [ ] 1.3.4 tasks.py (GET/POST /api/v1/tasks)
- [ ] 1.3.5 employees.py (GET /api/v1/employees/active)
- [ ] 1.3.6 stats.py (GET /api/v1/stats/funnel)
- [ ] 1.3.7 health.py (GET /health)

### 1.3a–c Автоматизация
- [ ] 1.3a task_generator.py (cron 1-е число: задачи по tax_calendar)
- [ ] 1.3b sla_monitor.py (cron 10 мин: new > 1ч → алерт в Telegram)
- [ ] 1.3c churn_detector.py (cron ежедневно: нет контактов 30+ дней)

### 1.4 HTMX-дашборд
- [ ] 1.4.1 web/routes.py (GET /crm/ — список лидов с фильтром по pipeline_stage)
- [ ] 1.4.2 templates/leads_list.html (таблица, HTMX-фильтры)
- [ ] 1.4.3 templates/client_card.html (карточка клиента)
- [ ] 1.4.4 templates/pipeline.html (канбан-воронка)

### 1.5 Outbox (CRM → Авито-бот)
- [ ] 1.5.1 outbox_writer.py
- [ ] 1.5.2 outbox_worker.py (pending → бот каждые 30 сек)
- [ ] 1.5.3 E2E: смена статуса → outbox → бот получил /leads/{chat_id}/status
- [ ] 1.5.4 Заглушка drip_scheduler.py (скелет, не активирован)

### 1.6 Эксплуатация
- [ ] 1.6.1 backup.sh + cron
- [ ] 1.6.2 Systemd-юнит mn-crm-core.service
- [ ] 1.6.3 Nginx конфиг (/crm/ → 8003, /crm/webhook/avito → 8001)
- [ ] 1.6.4 SSL проверка (certbot)
- [ ] 1.6.5 Финальная валидация: 10 тестовых диалогов E2E

## Решения (что и почему выбрали)
<!-- Заполняется по ходу работы -->
