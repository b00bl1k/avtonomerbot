import re
import requests


def translate_to_latin(text):
    chars = ("авекмнорстухАВЕКМНОРСТУХ", "abekmhopctyxabekmhopctyx")
    table = dict([(ord(a), ord(b)) for (a, b) in zip(*chars)])
    return text.lower().translate(table)


def validate_plate_number(number):
    res = re.match("^[abekmnopctyx]{1}\d{3}[abekmnopctyx]{2}\d{2,3}$", number)
    return res is not None


def search(plate_number, key):
    resp = requests.get(
        "https://avto-nomer.ru/mobile/api_photo.php",
        params={
            "key": key,
            "gal": 1,
            "nomer": plate_number,
        },
    )
    return resp.json()
