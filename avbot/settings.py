import logging
import os

import i18n

BOT_TOKEN = os.environ["BOT_TOKEN"]
AN_KEY = os.environ["AN_KEY"]
REDIS_CACHE_URL = os.environ["REDIS_CACHE_URL"]
DATABASE_URL = os.environ["DATABASE_URL"]
CELERY_BROKER_URL = os.environ["CELERY_BROKER_URL"]
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
LOCALE_PATH = "locale"

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
