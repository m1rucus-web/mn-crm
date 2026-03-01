import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from loguru import logger

from src.settings import settings


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
    setup_logging()
    logger.info("Авито-бот v{} запускается", settings.app_version)
    yield
    logger.info("Авито-бот останавливается")


app = FastAPI(
    title="Авито-бот",
    version=settings.app_version,
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "service": "avito-bot",
        "status": "ok",
        "version": settings.app_version,
    }
