"""Инициализация bot.db — 7 таблиц из FOUNDATION.md v4.9 раздел 6."""

import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "bot.db"


def backup_if_exists() -> None:
    if DB_PATH.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = DB_PATH.with_name(f"bot.db.bak.{ts}")
        shutil.copy(DB_PATH, backup)
        print(f"Бэкап: {backup}")


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avito_chat_id TEXT UNIQUE NOT NULL,
            client_name TEXT, phone TEXT, telegram TEXT, email TEXT,
            inn TEXT, company_name TEXT, client_type TEXT, tax_system TEXT,
            has_employees INTEGER DEFAULT 0, employees_count INTEGER DEFAULT 0,
            need TEXT, marketplace TEXT, city TEXT,
            status TEXT DEFAULT 'new',
            ai_enabled INTEGER DEFAULT 1,
            qualification_summary TEXT, estimated_price TEXT,
            avito_url TEXT, source_ad TEXT,
            consent_given_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            avito_msg_id TEXT UNIQUE NOT NULL,
            lead_id INTEGER REFERENCES leads(id),
            direction TEXT CHECK(direction IN ('in','out')),
            content TEXT, msg_type TEXT DEFAULT 'text',
            is_ai_response INTEGER DEFAULT 0, ai_model TEXT,
            ai_tokens_in INTEGER,
            ai_tokens_out INTEGER,
            ai_cost_usd REAL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL, short_name TEXT, username TEXT,
            role TEXT DEFAULT 'accountant', is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS topic_mapping (
            avito_chat_id TEXT PRIMARY KEY,
            telegram_topic_id INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
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

        CREATE TABLE IF NOT EXISTS ai_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER REFERENCES leads(id),
            model TEXT NOT NULL,
            prompt_hash TEXT,
            tokens_in INTEGER DEFAULT 0,
            tokens_out INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0,
            response_summary TEXT,
            is_fallback INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)


def create_indexes(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_outbox_pending
            ON outbox(status) WHERE status='pending';
        CREATE INDEX IF NOT EXISTS idx_outbox_aggregate
            ON outbox(aggregate_key, id) WHERE status IN ('pending','failed');
        CREATE INDEX IF NOT EXISTS idx_messages_lead
            ON messages(lead_id);
        CREATE INDEX IF NOT EXISTS idx_leads_status
            ON leads(status);
        CREATE INDEX IF NOT EXISTS idx_leads_created
            ON leads(created_at);
        CREATE INDEX IF NOT EXISTS idx_ai_logs_lead
            ON ai_logs(lead_id);
        CREATE INDEX IF NOT EXISTS idx_ai_logs_date
            ON ai_logs(created_at);
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

        # Проверка
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        ]
        print(f"Таблицы ({len(tables)}): {', '.join(tables)}")

        journal = conn.execute("PRAGMA journal_mode;").fetchone()[0]
        print(f"journal_mode: {journal}")
    finally:
        conn.close()

    print("init_db.py завершён успешно.")


if __name__ == "__main__":
    main()
