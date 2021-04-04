from unittest.mock import patch

from avbot import avtonomer


def test_validate_license_plate_number():
    assert avtonomer.validate_plate_number("a123aa123")
    assert avtonomer.validate_plate_number("a123aa12")
    assert not avtonomer.validate_plate_number("a123aa1")
    assert not avtonomer.validate_plate_number("aaa123")


def test_validate_plate_series():
    assert avtonomer.validate_plate_series("aaa199")
    assert avtonomer.validate_plate_series("aaa19")
    assert not avtonomer.validate_plate_series("aa199")
    assert not avtonomer.validate_plate_series("aaaa199")


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
    result = avtonomer.search("a123aa123", "key")
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
    result = avtonomer.search("a123aa123", "key")
    assert result is None
