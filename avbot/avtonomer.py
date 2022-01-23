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

TAG_NEW_LETTER_COMBINATION = 13

# region, type
US_STATES_ID = {
    "pa": (7538, 111),
    "oh": (7535, 71),
    "nc": (7527, 101),
    "ny": (7534, 21),
}

RU_REGIONS_ID = {
    "01": ("Республика Адыгея", "10001"),
    "02": ("Республика Башкортостан", "10002"),
    "03": ("Республика Бурятия", "10003"),
    "04": ("Республика Алтай", "10004"),
    "05": ("Республика Дагестан", "10005"),
    "06": ("Республика Ингушетия", "10006"),
    "07": ("Кабардино-Балкарская Республика", "10007"),
    "08": ("Республика Калмыкия", "10008"),
    "09": ("Карачаево-Черкесская Республика", "10009"),
    "10": ("Республика Карелия", "10010"),
    "11": ("Республика Коми", "10011"),
    "12": ("Республика Марий Эл", "10012"),
    "13": ("Республика Мордовия", "10013"),
    "14": ("Республика Саха (Якутия)", "10014"),
    "15": ("Республика Северная Осетия-Алания", "10015"),
    "16": ("Республика Татарстан", "10016"),
    "17": ("Республика Тыва", "10017"),
    "18": ("Удмуртская Республика", "10018"),
    "19": ("Республика Хакасия", "10019"),
    "20": ("Чеченская Республика", "10020"),
    "21": ("Чувашская Республика", "10021"),
    "22": ("Алтайский край", "10022"),
    "23": ("Краснодарский край", "10023"),
    "24": ("Красноярский край", "10024"),
    "25": ("Приморский край", "10025"),
    "26": ("Ставропольский край", "10026"),
    "27": ("Хабаровский край", "10027"),
    "28": ("Амурская область", "10028"),
    "29": ("Архангельская область", "10029"),
    "30": ("Астраханская область", "10030"),
    "31": ("Белгородская область", "10031"),
    "32": ("Брянская область", "10032"),
    "33": ("Владимирская область", "10033"),
    "34": ("Волгоградская область", "10034"),
    "35": ("Вологодская область", "10035"),
    "36": ("Воронежская область", "10036"),
    "37": ("Ивановская область", "10037"),
    "38": ("Иркутская область", "10038"),
    "39": ("Калининградская область", "10039"),
    "40": ("Калужская область", "10040"),
    "41": ("Камчатский край", "10041"),
    "42": ("Кемеровская область", "10042"),
    "43": ("Кировская область", "10043"),
    "44": ("Костромская область", "10044"),
    "45": ("Курганская область", "10045"),
    "46": ("Курская область", "10046"),
    "47": ("Ленинградская область", "10047"),
    "48": ("Липецкая область", "10048"),
    "49": ("Магаданская область", "10049"),
    "50": ("Московская область", "10050"),
    "51": ("Мурманская область", "10051"),
    "52": ("Нижегородская область", "10052"),
    "53": ("Новгородская область", "10053"),
    "54": ("Новосибирская область", "10054"),
    "55": ("Омская область", "10055"),
    "56": ("Оренбургская область", "10056"),
    "57": ("Орловская область", "10057"),
    "58": ("Пензенская область", "10058"),
    "59": ("Пермский край", "10059"),
    "60": ("Псковская область", "10060"),
    "61": ("Ростовская область", "10061"),
    "62": ("Рязанская область", "10062"),
    "63": ("Самарская область", "10063"),
    "64": ("Саратовская область", "10064"),
    "65": ("Сахалинская область", "10065"),
    "66": ("Свердловская область", "10066"),
    "67": ("Смоленская область", "10067"),
    "68": ("Тамбовская область", "10068"),
    "69": ("Тверская область", "10069"),
    "70": ("Томская область", "10070"),
    "71": ("Тульская область", "10071"),
    "72": ("Тюменская область", "10072"),
    "73": ("Ульяновская область", "10073"),
    "74": ("Челябинская область", "10074"),
    "75": ("Забайкальский край", "10075"),
    "76": ("Ярославская область", "10076"),
    "77": ("г. Москва", "10077"),
    "78": ("г. Санкт-Петербург", "10078"),
    "79": ("Еврейская автономная область", "10079"),
    "80": ("Агинский Бурятский автономный округ", "10080"),
    "81": ("Коми-Пермяцкий автономный округ", "10081"),
    "82": ("Республика Крым", "10082"),
    "83": ("Ненецкий автономный округ", "10083"),
    "84": ("Таймырский (Долгано-Ненецкий) автономный округ", "10084"),
    "85": ("Усть-Ордынский Бурятский автономный округ", "10085"),
    "86": ("Ханты-Мансийский автономный округ - Югра", "10086"),
    "87": ("Чукотский автономный округ", "10087"),
    "88": ("Эвенкийский автономный округ", "10088"),
    "89": ("Ямало-Ненецкий автономный округ", "10089"),
    "90": ("Московская область", "10090"),
    "91": ("Калининградская область", "10091"),
    "92": ("г. Севастополь", "10092"),
    "93": ("Краснодарский край", "10093"),
    "94": ("Территории, находящиеся за пределами РФ", "10094"),
    "95": ("Чеченская Республика", "10095"),
    "96": ("Свердловская область", "10096"),
    "97": ("г. Москва", "10097"),
    "98": ("г. Санкт-Петербург", "10098"),
    "99": ("г. Москва", "10099"),
    "082": ("Корякский автономный округ", "11000"),
    "102": ("Республика Башкортостан", "10102"),
    "113": ("Республика Мордовия", "10113"),
    "116": ("Республика Татарстан", "10116"),
    "121": ("Чувашская Республика", "10121"),
    "122": ("Алтайский край", "10122"),
    "123": ("Краснодарский край", "10123"),
    "124": ("Красноярский край", "10124"),
    "125": ("Приморский край", "10125"),
    "126": ("Ставропольский край", "10126"),
    "134": ("Волгоградская область", "10134"),
    "136": ("Воронежская область", "10136"),
    "138": ("Иркутская область", "10138"),
    "142": ("Кемеровская область", "10142"),
    "147": ("Ленинградская область", "10147"),
    "150": ("Московская область", "10150"),
    "152": ("Нижегородская область", "10152"),
    "154": ("Новосибирская область", "10154"),
    "155": ("Омская область", "10155"),
    "156": ("Оренбургская область", "10156"),
    "159": ("Пермский край", "10159"),
    "161": ("Ростовская область", "10161"),
    "163": ("Самарская область", "10163"),
    "164": ("Саратовская область", "10164"),
    "173": ("Ульяновская область", "10173"),
    "174": ("Челябинская область", "10174"),
    "177": ("г. Москва", "10177"),
    "178": ("г. Санкт-Петербург", "10178"),
    "186": ("Ханты-Мансийский автономный округ - Югра", "10186"),
    "190": ("Московская область", "10190"),
    "193": ("Краснодарский край", "10193"),
    "196": ("Свердловская область", "10196"),
    "197": ("г. Москва", "10197"),
    "198": ("г. Санкт-Петербург", "10198"),
    "199": ("г. Москва", "10199"),
    "702": ("Республика Башкортостан", "10702"),
    "716": ("Республика Татарстан", "10716"),
    "750": ("Московская область", "10750"),
    "761": ("Ростовская область", "10761"),
    "763": ("Самарская область", "10763"),
    "774": ("Челябинская область", "10774"),
    "777": ("г. Москва", "10777"),
    "790": ("Московская область", "10790"),
    "797": ("г. Москва", "10797"),
    "799": ("г. Москва", "10799"),
    "977": ("г. Москва", "10977"),
}


