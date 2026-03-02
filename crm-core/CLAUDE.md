# CLAUDE.md — CRM-ядро (Сервис 3)

## Что это
CRM для бухгалтерской компании. Принимает лидов из Авито-бота через API → карточки → воронка → задачи → назначение бухгалтеров. HTMX-дашборд для работы в браузере. Управляет drip-кампанией (решает КОГДА слать, бот решает КАК доставить).

## Стек
Python 3.12, FastAPI (порт 8003), SQLite WAL (data/crm.db), SQLAlchemy async, httpx, loguru, APScheduler, Jinja2 + HTMX, pydantic-settings.

## Структура
```
/opt/mn/crm-core/
├── CLAUDE.md              ← Этот файл
├── progress.md            ← Живой чеклист (где я сейчас)
├── worklog.md             ← Полный лог действий (что делал, когда, результат)
├── src/
│   ├── main.py              # FastAPI app + lifespan
│   ├── settings.py          # pydantic-settings из .env
│   ├── db.py                # SQLAlchemy async engine + sessions
│   ├── models.py            # ORM: clients, employees, tasks, history, onboarding_documents, processed_keys, drip_events, outbox
│   ├── api/
│   │   ├── leads.py         # POST /api/v1/leads — приём из Авито-бота
│   │   ├── clients.py       # GET/PATCH /api/v1/clients — CRUD
│   │   ├── tasks.py         # GET/POST /api/v1/tasks
│   │   ├── employees.py     # GET /api/v1/employees/active
│   │   └── stats.py         # GET /api/v1/stats/funnel
│   ├── web/
│   │   ├── routes.py        # HTMX-дашборд: /crm/
│   │   └── templates/       # Jinja2: leads_list, client_card, pipeline, tasks
│   ├── services/
│   │   ├── idempotency.py   # processed_keys: проверка idempotency_key
│   │   ├── lead_merger.py   # Дедупликация по phone/inn → merge
│   │   ├── pipeline.py      # Смена pipeline_stage + запись в history + outbox→бот
│   │   ├── assignment.py    # Назначение бухгалтера (round-robin, нагрузка)
│   │   ├── cp_generator.py  # PDF с логотипом (docxtpl)
│   │   ├── dadata.py        # Проверка контрагентов
│   │   └── outbox_writer.py # Запись в outbox (для бота и Telegram)
│   ├── workers/
│   │   ├── outbox_worker.py # Фоновая отправка pending → Авито-бот (каждые 30 сек)
│   │   ├── drip_scheduler.py  # Drip-кампания: проверка drip_next_at, отправка через outbox
│   │   ├── task_generator.py  # Cron 1-е число: задачи по tax_calendar
│   │   ├── sla_monitor.py     # Cron 10 мин: new > 1ч → алерт
│   │   └── churn_detector.py  # Cron ежедневно: нет контактов 30+ дней
├── scripts/
│   ├── init_db.py
│   ├── backup.sh
│   └── seed_test_data.py    # Тестовые данные для разработки
├── tests/
├── data/crm.db
└── .env
```

## Конфиги
Читать из `/opt/mn/shared/config/` (read-only):
- `pricelist.json` — цены (для генерации КП)
- `company.json` — реквизиты (для договоров и КП)
- `employees.json` — начальный импорт (потом мастер — crm.db)
- `tax_calendar.json` — сроки отчётности (для task_generator)
- `templates.json` — шаблоны сообщений (drip, напоминания)
- `services_catalog.json` — каталог услуг (для КП)

## .env переменные
```
AVITO_INTERNAL_KEY=
TELEGRAM_BOT_TOKEN=
ADMIN_CHAT_ID=
DADATA_API_KEY=
DADATA_SECRET_KEY=
CRM_DB_PATH=data/crm.db
AVITO_BOT_URL=http://localhost:8001
LOG_LEVEL=INFO
APP_VERSION=0.1.0
```

## Как запускать
```bash
sudo -u mn-crm bash
cd /opt/mn/crm-core
source .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8003
```
Systemd: `mn-crm-core.service`

## Ключевые правила

### Воронка (pipeline_stage)
```
new → contacted → cp → contract → payment → onboarding → active
                                                        → lost_thinking / lost_silent / lost_competitor / lost_banned / lost_final
```
- КАЖДОЕ изменение → запись в `history` (action='stage_change', details=JSON from/to)
- При переходе в contract/payment/active → outbox → POST /api/v1/leads/{chat_id}/status на боте (отключает AI)

### Приём лидов (POST /api/v1/leads)
1. Проверить `X-Internal-Key` (== AVITO_INTERNAL_KEY из .env)
2. Проверить `idempotency_key` в `processed_keys` → дубль? вернуть предыдущий результат
3. **Дедупликация:** если phone ИЛИ inn совпадает → обновить существующего → `{"status": "merged"}`
4. UPSERT по `ON CONFLICT (source, source_id)` → 201 (created) / 200 (updated)
5. Маппинг: API `client_name` → DB `name`

### Drip-кампания
- Поля `drip_active`, `drip_campaign_step`, `drip_next_at` — в clients
- Триггер: 3 дня после `last_client_message_at`
- Отправка: через outbox → POST /api/v1/send-message на боте
- Ответ клиента → `drip_active=0`, `pipeline_stage=contacted`, задача бухгалтеру
- 403 от бота → `lost_banned`, drip стоп
- 7-й шаг без ответа → `lost_final`
- Логировать в `drip_events`

