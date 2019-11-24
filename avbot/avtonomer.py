import json
import logging
import re
import requests

logger = logging.getLogger(__name__)


def translate_to_latin(text):
    chars = ("авекмнорстухАВЕКМНОРСТУХ", "abekmhopctyxabekmhopctyx")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return text.lower().translate(table)


def validate_plate_number(number):
    res = re.match(r"^[abekmhopctyx]{1}\d{3}[abekmhopctyx]{2}\d{2,3}$", number)
    return res is not None


def translate_to_cyrillic(number):
    chars = ("abekmhopctyx", "АВЕКМНОРСТУХ")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return number.translate(table)


def search(plate_number, key):
    try:
        resp = requests.get(
            "http://avto-nomer.ru/mobile/api_photo.php",
            params={
                "key": key,
                "gal": 1,
                "nomer": plate_number,
            },
        )
        return resp.json()
    except (json.decoder.JSONDecodeError,
            requests.exceptions.ConnectionError) as e:
        logger.error("search error", exc_info=e)
        return None
