import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from loguru import logger
from sqlalchemy import text

from src.api.leads import router as leads_router
from src.db import async_session
from src.settings import settings

_start_time: float = 0.0


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | {message}",
    )
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger.add(
        log_dir / "app.log",
        level=settings.log_level,
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    setup_logging()
    _start_time = time.time()
    # Проверка БД при старте — не стартуем с битой базой
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        logger.info("БД crm.db — OK")
    except Exception as exc:
        logger.error("БД crm.db недоступна: {}", exc)
        raise RuntimeError(f"БД crm.db недоступна: {exc}") from exc
    logger.info("CRM-ядро v{} запускается", settings.app_version)
    yield
    logger.info("CRM-ядро останавливается")


app = FastAPI(
    title="CRM-ядро",
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(leads_router)


@app.get("/health")
async def health():
    db_status = "ok"
    outbox_pending = 0
    outbox_failed = 0
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            row = await session.execute(
                text("SELECT "
                     "SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END), "
                     "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) "
                     "FROM outbox")
            )
            counts = row.one()
            outbox_pending = counts[0] or 0
            outbox_failed = counts[1] or 0
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "service": "crm-core",
        "status": "ok" if db_status == "ok" else "degraded",
        "version": settings.app_version,
        "uptime_seconds": round(time.time() - _start_time),
        "db": db_status,
        "outbox_pending": outbox_pending,
        "outbox_failed": outbox_failed,
        "errors_last_hour": 0,
    }
