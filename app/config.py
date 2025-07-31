import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

LOCAL_SUBDOMAIN: str = "localhost"

DEBUG = bool(os.environ.get("DEBUG", False))
SECRET_KEY = os.environ.get("SECRET_KEY", "long-long-long-secret-key")

DB_URL = str(os.environ.get("DB_URL"))

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*")
SITE_DOMAIN = str(os.environ.get("SITE_DOMAIN"))
EXECUTOR_HOST = os.environ.get("EXECUTOR_HOST")

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATIC_ROOT = os.path.join(BASE_DIR, "static")

LOG_LEVEL = "INFO" if DEBUG is True else "INFO"