@dataclass
class AvCar:
    make: str
    model: str
    date: date
    page_url: str
    photo_url: str
    thumb_url: str
    license_plate: str


@dataclass
class AvSearchResult:
    region: str
    informer_url: str
    total_results: int
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


def validate_ru_region(req):
    res = re.match(r"^ru(\d{2,3})$", req)
    if res:
        state = res.groups()[0]
        if state in RU_REGIONS_ID.keys():
            return res


def translate_to_cyrillic(number):
    chars = ("abekmhopctyx", "АВЕКМНОРСТУХ")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return number.translate(table)


def ensure_https(url):
    if url.lower().startswith("http:"):
        return "https:" + url[5:]
    return url


def parse_search_results(resp) -> Union[AvSearchResult, None]:
    resp.raise_for_status()
    res = re.search(r"Найдено номеров.*?<b>([\d\s]+)", resp.text)
    total_results = (
        int(res.group(1).replace(" ", ""))
        if res
        else 0
    )

    doc = BeautifulSoup(resp.text, "html.parser")
    panels = doc.select(".content .panel-body")
    if len(panels) == 0:
        return None

    cars = []
    for panel in panels:
        page_url = "https://avto-nomer.ru{}".format(panel.select("a")[0]["href"])
        thumb_url = ensure_https(panel.select("img")[0]["src"])
        license_plate = panel.select("img")[1]["alt"]
        dt = parse(panel.select("small.pull-right")[0].text)
        model_arr = panel.select("a")[1].text.split(" ", maxsplit=1)
        if len(model_arr) == 2:
            make, model = model_arr
        else:
            make = model_arr[0]
            model = ""
        cars.append(AvCar(make, model, dt, page_url, "", thumb_url, license_plate))

    return AvSearchResult("unknown", "", total_results, cars)


def search_ru(fastsearch=None, ctype=None, regions=None, tags=None) -> Union[AvSearchResult, None]:
    params = {}
    if fastsearch is not None:
        params["fastsearch"] = fastsearch
    if ctype is not None:
        params["ctype"] = ctype
    if regions is not None:
        params["aregions[0]"] = "_".join([RU_REGIONS_ID[r][1] for r in regions])
    if tags is not None:
        for i, tag in enumerate(tags):
            params[f"tags[{i}]"] = tag
    resp = scraper.get(
        "http://avto-nomer.ru/ru/gallery.php",
        params=params,
    )
    return parse_search_results(resp)


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
    return parse_search_results(resp)


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
