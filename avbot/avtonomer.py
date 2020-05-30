import cfscrape
from io import BytesIO
import json
import logging
import re
import requests

import cache

PHOTO_NOT_FOUND = "assets/not-found.png"

scraper = cfscrape.create_scraper()
logger = logging.getLogger(__name__)


def translate_to_latin(text):
    chars = ("авекмнорстухАВЕКМНОРСТУХ", "abekmhopctyxabekmhopctyx")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return text.lower().translate(table)


def validate_plate_number(number):
    res = re.match(r"^[abekmhopctyx]{1}\d{3}[abekmhopctyx]{2}\d{2,3}$", number)
    return res is not None


def validate_plate_series(number):
    res = re.match(r"^[abekmhopctyx]{3}\d{2,3}$", number)
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


def get_series(series_number):
    resp = scraper.get(
        "http://avto-nomer.ru/ru/gallery.php?fastsearch={}*{}".format(
            series_number[:1],
            series_number[1:],
        )
    )
    if resp.status_code != 200:
        return False
    res = re.search(r"Найдено номеров.*?<b>([\d\s]+)", resp.text)
    if res:
        return int(res.group(1).replace(" ", ""))


def get_car_photo(car):
    url = car["photo"]["medium"]

    file_id = cache.get(url)
    if file_id:
        return file_id, None

    resp = scraper.get(url)
    if resp.status_code == 200:
        return BytesIO(resp.content), url

    if resp.status_code == 404:
        file_id = cache.get(PHOTO_NOT_FOUND)
        if file_id:
            return file_id, None

        return open(PHOTO_NOT_FOUND, "rb"), PHOTO_NOT_FOUND

    return None, None


def cache_car_photo(key, file_id):
    cache.add(key, file_id)
