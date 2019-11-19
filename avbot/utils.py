from functools import wraps
import pickle
from settings import cache


def cached_func(time):
    def actual_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = pickle.dumps([args, kwargs])
            cached_value = cache.get(key)
            if cached_value is not None:
                return pickle.loads(cached_value)
            value = func(*args, **kwargs)
            if value is not None:
                cache.setex(key, time, pickle.dumps(value))
            return value
        return wrapper
    return actual_decorator
