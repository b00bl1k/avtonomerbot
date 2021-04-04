import logging
import re
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import List

import cfscrape
from dateutil.parser import parse

scraper = cfscrape.create_scraper()
logger = logging.getLogger(__name__)


@dataclass
class AvCar:
    make: str
    model: str
    date: date
    page_url: str
    photo_url: str
    thumb_url: str


@dataclass
class AvSearchResult:
    region: str
    informer_url: str
    cars: List[AvCar]


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


def ensure_https(url):
    if url.lower().startswith("http:"):
        return "https:" + url[5:]
    return url


def search(plate_number, key) -> AvSearchResult:
    resp = scraper.get(
        "https://avto-nomer.ru/mobile/api_photo.php",
        params={
            "key": key,
            "gal": 1,
            "nomer": plate_number,
        },
    )
    resp.raise_for_status()
    result = resp.json()
    if result["error"] == 0:
        cars = [
            AvCar(
                item["make"],
                item["model"],
                parse(item["date"]),
                ensure_https(item["photo"]["link"]),
                ensure_https(item["photo"]["original"]),
                ensure_https(item["photo"]["medium"]),
            )
            for item in result["cars"]
        ]
        return AvSearchResult(
            result["region"],
            ensure_https(result["informer"]),
            cars,
        )


def get_series(series_number):
    resp = scraper.get(
        "https://avto-nomer.ru/ru/gallery.php?fastsearch={}*{}".format(
            series_number[:1],
            series_number[1:],
        )
    )
    resp.raise_for_status()
    res = re.search(r"Найдено номеров.*?<b>([\d\s]+)", resp.text)
    if res:
        return int(res.group(1).replace(" ", ""))


def load_photo(path):
    resp = scraper.get(path)
    if resp.status_code == 200:
        return BytesIO(resp.content)
    if resp.status_code != 404:
        resp.raise_for_status()
