"""Инициализация crm.db — 8 таблиц из FOUNDATION.md v4.9 раздел 6."""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "crm.db"


def backup_if_exists() -> None:
    if DB_PATH.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = DB_PATH.with_name(f"crm.db.bak.{ts}")
        shutil.copy(DB_PATH, backup)
        print(f"Бэкап: {backup}")


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL, source_id TEXT, idempotency_key TEXT UNIQUE,
            name TEXT,
            phone TEXT, telegram TEXT, email TEXT,
            inn TEXT, company_name TEXT, client_type TEXT, tax_system TEXT,
            has_employees INTEGER DEFAULT 0, employees_count INTEGER DEFAULT 0,
            need TEXT, marketplace TEXT, city TEXT,
            source_url TEXT,
            pipeline_stage TEXT DEFAULT 'new',
            responsible_id INTEGER REFERENCES employees(id),
            qualification_summary TEXT, estimated_price TEXT, monthly_price INTEGER, notes TEXT,
            is_waiting_docs INTEGER DEFAULT 0,
            is_vip_newcomer INTEGER DEFAULT 0,
            last_client_message_at TEXT,
            messages_count INTEGER DEFAULT 0,
            first_message_at TEXT,
            source_last_message_at TEXT,
            drip_campaign_step INTEGER DEFAULT 0,
            drip_next_at TEXT,
            drip_active INTEGER DEFAULT 0,
            consent_given_at TEXT,
            deleted_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(source, source_id)
        );

        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL, short_name TEXT,
            username TEXT,
            role TEXT DEFAULT 'accountant', max_clients INTEGER DEFAULT 50,
            status TEXT DEFAULT 'active',
            substitute_id INTEGER REFERENCES employees(id),
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER REFERENCES clients(id),
            action TEXT NOT NULL, details TEXT,
            employee_id INTEGER, auto INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER REFERENCES clients(id),
            employee_id INTEGER, type TEXT NOT NULL,
            description TEXT, due_at TEXT NOT NULL,
            completed_at TEXT, status TEXT DEFAULT 'pending',
            deleted_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS onboarding_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER REFERENCES clients(id),
            doc_type TEXT NOT NULL, doc_name TEXT NOT NULL,
            is_received INTEGER DEFAULT 0, received_at TEXT, last_reminder_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS processed_keys (
            idempotency_key TEXT PRIMARY KEY, response TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_url TEXT NOT NULL, method TEXT DEFAULT 'POST',
            payload TEXT NOT NULL, idempotency_key TEXT UNIQUE, trace_id TEXT,
            aggregate_key TEXT,
            status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 10, next_retry_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            sent_at TEXT, response_code INTEGER, error TEXT
        );

        CREATE TABLE IF NOT EXISTS drip_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            step INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_at TEXT DEFAULT (datetime('now')),
            meta TEXT
        );
    """)


def create_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_clients_responsible
            ON clients(responsible_id) WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_clients_pipeline
            ON clients(pipeline_stage) WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_clients_inn
            ON clients(inn) WHERE deleted_at IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_clients_inn_unique
            ON clients(inn) WHERE inn IS NOT NULL AND deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_history_client
            ON history(client_id);
        CREATE INDEX IF NOT EXISTS idx_history_action
            ON history(action) WHERE action='stage_change';
        CREATE INDEX IF NOT EXISTS idx_tasks_client
            ON tasks(client_id) WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_tasks_employee_due
            ON tasks(employee_id, due_at) WHERE status='pending';
        CREATE INDEX IF NOT EXISTS idx_onboarding_client
            ON onboarding_documents(client_id) WHERE is_received=0;
        CREATE INDEX IF NOT EXISTS idx_outbox_pending_crm
            ON outbox(status) WHERE status='pending';
        CREATE INDEX IF NOT EXISTS idx_outbox_aggregate_crm
            ON outbox(aggregate_key, id) WHERE status IN ('pending','failed');
        CREATE INDEX IF NOT EXISTS idx_drip_events_client_step
            ON drip_events(client_id, step);
    """)


def set_pragmas(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    backup_if_exists()

    print(f"Создаю БД: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    try:
        create_tables(conn)
        create_indexes(conn)
        set_pragmas(conn)
        conn.commit()
        print("Таблицы и индексы созданы.")

        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        print(f"Таблицы ({len(tables)}): {', '.join(tables)}")

        indexes = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name"
            ).fetchall()
        ]
        print(f"Индексы ({len(indexes)}): {', '.join(indexes)}")

        journal = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        print(f"journal_mode: {journal}")
    finally:
        conn.close()

    print("init_db.py завершён успешно.")


if __name__ == "__main__":
    main()
