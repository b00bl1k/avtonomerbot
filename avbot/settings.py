import logging
import os
import redis

BOT_TOKEN = os.environ["BOT_TOKEN"]
AN_KEY = os.environ["AN_KEY"]
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_CACHE_DB = int(os.environ.get("REDIS_CACHE_DB", 0))
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
    format="%(asctime)s %(filename)s:%(lineno)d: %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S"
)

cache = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_CACHE_DB)
