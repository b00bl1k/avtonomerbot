import re

from avbot import avtonomer as an
from avbot import tasks
from avbot.i18n import __
from avbot.cmd.base import PlateRequestBase, translate_to_cyr


class SuVehicleRequest(PlateRequestBase):
    num_type = "su"
    example = "а0069МО"
    description = __("private vehicles (1980) 🚗")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_cyr(query)
        res = re.match(
            r"^([абвгдежзиклмнопрстуфхцчшщэюя\u0456]{1})\s*(\d{4})\s*([абвгдежзиклмнопрстуфхцчшщэюя\u0456АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ\u0406]{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_su(validated_query, an.CTYPE_SU_PRIVATE_VEHICLES_1980)


SU_PLATES = [
    SuVehicleRequest,
]
