"""SQLAlchemy ORM-модели для crm.db — 8 таблиц из FOUNDATION.md §6."""

from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("source", "source_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str | None] = mapped_column(String)
    idempotency_key: Mapped[str | None] = mapped_column(String, unique=True)
    name: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    telegram: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    inn: Mapped[str | None] = mapped_column(String)
    company_name: Mapped[str | None] = mapped_column(String)
    client_type: Mapped[str | None] = mapped_column(String)
    tax_system: Mapped[str | None] = mapped_column(String)
    has_employees: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    employees_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    need: Mapped[str | None] = mapped_column(String)
    marketplace: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    source_url: Mapped[str | None] = mapped_column(String)
    pipeline_stage: Mapped[str] = mapped_column(String, default="new", server_default="new")
    responsible_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    qualification_summary: Mapped[str | None] = mapped_column(Text)
    estimated_price: Mapped[str | None] = mapped_column(String)
    monthly_price: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    is_waiting_docs: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_vip_newcomer: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_client_message_at: Mapped[str | None] = mapped_column(String)
    messages_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    first_message_at: Mapped[str | None] = mapped_column(String)
    source_last_message_at: Mapped[str | None] = mapped_column(String)
    drip_campaign_step: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    drip_next_at: Mapped[str | None] = mapped_column(String)
    drip_active: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    consent_given_at: Mapped[str | None] = mapped_column(String)
    deleted_at: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))
    updated_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    short_name: Mapped[str | None] = mapped_column(String)
    username: Mapped[str | None] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="accountant", server_default="accountant")
    max_clients: Mapped[int] = mapped_column(Integer, default=20, server_default="20")
    status: Mapped[str] = mapped_column(String, default="active", server_default="active")
    substitute_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"))
    is_active: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))


class History(Base):
    __tablename__ = "history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    action: Mapped[str] = mapped_column(String, nullable=False)
    details: Mapped[str | None] = mapped_column(Text)
    employee_id: Mapped[int | None] = mapped_column(Integer)
    auto: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    employee_id: Mapped[int | None] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[str] = mapped_column(String, nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending", server_default="pending")
    deleted_at: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))


class OnboardingDocument(Base):
    __tablename__ = "onboarding_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("clients.id"))
    doc_type: Mapped[str] = mapped_column(String, nullable=False)
    doc_name: Mapped[str] = mapped_column(String, nullable=False)
    is_received: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    received_at: Mapped[str | None] = mapped_column(String)
    last_reminder_at: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))


class ProcessedKey(Base):
    __tablename__ = "processed_keys"

    idempotency_key: Mapped[str] = mapped_column(String, primary_key=True)
    response: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))


class OutboxMessage(Base):
    __tablename__ = "outbox"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_url: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, default="POST", server_default="POST")
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String, unique=True)
    trace_id: Mapped[str | None] = mapped_column(String)
    aggregate_key: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending", server_default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, default=10, server_default="10")
    next_retry_at: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))
    sent_at: Mapped[str | None] = mapped_column(String)
    response_code: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)


class DripEvent(Base):
    __tablename__ = "drip_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(Integer, nullable=False)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_at: Mapped[str | None] = mapped_column(String, server_default=text("(datetime('now'))"))
    meta: Mapped[str | None] = mapped_column(Text)
