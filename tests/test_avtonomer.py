from unittest.mock import patch

from avbot import avtonomer


def test_validate_ru_cars_license_plate():
    assert avtonomer.validate_ru_plate_number("a123aa123")
    assert avtonomer.validate_ru_plate_number("a123aa12")
    assert not avtonomer.validate_ru_plate_number("a123aa1")
    assert not avtonomer.validate_ru_plate_number("aaa123")


def test_validate_ru_pt_license_plates():
    assert avtonomer.validate_ru_pt_plate_number("ax12377")
    assert not avtonomer.validate_ru_pt_plate_number("ax123177")
    assert not avtonomer.validate_ru_pt_plate_number("a12399")


def test_validate_ru_moto_license_plates():
    assert avtonomer.validate_ru_moto_plate_number("1234ax77")
    assert avtonomer.validate_ru_moto_plate_number("1234ax177")
    assert not avtonomer.validate_ru_moto_plate_number("123ax77")
    assert not avtonomer.validate_ru_moto_plate_number("1234x77")


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
def test_search_ru_is_success(mockget):
    with open("tests/ru_fastsearch.html", "r") as f:
        data = f.read()
    mockget.return_value.text = data
    result = avtonomer.search_ru("а*аа37")
    assert len(result.cars) == 10
    assert result.total_results == 2000


@patch("avbot.avtonomer.scraper.get")
def test_search_su_is_success(mockget):
    with open("tests/su_fastsearch.html", "r") as f:
        data = f.read()
    mockget.return_value.text = data
    result = avtonomer.search_su("с0274НІ")
    assert len(result.cars) == 2
    assert result.cars[0].make == "Opel"
    assert result.cars[0].model == "Rekord"
    assert result.cars[0].date.day == 7
    assert result.cars[0].date.month == 4
    assert result.cars[0].date.year == 2021
    assert result.cars[0].page_url == "https://platesmania.com/su/nomer16485152"
    assert result.cars[0].thumb_url == "https://img03.platesmania.com/210407/m/16485152.jpg"
    assert result.cars[0].license_plate == "с 0274 НІ"


@patch("avbot.avtonomer.scraper.get")
def test_search_ru_is_failed_because_no_data(mockget):
    mockget.return_value.text = ""
    result = avtonomer.search_ru("а111аа777")
    assert result is None


def test_series_ru_url():
    url = avtonomer.get_series_ru_url("ack13")
    assert "https://platesmania.com/ru/gallery.php?fastsearch=a%2Ack13" == url


def test_series_us_url():
    url = avtonomer.get_series_us_url(1, 2, "rbb")
    assert "https://platesmania.com/us/gallery.php?gal=us&region=1&ctype=2&nomer=rbb+%2A" == url
