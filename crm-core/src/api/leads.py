"""POST /api/v1/leads — приём лидов из Авито-бота."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Response
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select

from src.db import async_session
from src.models import Client, History
from src.services.idempotency import check_idempotency, save_idempotency
from src.services.lead_merger import find_duplicate, merge_lead
from src.settings import settings

router = APIRouter(prefix="/api/v1", tags=["leads"])


class LeadRequest(BaseModel):
    idempotency_key: str
    trace_id: str | None = None
    source: str = "avito"
    source_id: str
    client_name: str | None = None
    phone: str | None = None
    telegram: str | None = None
    email: str | None = None
    inn: str | None = None
    company_name: str | None = None
    client_type: str | None = None
    tax_system: str | None = None
    has_employees: bool = False
    employees_count: int = 0
    need: str | None = None
    marketplace: str | None = None
    city: str | None = None
    source_url: str | None = None
    qualification_summary: str | None = None
    estimated_price: str | None = None
    messages_count: int | None = None
    first_message_at: str | None = None
    last_message_at: str | None = None
    consent_given_at: str | None = None


def _build_client_data(req: LeadRequest) -> dict:
    """Маппинг request → Client fields.

    client_name → name, last_message_at → source_last_message_at.
    """
    data: dict = {}
    if req.client_name is not None:
        data["name"] = req.client_name
    if req.phone is not None:
        data["phone"] = req.phone
    if req.telegram is not None:
        data["telegram"] = req.telegram
    if req.email is not None:
        data["email"] = req.email
    if req.inn is not None:
        data["inn"] = req.inn
    if req.company_name is not None:
        data["company_name"] = req.company_name
    if req.client_type is not None:
        data["client_type"] = req.client_type
    if req.tax_system is not None:
        data["tax_system"] = req.tax_system
    data["has_employees"] = int(req.has_employees)
    data["employees_count"] = req.employees_count
    if req.need is not None:
        data["need"] = req.need
    if req.marketplace is not None:
        data["marketplace"] = req.marketplace
    if req.city is not None:
        data["city"] = req.city
    if req.source_url is not None:
        data["source_url"] = req.source_url
    if req.qualification_summary is not None:
        data["qualification_summary"] = req.qualification_summary
    if req.estimated_price is not None:
        data["estimated_price"] = req.estimated_price
    if req.messages_count is not None:
        data["messages_count"] = req.messages_count
    if req.first_message_at is not None:
        data["first_message_at"] = req.first_message_at
    if req.last_message_at is not None:
        data["source_last_message_at"] = req.last_message_at
    if req.consent_given_at is not None:
        data["consent_given_at"] = req.consent_given_at
    return data


@router.post("/leads")
async def create_lead(
    req: LeadRequest,
    response: Response,
    x_internal_key: str | None = Header(None),
):
    """Приём лида из Авито-бота: авторизация, идемпотентность, дедупликация, UPSERT."""
    # 1. Авторизация X-Internal-Key
    if not x_internal_key or x_internal_key != settings.avito_internal_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    async with async_session() as session:
        async with session.begin():
            # 2. Идемпотентность
            cached = await check_idempotency(session, req.idempotency_key)
            if cached is not None:
                logger.info(
                    "trace={} source_id={} idempotent_hit",
                    req.trace_id, req.source_id,
                )
                response.status_code = 201 if cached.get("status") == "created" else 200
                return cached

            # 3. Дедупликация по phone/inn
            duplicate = await find_duplicate(session, req.phone, req.inn)
            if duplicate:
                new_data = _build_client_data(req)
                merged = await merge_lead(session, duplicate, new_data)
                result = {"status": "merged", "client_id": merged.id}
                await save_idempotency(session, req.idempotency_key, result)
                logger.info(
                    "trace={} source_id={} merged client_id={}",
                    req.trace_id, req.source_id, merged.id,
                )
                response.status_code = 200
                return result

            # 4. UPSERT по (source, source_id)
            row = await session.execute(
                select(Client).where(
                    Client.source == req.source,
                    Client.source_id == req.source_id,
                )
            )
            existing = row.scalar_one_or_none()

            if existing:
                # UPDATE (конфликт source + source_id)
                client_data = _build_client_data(req)
                updated_fields = []
                for field, value in client_data.items():
                    old = getattr(existing, field, None)
                    if old != value:
                        setattr(existing, field, value)
                        updated_fields.append(field)
                existing.updated_at = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                session.add(
                    History(
                        client_id=existing.id,
                        action="lead_updated",
                        details=json.dumps(
                            {
                                "updated_fields": updated_fields,
                                "source_id": req.source_id,
                            },
                            ensure_ascii=False,
                        ),
                        auto=1,
                    )
                )
                await session.flush()

                result = {"status": "updated", "client_id": existing.id}
                await save_idempotency(session, req.idempotency_key, result)
                logger.info(
                    "trace={} source_id={} updated client_id={}",
                    req.trace_id, req.source_id, existing.id,
                )
                response.status_code = 200
                return result

            # INSERT (новый клиент)
            client_data = _build_client_data(req)
            new_client = Client(
                source=req.source,
                source_id=req.source_id,
                idempotency_key=req.idempotency_key,
                **client_data,
            )
            session.add(new_client)
            await session.flush()

            session.add(
                History(
                    client_id=new_client.id,
                    action="lead_created",
                    auto=1,
                )
            )
            await session.flush()

            result = {"status": "created", "client_id": new_client.id}
            await save_idempotency(session, req.idempotency_key, result)
            logger.info(
                "trace={} source_id={} created client_id={}",
                req.trace_id, req.source_id, new_client.id,
            )
            response.status_code = 201
            return result
