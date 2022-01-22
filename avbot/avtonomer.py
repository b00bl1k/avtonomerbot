import logging
import re
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import List, Union
from requests import Request

import cfscrape
from bs4 import BeautifulSoup
from dateutil.parser import parse

scraper = cfscrape.create_scraper()
logger = logging.getLogger(__name__)


# region, type
US_STATES_ID = {
    "pa": (7538, 111),
    "oh": (7535, 71),
    "nc": (7527, 101),
    "ny": (7534, 21),
}


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


def translate_to_cyr(text):
    chars = ("iI", "\u0456\u0406")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return text.lower().translate(table)


def validate_ru_plate_number(number):
    res = re.match(r"^[abekmhopctyx]{1}\d{3}[abekmhopctyx]{2}\d{2,3}$", number)
    return res


def validate_su_plate_number(number):
    res = re.match(r"^[абвгдежзиклмнопрстуфхцчшщэюя\u0456]{1}\d{4}[абвгдежзиклмнопрстуфхцчшщэюя\u0456АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ\u0406]{2}$", number)
    return res


def validate_ru_plate_series(number):
    res = re.match(r"^[abekmhopctyx]{3}\d{2,3}$", number)
    return res


def validate_us_plate_series(number):
    res = re.match(r"^([a-z]{2})\s+([a-z]{3})$", number)
    if res:
        state = res.groups()[0]
        if state in US_STATES_ID.keys():
            return res


def translate_to_cyrillic(number):
    chars = ("abekmhopctyx", "АВЕКМНОРСТУХ")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return number.translate(table)


def ensure_https(url):
    if url.lower().startswith("http:"):
        return "https:" + url[5:]
    return url


def search_generic(resp) -> Union[AvSearchResult, None]:
    resp.raise_for_status()

    doc = BeautifulSoup(resp.text, "html.parser")
    panels = doc.select(".content .panel-body")
    if len(panels) == 0:
        return None

    cars = []
    for panel in panels:
        page_url = "https://avto-nomer.ru{}".format(panel.select("a")[0]["href"])
        thumb_url = ensure_https(panel.select("img")[0]["src"])
        dt = parse(panel.select("small.pull-right")[0].text)
        model_arr = panel.select("a")[1].text.split(" ", maxsplit=1)
        if len(model_arr) == 2:
            make, model = model_arr
        else:
            make = model_arr[0]
            model = ""
        cars.append(AvCar(make, model, dt, page_url, "", thumb_url))

    return AvSearchResult("unknown", "", cars)


def search_ru(plate_number, key) -> Union[AvSearchResult, None]:
    resp = scraper.get(
        "http://avto-nomer.ru/ru/gallery.php",
        params={
            "fastsearch": plate_number,
        },
    )
    return search_generic(resp)


def search_su(plate_number) -> Union[AvSearchResult, None]:
    resp = scraper.get(
        "http://avto-nomer.ru/su/gallery.php",
        params={
            "fastsearch": "{} {} {}".format(
                plate_number[:1],
                plate_number[1:5],
                plate_number[5:],
            ),
        },
    )
    return search_generic(resp)


def get_series_ru_url(series_number):
    return Request(
        "GET",
        "https://avto-nomer.ru/ru/gallery.php",
        params={
            "fastsearch": "{}*{}".format(
                series_number[:1],
                series_number[1:],
            ),
        },
    ).prepare().url


def get_series_ru(series_number):
    resp = scraper.get(
        "https://avto-nomer.ru/ru/gallery.php",
        params={
            "fastsearch": "{}*{}".format(
                series_number[:1],
                series_number[1:],
            ),
        },
    )
    resp.raise_for_status()
    res = re.search(r"Найдено номеров.*?<b>([\d\s]+)", resp.text)
    if res:
        return int(res.group(1).replace(" ", ""))


def get_series_us_url(region, ctype, series_number):
    return Request(
        "GET",
        "https://avto-nomer.ru/us/gallery.php",
        params={
            "gal": "us",
            "region": region,
            "ctype": ctype,
            "nomer": "{} *".format(series_number),
        },
    ).prepare().url


def get_series_us(region, ctype, series_number):
    resp = scraper.get(
        "https://avto-nomer.ru/us/gallery.php",
        params={
            "gal": "us",
            "region": region,
            "ctype": ctype,
            "nomer": "{} *".format(series_number),
        },
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
