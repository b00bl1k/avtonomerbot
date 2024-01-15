import re

from avbot import avtonomer as an
from avbot import tasks
from avbot.i18n import __
from avbot.cmd.base import PlateRequestBase, translate_to_latin


class UzPrivateVehiclesRequest(PlateRequestBase):
    num_type = "uz"
    example = "01p347ta"
    description = __("private vehicle plate")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^(\d{2})\s*([a-z]{1})\s*(\d{3})\s*([a-z]{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search(
            "uz", validated_query, an.CTYPE_UZ_PRIVATE_VEHICLES)


UZ_PLATES = [
    UzPrivateVehiclesRequest,
]
