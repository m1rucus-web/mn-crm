#!/usr/bin/env bash
# CI-валидация проекта «Метод Никифорова»
# Выход exit 1 при любой неудаче.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAILED=0

fail() {
    echo "FAIL: $1"
    FAILED=1
}

pass() {
    echo "PASS: $1"
}

# ─── 1. Утечка секретов: .env файлы не должны быть в git ───
echo "=== Проверка 1: утечка секретов ==="
LEAKED=$(git -C "$REPO_ROOT" ls-files | grep -E '\.env$' || true)
if [ -n "$LEAKED" ]; then
    fail "Файлы .env в git: $LEAKED"
else
    pass "Файлы .env не в git"
fi

# ─── 2. Схема bot.db: 7 таблиц ───
echo ""
echo "=== Проверка 2: схема bot.db (7 таблиц) ==="
BOT_DB="/tmp/ci_test_bot.db"
rm -f "$BOT_DB" "$BOT_DB-wal" "$BOT_DB-shm"

# Подменяем путь к БД через переменную окружения — init_db.py использует hardcoded path,
# поэтому запускаем через python с патчем
python3 -c "
import sys, sqlite3
sys.path.insert(0, '$REPO_ROOT/avito-bot/scripts')
import init_db
init_db.DB_PATH = __import__('pathlib').Path('$BOT_DB')
init_db.main()
" > /dev/null 2>&1

BOT_TABLES=$(sqlite3 "$BOT_DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
if [ "$BOT_TABLES" -eq 7 ]; then
    pass "bot.db: $BOT_TABLES таблиц"
else
    fail "bot.db: ожидалось 7 таблиц, найдено $BOT_TABLES"
fi
rm -f "$BOT_DB" "$BOT_DB-wal" "$BOT_DB-shm"

# ─── 3. Схема crm.db: 8 таблиц ───
echo ""
echo "=== Проверка 3: схема crm.db (8 таблиц) ==="
CRM_DB="/tmp/ci_test_crm.db"
rm -f "$CRM_DB" "$CRM_DB-wal" "$CRM_DB-shm"

python3 -c "
import sys, sqlite3
sys.path.insert(0, '$REPO_ROOT/crm-core/scripts')
import init_db
init_db.DB_PATH = __import__('pathlib').Path('$CRM_DB')
init_db.main()
" > /dev/null 2>&1

CRM_TABLES=$(sqlite3 "$CRM_DB" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
if [ "$CRM_TABLES" -eq 8 ]; then
    pass "crm.db: $CRM_TABLES таблиц"
else
    fail "crm.db: ожидалось 8 таблиц, найдено $CRM_TABLES"
fi
rm -f "$CRM_DB" "$CRM_DB-wal" "$CRM_DB-shm"

# ─── 4. Компиляция: py_compile для всех .py ───
echo ""
echo "=== Проверка 4: компиляция Python ==="
COMPILE_FAIL=0
while IFS= read -r pyfile; do
    if ! python3 -m py_compile "$pyfile" 2>/dev/null; then
        fail "py_compile не прошёл: $pyfile"
        COMPILE_FAIL=1
    fi
done < <(find "$REPO_ROOT/avito-bot/src" "$REPO_ROOT/avito-bot/scripts" \
              "$REPO_ROOT/crm-core/src" "$REPO_ROOT/crm-core/scripts" \
              -name '*.py' -type f 2>/dev/null)

if [ "$COMPILE_FAIL" -eq 0 ]; then
    pass "Все .py файлы компилируются"
fi

# ─── 5. Полнота .env.example ───
echo ""
echo "=== Проверка 5: полнота .env.example ==="

check_env_example() {
    local service="$1"
    local settings_file="$REPO_ROOT/$service/src/settings.py"
    local env_example="$REPO_ROOT/$service/.env.example"

    if [ ! -f "$settings_file" ]; then
        fail "$service: settings.py не найден"
        return
    fi
    if [ ! -f "$env_example" ]; then
        fail "$service: .env.example не найден"
        return
    fi

    # Извлекаем имена полей из settings.py (snake_case) → UPPER_CASE
    SETTINGS_KEYS=$(grep -oP '^\s+(\w+)\s*:\s*\w+' "$settings_file" \
        | sed 's/^\s*//' | cut -d: -f1 \
        | grep -v '^model_config$' \
        | tr '[:lower:]' '[:upper:]' | sort)

    # Извлекаем ключи из .env.example
    ENV_KEYS=$(grep -oP '^[A-Z_]+' "$env_example" | sort)

    MISSING=$(comm -23 <(echo "$SETTINGS_KEYS") <(echo "$ENV_KEYS"))
    if [ -n "$MISSING" ]; then
        fail "$service: в .env.example не хватает: $MISSING"
    else
        pass "$service: .env.example полный"
    fi
}

check_env_example "avito-bot"
check_env_example "crm-core"

# ─── 6. Динамическая проверка /health ───
echo ""
echo "=== Проверка 6: /health эндпоинт ==="

# Убиваем фоновые серверы при выходе
cleanup_servers() {
    kill %1 %2 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup_servers EXIT

# Запускаем оба сервиса на непродовых портах
cd "$REPO_ROOT/avito-bot" && .venv/bin/uvicorn src.main:app --port 18001 &>/dev/null &
cd "$REPO_ROOT/crm-core" && .venv/bin/uvicorn src.main:app --port 18003 &>/dev/null &
sleep 3

HEALTH_EXPECTED='service,status,version,uptime_seconds,db,outbox_pending,outbox_failed,errors_last_hour'

check_health() {
    local name="$1"
    local port="$2"
    local response
    response=$(curl -sf "http://127.0.0.1:$port/health" 2>/dev/null) || {
        fail "$name: /health не отвечает на порту $port"
        return
    }
    local missing
    missing=$(echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
expected = {'service','status','version','uptime_seconds','db','outbox_pending','outbox_failed','errors_last_hour'}
missing = expected - set(d.keys())
if missing:
    print(f'не хватает: {missing}')
") || {
        fail "$name: /health вернул невалидный JSON"
        return
    }
    if [ -n "$missing" ]; then
        fail "$name: /health $missing"
    else
        pass "$name: /health OK (все 8 полей)"
    fi
}

check_health "avito-bot" 18001
check_health "crm-core" 18003

# Останавливаем серверы
cleanup_servers
trap - EXIT

# ─── Итог ───
echo ""
echo "=============================="
if [ "$FAILED" -eq 0 ]; then
    echo "CI PASS: все проверки пройдены"
    exit 0
else
    echo "CI FAIL: есть ошибки выше"
    exit 1
fi
