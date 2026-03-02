"""10 тестов POST /api/v1/leads — идемпотентность, дедупликация, merge, UPSERT."""

import os
import sqlite3
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Подставляем тестовую БД ДО импорта приложения
_tmp_dir = tempfile.mkdtemp()
_test_db = os.path.join(_tmp_dir, "test_crm.db")
os.environ["CRM_DB_PATH"] = _test_db

from src.main import app  # noqa: E402

INTERNAL_KEY = "068c700eb67182855a68d3dfe78079cb52e70dd75d9c83ad865aecc7c4905d85"
HEADERS = {"Content-Type": "application/json", "X-Internal-Key": INTERNAL_KEY}


def _init_test_db():
    """Создаём таблицы в тестовой БД через init_db.py логику."""
    conn = sqlite3.connect(_test_db)
    # Копируем CREATE TABLE из init_db.py
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

        PRAGMA journal_mode=WAL;
        PRAGMA busy_timeout=5000;
    """)
    conn.commit()
    conn.close()


def _clean_db():
    """Очистка всех таблиц между тестами."""
    conn = sqlite3.connect(_test_db)
    for table in ("history", "processed_keys", "clients"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()


@pytest.fixture(autouse=True)
def clean_db():
    """Пересоздаём тестовую БД перед каждым тестом."""
    _init_test_db()
    _clean_db()
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _db():
    return sqlite3.connect(_test_db)


# --- 1. Создание лида ---
@pytest.mark.asyncio
async def test_create_lead_success(client):
    resp = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-001",
        "source": "avito",
        "source_id": "chat_1",
        "client_name": "Иван Петров",
    }, headers=HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert "client_id" in data
    assert data["status"] == "created"


# --- 2. Неверный ключ ---
@pytest.mark.asyncio
async def test_create_lead_wrong_key(client):
    resp = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-002",
        "source": "avito",
        "source_id": "chat_2",
    }, headers={"Content-Type": "application/json", "X-Internal-Key": "wrong-key"})
    assert resp.status_code == 403


# --- 3. Без ключа ---
@pytest.mark.asyncio
async def test_create_lead_missing_key(client):
    resp = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-003",
        "source": "avito",
        "source_id": "chat_3",
    }, headers={"Content-Type": "application/json"})
    assert resp.status_code == 403


# --- 4. Идемпотентность ---
@pytest.mark.asyncio
async def test_idempotency_duplicate(client):
    payload = {
        "idempotency_key": "test-004",
        "source": "avito",
        "source_id": "chat_4",
        "client_name": "Дубль",
    }
    resp1 = await client.post("/api/v1/leads", json=payload, headers=HEADERS)
    resp2 = await client.post("/api/v1/leads", json=payload, headers=HEADERS)
    assert resp1.json()["client_id"] == resp2.json()["client_id"]
    # В БД 1 клиент
    conn = _db()
    count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    conn.close()
    assert count == 1


# --- 5. Merge по phone ---
@pytest.mark.asyncio
async def test_merge_by_phone(client):
    resp1 = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-005a",
        "source": "avito",
        "source_id": "chat_5a",
        "client_name": "Первый",
        "phone": "79001234567",
    }, headers=HEADERS)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-005b",
        "source": "avito",
        "source_id": "chat_5b",
        "client_name": "Второй",
        "phone": "79001234567",
    }, headers=HEADERS)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "merged"

    # В БД 1 клиент
    conn = _db()
    count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    conn.close()
    assert count == 1


# --- 6. Merge по inn ---
@pytest.mark.asyncio
async def test_merge_by_inn(client):
    resp1 = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-006a",
        "source": "avito",
        "source_id": "chat_6a",
        "inn": "1234567890",
    }, headers=HEADERS)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-006b",
        "source": "avito",
        "source_id": "chat_6b",
        "inn": "1234567890",
    }, headers=HEADERS)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "merged"


# --- 7. Маппинг client_name → name ---
@pytest.mark.asyncio
async def test_client_name_mapping(client):
    await client.post("/api/v1/leads", json={
        "idempotency_key": "test-007",
        "source": "avito",
        "source_id": "chat_7",
        "client_name": "Иван",
    }, headers=HEADERS)

    conn = _db()
    name = conn.execute("SELECT name FROM clients WHERE source_id='chat_7'").fetchone()[0]
    conn.close()
    assert name == "Иван"


# --- 8. History при создании ---
@pytest.mark.asyncio
async def test_history_created_on_new_lead(client):
    resp = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-008",
        "source": "avito",
        "source_id": "chat_8",
        "client_name": "История",
    }, headers=HEADERS)
    client_id = resp.json()["client_id"]

    conn = _db()
    row = conn.execute(
        "SELECT action, auto FROM history WHERE client_id=?", (client_id,)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "lead_created"
    assert row[1] == 1


# --- 9. UPSERT same source ---
@pytest.mark.asyncio
async def test_upsert_same_source(client):
    resp1 = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-009a",
        "source": "avito",
        "source_id": "chat_9",
        "client_name": "Первая версия",
    }, headers=HEADERS)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/leads", json={
        "idempotency_key": "test-009b",
        "source": "avito",
        "source_id": "chat_9",
        "client_name": "Первая версия",
        "phone": "79998887766",
    }, headers=HEADERS)
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "updated"

    # В БД 1 клиент, phone обновился
    conn = _db()
    row = conn.execute("SELECT phone FROM clients WHERE source_id='chat_9'").fetchone()
    count = conn.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    conn.close()
    assert count == 1
    assert row[0] == "79998887766"


# --- 10. Пустой body ---
@pytest.mark.asyncio
async def test_bad_payload(client):
    resp = await client.post("/api/v1/leads", content=b"{}", headers=HEADERS)
    assert resp.status_code == 422
