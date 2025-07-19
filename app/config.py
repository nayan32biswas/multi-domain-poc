import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from mongodb_odm import connect, disconnect

logger = logging.getLogger(__name__)

LOCAL_SUBDOMAIN = "localhost"

DEBUG = bool(os.environ.get("DEBUG", False))
SECRET_KEY = os.environ.get("SECRET_KEY", "long-long-long-secret-key")

DB_URL = str(os.environ.get("DB_URL"))

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*")

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATIC_ROOT = os.path.join(BASE_DIR, "static")

LOG_LEVEL = "INFO" if DEBUG is True else "INFO"


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    connect(DB_URL)

    yield

    disconnect()
