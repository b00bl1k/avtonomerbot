import re

from avbot import avtonomer as an
from avbot import tasks
from avbot.i18n import __
from avbot.cmd.base import PlateRequestBase


class GeVehicles2014Request(PlateRequestBase):
    num_type = "ge"
    example = "af-235-fa"
    description = __("vehicle plate (2014)")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = query.lower()
        res = re.match(
            r"^([a-z]{2})-(\d{3})-([a-z]{2})$",
            query
        )
        if res:
            return "-".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search(
            "ge", validated_query, an.CTYPE_GE_VEHICLES_2014)


GE_PLATES = [
    GeVehicles2014Request,
]
