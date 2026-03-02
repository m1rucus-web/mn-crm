"""Lead merger — дедупликация по phone/inn и merge полей."""

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Client, History


async def find_duplicate(
    session: AsyncSession, phone: str | None, inn: str | None
) -> Client | None:
    """Ищет существующего клиента (WHERE deleted_at IS NULL) по phone ИЛИ inn."""
    if phone:
        result = await session.execute(
            select(Client).where(
                Client.phone == phone,
                Client.deleted_at.is_(None),
            )
        )
        found = result.scalar_one_or_none()
        if found:
            return found

    if inn:
        result = await session.execute(
            select(Client).where(
                Client.inn == inn,
                Client.deleted_at.is_(None),
            )
        )
        found = result.scalar_one_or_none()
        if found:
            return found

    return None


# Поля клиента, которые можно обновить при merge
_MERGEABLE_FIELDS = [
    "name", "phone", "telegram", "email", "inn", "company_name",
    "client_type", "tax_system", "has_employees", "employees_count",
    "need", "marketplace", "city", "source_url",
    "qualification_summary", "estimated_price",
    "messages_count", "first_message_at", "source_last_message_at",
    "consent_given_at",
]


async def merge_lead(
    session: AsyncSession, existing: Client, new_data: dict
) -> Client:
    """Обновляет поля existing из new_data (только если existing.field пустой/None).

    НЕ перезаписывает заполненные поля пустыми.
    Записывает в history: action='lead_merged', auto=1.
    """
    updated_fields = []

    for field in _MERGEABLE_FIELDS:
        new_value = new_data.get(field)
        if new_value is None:
            continue
        current_value = getattr(existing, field, None)
        # Не перезаписываем заполненные поля
        if current_value is not None and current_value != "" and current_value != 0:
            continue
        setattr(existing, field, new_value)
        updated_fields.append(field)

    existing.updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Запись в history
    history_entry = History(
        client_id=existing.id,
        action="lead_merged",
        details=json.dumps(
            {
                "updated_fields": updated_fields,
                "source_id": new_data.get("source_id", ""),
            },
            ensure_ascii=False,
        ),
        auto=1,
    )
    session.add(history_entry)
    await session.flush()

    return existing
