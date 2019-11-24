import logging
import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
AN_KEY = os.environ["AN_KEY"]
REDIS_CACHE_URL = os.environ["REDIS_CACHE_URL"]
DATABASE_URL = os.environ["DATABASE_URL"]
SENTRY_DSN = os.environ.get("SENTRY_DSN")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
PROXY_URL = os.environ.get("PROXY_URL")
PROXY_USERNAME = os.environ.get("PROXY_USERNAME")
PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD")
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

if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(SENTRY_DSN)
