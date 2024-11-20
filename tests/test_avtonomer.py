from unittest.mock import patch

from avbot import avtonomer


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
    result = avtonomer.search("su", "с0274НІ")
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
def test_search_us_is_success(mockget):
    with open("tests/us_fastsearch.html", "r") as f:
        data = f.read()
    mockget.return_value.text = data
    result = avtonomer.search("us", "kgh")
    assert len(result.cars) == 3
    assert result.cars[0].make == "Chrysler"
    assert result.cars[0].model == "LeBaron"


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
