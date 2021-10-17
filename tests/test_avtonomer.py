from unittest.mock import patch

from avbot import avtonomer


def test_validate_ru_license_plate():
    assert avtonomer.validate_ru_plate_number("a123aa123")
    assert avtonomer.validate_ru_plate_number("a123aa12")
    assert not avtonomer.validate_ru_plate_number("a123aa1")
    assert not avtonomer.validate_ru_plate_number("aaa123")


def test_validate_su_license_plate():
    assert avtonomer.validate_su_plate_number("ж8028ХА")
    assert avtonomer.validate_su_plate_number("ж8028ха")
    assert avtonomer.validate_su_plate_number("ж8028Н\u0406")
    assert not avtonomer.validate_su_plate_number("ж8028Х")
    assert not avtonomer.validate_su_plate_number("b8028ХА")


def test_validate_plate_series():
    assert avtonomer.validate_ru_plate_series("aaa199")
    assert avtonomer.validate_ru_plate_series("aaa19")
    assert not avtonomer.validate_ru_plate_series("aa199")
    assert not avtonomer.validate_ru_plate_series("aaaa199")


@patch("avbot.avtonomer.scraper.get")
def test_search(mockget):
    data = {
        "error": 0,
        "region": "37",
        "informer": "http://url1",
        "cars": [
            {
                "make": "Mitsubishi",
                "model": "Outlander XL",
                "date": "2019-03-21 21:51:58",
                "photo":
                {
                    "link": "http://url2",
                    "small": "http://url3",
                    "medium": "http://url4",
                    "original": "http://url5"
                }
            }
        ]
    }
    mockget.return_value.json.return_value = data
    result = avtonomer.search_ru("a123aa123", "key")
    assert result.region == "37"
    assert result.informer_url == "https://url1"
    assert len(result.cars) == 1
    assert result.cars[0].make == "Mitsubishi"
    assert result.cars[0].model == "Outlander XL"
    assert result.cars[0].date.day == 21
    assert result.cars[0].date.month == 3
    assert result.cars[0].date.year == 2019
    assert result.cars[0].page_url == "https://url2"
    assert result.cars[0].photo_url == "https://url5"
    assert result.cars[0].thumb_url == "https://url4"

    data = {"error": 1}
    mockget.return_value.json.return_value = data
    result = avtonomer.search_ru("a123aa123", "key")
    assert result is None


@patch("avbot.avtonomer.scraper.get")
def test_search_su(mockget):
    with open("tests/su.html", "r") as f:
        data = f.read()
    mockget.return_value.text = data
    result = avtonomer.search_su("с0274НІ")
    assert len(result.cars) == 2
    assert result.cars[0].make == "Opel"
    assert result.cars[0].model == "Rekord"
    assert result.cars[0].date.day == 7
    assert result.cars[0].date.month == 4
    assert result.cars[0].date.year == 2021
    assert result.cars[0].page_url == "https://avto-nomer.ru/su/nomer16485152"
    assert result.cars[0].thumb_url == "https://img03.platesmania.com/210407/m/16485152.jpg"


def test_series_ru_url():
    url = avtonomer.get_series_ru_url("ack13")
    assert "https://avto-nomer.ru/ru/gallery.php?fastsearch=a%2Ack13" == url


def test_series_us_url():
    url = avtonomer.get_series_us_url(1, 2, "rbb")
    assert "https://avto-nomer.ru/us/gallery.php?gal=us&region=1&ctype=2&nomer=rbb+%2A" == url
