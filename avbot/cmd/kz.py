import re

from avbot import avtonomer as an
from avbot import tasks
from avbot.i18n import __
from avbot.cmd.base import PlateRequestBase, translate_to_latin


class KzPrivateVehicles2012Request(PlateRequestBase):
    num_type = "kz"
    example = "453dxa12"
    description = __("private vehicle plate (2012)")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^(\d{3})\s*([a-z]{3})\s*(\d{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search(
            "kz", validated_query, an.CTYPE_KZ_PRIVATE_VEHICLES_2012)


KZ_PLATES = [
    KzPrivateVehicles2012Request,
]