### SLA
- new > 1 час → алерт в Telegram
- КП > 48 часов → задача бухгалтеру
- Нагрузка > 20 клиентов на бухгалтера → задача «начать найм»
- Нагрузка > 23 → drip на паузу

---

## ⚡ Протокол работы (ОБЯЗАТЕЛЬНО)

### При старте каждой сессии:
0. **Проверить git:** `cd /opt/mn && git add -A && git diff --cached --quiet || git commit -m 'fix: незакоммиченные файлы' && git diff origin/main --quiet || git push`
1. **ПЕРВЫМ ДЕЛОМ** прочитай `progress.md` и `worklog.md`
2. Если в worklog.md есть запись «НАЧИНАЮ» без парного «ГОТОВО» — это незавершённый шаг. Проверь его состояние, доложи, потом продолжай.
3. Прочитай текущий шаг в progress.md → это твоя задача.

### Перед КАЖДЫМ шагом:
1. Запиши в `worklog.md`:
   ```
   ## ГГГГ-ММ-ДД ЧЧ:ММ — НАЧИНАЮ: [название шага]
   Что делаю: [описание]
   Изменения: [какие файлы создаю/меняю]
   Зависимости: [от чего зависит]
   Риски: [что может пойти не так]
   ```
2. Обнови `progress.md`: поставь `← В РАБОТЕ` на текущий подшаг.

### После КАЖДОГО шага:
1. Запиши в `worklog.md`:
   ```
   ## ГГГГ-ММ-ДД ЧЧ:ММ — ГОТОВО: [название шага] ✅
   Результат: [что получилось]
   Коммит: [хеш] "[сообщение коммита]"
   Следующий: [какой шаг дальше]
   ```
2. Обнови `progress.md`: поставь `[x]` и сдвинь `← СЛЕДУЮЩИЙ`.
3. Сделай `git commit` с осмысленным сообщением на русском.

### При обрыве связи (восстановление):
1. Прочитай `progress.md` → `worklog.md` → `git log --oneline -5` → `git diff`
2. Запиши в worklog: «ВОССТАНОВЛЕНИЕ после обрыва. Состояние: [что нашёл]»
3. Доложи статус, жди инструкций.

---

## ПРАВИЛО: worklog после каждого промпта
После КАЖДОГО выполненного промпта — обязательно:
1. Добавить запись в `worklog.md` (новые записи сверху)
2. `git add worklog.md progress.md`
3. `git commit` с осмысленным сообщением
4. `git push`

---

## ЗАПРЕЩЕНО
- Прямой доступ к bot.db
- DELETE в SQLite для бизнес-сущностей (clients, tasks) — только soft delete
- Docker, Kubernetes, GraphQL, микрофронтенды
- Мессенджер-хаб, Аналитика, Биллинг — это Фазы 2-3
- Хранение API-ключей в коде (только .env)
- Пропускать записи в worklog.md и progress.md

## Логирование
- После КАЖДОГО шага из progress.md — обновить worklog.md (что сделал, результат)
- git add + commit после каждого шага
- git push — после каждого ПРОМПТА (не после каждого шага)
- Формат записи: "### Шаг X.X.X — название" + что сделал + результат

## Обязательные проверки после каждого промпта

0. Перед git push — запусти `bash /opt/mn/scripts/ci_validate.sh`. Если FAIL — исправь до зелёного. Коммитить с красным CI запрещено.

1. Обнови /opt/mn/STATE.md — секции 'Последнее обновление', 'Где мы', 'Что дальше', 'Открытые проблемы'.

2. Сверить .env.example с .env:
   diff <(grep -oP '^[A-Z_]+' .env.example | sort) <(grep -oP '^[A-Z_]+' .env | sort)
   Если diff не пустой — добавить недостающие переменные в .env.

3. Проверить что ВСЕ файлы из промпта созданы:
   Перечитай промпт, пройди по каждому "Создай файл X" — проверь test -f X.

4. В worklog записать:
   "Проверка полноты: ОК" или "Проверка полноты: добавил X, Y, Z"

5. Если промпт создаёт таблицы — проверить .tables и сверить с FOUNDATION.md.

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

## Запрещено (нарушение = баг)

- НЕ удалять файлы без явной команды Юрия
- НЕ менять .env (только .env.example — .env трогает только Юрий)
- НЕ менять структуру БД без сверки с FOUNDATION.md раздел 6
- НЕ запускать планировщики/cron автоматически (урок: 96 спам-сообщений)
- НЕ делать DROP TABLE, DELETE FROM, rm -rf

## Перед написанием кода

1. Прочитай /opt/mn/STATE.md — пойми где проект сейчас и что делаем.
2. Прочитай FOUNDATION.md — найди раздел про то что делаешь
3. Прочитай progress.md — найди текущий шаг
4. Проверь что на сервере сейчас (ls, test -f, .tables) — не предполагай

## Если что-то сломалось

1. НЕ чини молча — запиши в worklog что сломалось и почему
2. Если сломал чужой сервис — СТОП, сообщи Юрию
3. Откати через git: git diff → git checkout -- файл

## Handoff

Обновлять `.claude/handoff.md` в конце каждой сессии.
