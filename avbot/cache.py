from functools import wraps
import pickle
import redis

from avbot import settings

_cache = redis.StrictRedis.from_url(settings.REDIS_CACHE_URL)


def add(key, value, time=None):
    key = pickle.dumps(key)
    serialized_value = pickle.dumps(value)
    if time:
        _cache.setex(key, time, serialized_value)
    else:
        _cache.set(key, serialized_value)
    return value


def get(key):
    key = pickle.dumps(key)
    cached_value = _cache.get(key)
    if cached_value:
        return pickle.loads(cached_value)
    return None


def cached_func(time):
    def actual_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = pickle.dumps([args, kwargs])
            cached_value = _cache.get(key)
            if cached_value is not None:
                return pickle.loads(cached_value)
            value = func(*args, **kwargs)
            if value is not None:
                _cache.setex(key, time, pickle.dumps(value))
            return value
        return wrapper
    return actual_decorator
