import logging
import os

from avbot import i18n

BOT_TOKEN = os.environ.get("BOT_TOKEN", "1234:test")
REDIS_CACHE_URL = os.environ.get("REDIS_CACHE_URL", "redis://localhost:6379")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:pwd@pg/db")
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
SENTRY_DSN = os.environ.get("SENTRY_DSN")
SENTRY_SAMPLE_RATE = float(os.environ.get("SENTRY_SAMPLE_RATE", 0.2))
FWD_CHAT_ID = os.environ.get("FWD_CHAT_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "/")
WEBHOOK_HOST = os.environ.get("WEBHOOK_HOST", "localhost")
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "5000"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
PROXY_URL = os.environ.get("PROXY_URL")
PROXY_USERNAME = os.environ.get("PROXY_USERNAME")
PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD")
LOCALE_PATH = "avbot/locale"
VIN_PROVIDER_URL = os.environ.get("VIN_PROVIDER_URL")
VIN_PROVIDER_TOKEN = os.environ.get("VIN_PROVIDER_TOKEN")


REQUEST_KWARGS = (
    {
        "proxy_url": PROXY_URL,
        "urllib3_proxy_kwargs": {
            "username": PROXY_USERNAME,
            "password": PROXY_PASSWORD,
        },
    }
    if PROXY_URL
    else None
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(levelname)s %(asctime)s %(name)s: %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)

i18n.load_translations(LOCALE_PATH)

if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(SENTRY_DSN, traces_sample_rate=SENTRY_SAMPLE_RATE)
