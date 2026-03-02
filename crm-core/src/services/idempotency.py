"""Idempotency service — проверка и сохранение idempotency_key в processed_keys."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ProcessedKey


async def check_idempotency(session: AsyncSession, key: str) -> dict | None:
    """Ищет key в processed_keys. Найден → json.loads(response). Не найден → None."""
    result = await session.execute(
        select(ProcessedKey).where(ProcessedKey.idempotency_key == key)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return json.loads(row.response) if row.response else None


async def save_idempotency(session: AsyncSession, key: str, response: dict) -> None:
    """Сохраняет key + json.dumps(response) в processed_keys."""
    pk = ProcessedKey(
        idempotency_key=key,
        response=json.dumps(response, ensure_ascii=False),
    )
    session.add(pk)
    await session.flush()
