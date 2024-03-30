import re

from avbot import avtonomer as an
from avbot import tasks
from avbot.i18n import __
from avbot.cmd.base import PlateRequestBase, translate_to_latin


class UaPrivateVehiclesRequest(PlateRequestBase):
    num_type = "ua"
    example = "aa1234bb"
    description = __("regular plates (2004)")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^([a-z]{2})\s*(\d{4})\s*([a-z]{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search(
            "ua", validated_query, an.CTYPE_UA_REGULAR_PLATES_2004)


UA_PLATES = [
    UaPrivateVehiclesRequest,
]
