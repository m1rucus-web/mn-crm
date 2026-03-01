# CLAUDE.md — Авито-бот (Сервис 1)

## Что это
AI-бот для Авито. Принимает сообщения от клиентов → ведёт диалог (промпт Елизаветы) → квалифицирует → берёт телефон → передаёт в CRM через outbox. Также принимает команды от CRM (отправить сообщение клиенту, обновить статус лида).

## Стек
Python 3.12, FastAPI (порт 8001), SQLite WAL (data/bot.db), SQLAlchemy async, httpx, loguru, APScheduler, pydantic-settings.

## Структура
```
/opt/mn/avito-bot/
├── CLAUDE.md              ← Этот файл
├── progress.md            ← Живой чеклист (где я сейчас)
├── worklog.md             ← Полный лог действий (что делал, когда, результат)
├── src/
│   ├── main.py              # FastAPI app + lifespan
│   ├── settings.py          # pydantic-settings из .env
│   ├── db.py                # SQLAlchemy async engine + sessions
│   ├── models.py            # ORM: leads, messages, employees, topic_mapping, outbox
│   ├── api/
│   │   ├── webhooks.py      # POST /webhook/avito — входящие от Авито
│   │   ├── send_message.py  # POST /api/v1/send-message — исходящие от CRM
│   │   └── lead_status.py   # POST /api/v1/leads/{chat_id}/status — обновление от CRM
│   ├── services/
│   │   ├── avito_client.py  # Авито API (отправка, получение, rate limits)
│   │   ├── ai_client.py     # OpenRouter (gemini-2.5-flash + fallback deepseek-v3.2)
│   │   ├── prompt.py        # Промпт Елизаветы + context builder
│   │   ├── anonymize.py     # anonymize_text() — ФИО, ИНН, телефоны → плейсхолдеры
│   │   ├── post_check.py    # Regex: цена < 7000, >1 вопрос, числительные прописью
│   │   ├── whisper.py       # Голосовые → текст (Whisper API, <2мин, fallback)
│   │   ├── dadata.py        # DaData: ИНН → реквизиты (с кэшем)
│   │   ├── rate_limiter.py  # 10/мин, 60/час, 300/день
│   │   └── outbox_writer.py # Запись событий в outbox
│   └── workers/
│       └── outbox_worker.py # Фоновая отправка pending → CRM (каждые 30 сек)
├── scripts/
│   ├── init_db.py           # Создание таблиц
│   └── backup.sh            # .backup() + integrity_check
├── tests/
├── data/bot.db
└── .env
```

## Конфиги
Читать из `/opt/mn/shared/config/` (read-only):
- `pricelist.json` — цены (для промпта)
- `ai_models.json` — модели, таймауты, семафор
- `brand_voice.json` — тон, max_questions: 1
- `objections.json` — ответы на возражения
- `employees.json` — бухгалтеры (кэшировать)
- `work_hours.json` — ночной режим 22-08 МСК

## .env переменные
```
AVITO_CLIENT_ID=
AVITO_CLIENT_SECRET=
AVITO_USER_ID=
OPENROUTER_API_KEY=
WHISPER_API_KEY=
DADATA_API_KEY=
DADATA_SECRET_KEY=
CRM_INTERNAL_KEY=
CRM_URL=http://localhost:8003
BOT_DB_PATH=data/bot.db
LOG_LEVEL=INFO
```

## Как запускать
```bash
sudo -u mn-avito bash
cd /opt/mn/avito-bot
source .venv/bin/activate
uvicorn src.main:app --host 127.0.0.1 --port 8001
```
Systemd: `mn-avito-bot.service`

## Ключевые правила
1. **Дебаунс 8 сек** — не отвечать на каждое сообщение, ждать финальное
2. **AI async** — return 200 OK сразу, AI через asyncio.create_task()
3. **anonymize_text()** — ФИО, ИНН, телефоны НЕ уходят в OpenRouter
4. **Пост-проверка** — regex: цена < 7000₽ → блокировка; >1 вопрос → обрезка
5. **Outbox** — все данные в CRM только через outbox, НИКОГДА напрямую в crm.db
6. **Таймауты** — httpx: AI=15s, Whisper=30s. При timeout → шаблонный ответ + retry
7. **Semaphore(3)** — не более 3 параллельных AI-вызовов
8. **WAL** — PRAGMA journal_mode=WAL; busy_timeout=5000; при init

## Двухэтапная передача лида в CRM
1. Первое сообщение клиента → outbox → CRM создаёт пустую карточку (имя + chat_id)
2. Handoff (получен телефон) → outbox → CRM UPSERT с полной квалификацией

## Статусы lead
- `new` — первое сообщение получено
- `ai_active` — диалог идёт
- `handoff` — передан в CRM

Все `lost_*` статусы — ТОЛЬКО в CRM. Бот их не знает и не ставит.

---

## ⚡ Протокол работы (ОБЯЗАТЕЛЬНО)

### При старте каждой сессии:
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
- Прямой доступ к crm.db
- Хранение API-ключей в коде (только .env)
- Отправка ПДн (ФИО, ИНН, телефон) в AI без anonymize
- DELETE в SQLite (только soft delete через статусы)
- Docker, Kubernetes, GraphQL, микрофронтенды
- Пропускать записи в worklog.md и progress.md

## Логирование
- После КАЖДОГО шага из progress.md — обновить worklog.md (что сделал, результат)
- git add + commit после каждого шага
- git push — после каждого ПРОМПТА (не после каждого шага)
- Формат записи: "### Шаг X.X.X — название" + что сделал + результат

## Обязательные проверки после каждого промпта

1. Сверить .env.example с .env:
   diff <(grep -oP '^[A-Z_]+' .env.example | sort) <(grep -oP '^[A-Z_]+' .env | sort)
   Если diff не пустой — добавить недостающие переменные в .env.

2. Проверить что ВСЕ файлы из промпта созданы:
   Перечитай промпт, пройди по каждому "Создай файл X" — проверь test -f X.

3. В worklog записать:
   "Проверка полноты: ОК" или "Проверка полноты: добавил X, Y, Z"

4. Если промпт создаёт таблицы — проверить .tables и сверить с FOUNDATION.md.

## Запрещено (нарушение = баг)

- НЕ удалять файлы без явной команды Юрия
- НЕ менять .env (только .env.example — .env трогает только Юрий)
- НЕ менять структуру БД без сверки с FOUNDATION.md раздел 6
- НЕ запускать планировщики/cron автоматически (урок: 96 спам-сообщений)
- НЕ делать DROP TABLE, DELETE FROM, rm -rf

## Перед написанием кода

1. Прочитай FOUNDATION.md — найди раздел про то что делаешь
2. Прочитай progress.md — найди текущий шаг
3. Проверь что на сервере сейчас (ls, test -f, .tables) — не предполагай

## Если что-то сломалось

1. НЕ чини молча — запиши в worklog что сломалось и почему
2. Если сломал чужой сервис — СТОП, сообщи Юрию
3. Откати через git: git diff → git checkout -- файл
