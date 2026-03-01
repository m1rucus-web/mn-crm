# Прогресс: Авито-бот (Сервис 1)
Последнее обновление: 2026-03-01

## Текущий шаг
➡️ Промпт 4 — venv + FastAPI-каркас для Авито-бота

## Чеклист Фазы 1

### 1.0 Инфраструктура (совместно с CRM, под root)
- [x] 1.0.1 Создать /opt/mn/ и поддиректории
- [x] 1.0.2 Создать Linux-пользователей mn-avito, mn-crm
- [x] 1.0.3 Настроить права (chmod 700, shared 755)
- [x] 1.0.4 Проверить 10 JSON-конфигов в shared/config/ (все OK)
- [ ] 1.0.5 Инициализировать venv для avito-bot ← СЛЕДУЮЩИЙ
- [ ] 1.0.6 Инициализировать venv для crm-core

### 1.1 База данных
- [ ] 1.1.1 Создать scripts/init_db.py
- [ ] 1.1.2 Создать bot.db со всеми таблицами (leads, messages, employees, topic_mapping, settings, outbox, ai_logs)
- [ ] 1.1.3 Проверить PRAGMA WAL + busy_timeout
- [ ] 1.1.4 Проверить все индексы

### 1.2 Ядро бота (без AI)
- [ ] 1.2.1 settings.py (pydantic-settings из .env)
- [ ] 1.2.2 db.py (SQLAlchemy async engine)
- [ ] 1.2.3 models.py (ORM-модели)
- [ ] 1.2.4 avito_client.py (из /root/crm/, адаптация на httpx)
- [ ] 1.2.5 rate_limiter.py (10/мин, 60/час, 300/день)
- [ ] 1.2.6 webhooks.py (POST /webhook/avito — 200 OK, сохранение)
- [ ] 1.2.7 Дебаунс 8 сек
- [ ] 1.2.8 Фильтр системных сообщений Авито
- [ ] 1.2.9 outbox_writer.py
- [ ] 1.2.10 outbox_worker.py (pending → CRM каждые 30 сек)
- [ ] 1.2.11 Echo-ответ (без AI)
- [ ] 1.2.12 health.py (GET /health)

### 1.2a Миграция старой БД
- [ ] 1.2a.1 Экспорт leads из /root/crm/ старой БД
- [ ] 1.2a.2 Schema diff + count(*)
- [ ] 1.2a.3 Импорт в новую bot.db

### 1.3 AI-интеграция
- [ ] 1.3.1 anonymize.py (ФИО, ИНН, телефоны → плейсхолдеры)
- [ ] 1.3.2 ai_client.py (OpenRouter, gemini-2.5-flash + fallback)
- [ ] 1.3.3 prompt.py (промпт Елизаветы + context builder)
- [ ] 1.3.4 post_check.py (regex: цена < 7000, >1 вопрос)
- [ ] 1.3.5 Интеграция в webhook pipeline
- [ ] 1.3.6 ai_logs — логирование AI-вызовов

### 1.4 Связка с CRM через outbox
- [ ] 1.4.1 E2E: webhook → outbox → CRM получил лида
- [ ] 1.4.2 E2E: AI-квалификация → handoff → CRM UPSERT
- [ ] 1.4.3 send_message.py (POST /api/v1/send-message от CRM)
- [ ] 1.4.4 lead_status.py (POST /api/v1/leads/{chat_id}/status от CRM)

### 1.5 Эксплуатация
- [ ] 1.5.1 backup.sh + cron
- [ ] 1.5.2 Systemd-юнит mn-avito-bot.service
- [ ] 1.5.3 10 тестовых диалогов (дубли, порядок, ретраи)

## Решения (что и почему выбрали)
<!-- Заполняется по ходу работы -->
