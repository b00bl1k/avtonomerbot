import re

from avbot import avtonomer as an
from avbot import tasks
from avbot.i18n import _, __
from avbot.cmd.base import PlateRequestBase, translate_to_latin, \
    translate_to_cyrillic


class RuVehicleRequest(PlateRequestBase):
    num_type = "ru"
    example = "а123аа777"
    description = __("vehicle plate 🚗")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^([abekmhopctyx]{1})\s*(\d{3})\s*([abekmhopctyx]{2})\s*(\d{2,3})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_ru(validated_query, an.CTYPE_RU_CARS)


class RuTrailersRequest(PlateRequestBase):
    num_type = "ru-trailer"
    example = "ан239936"
    description = __("trailer plate")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^([abekmhopctyx]{2})\s*(\d{4})\s*(\d{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_ru(validated_query, an.CTYPE_RU_TRAILERS)


class RuSpecialVehiclesRequest(PlateRequestBase):
    num_type = "ru-spec"
    example = "4197хк47"
    description = __("special vehicle plate 🚜")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^(\d{4})\s*([abekmhopctyx]{2})\s*(\d{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_ru(validated_query, an.CTYPE_RU_SPECIAL_VEHICLES)


class RuMotorcyclesRequest(PlateRequestBase):
    num_type = "ru-moto"
    example = "7851аа40"
    description = __("motorcycle plate 🏍")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^(\d{4})\s*([abekmhopctyx]{2})\s*(\d{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_ru(validated_query, an.CTYPE_RU_MOTORCYCLES)


class RuTransitRequest(PlateRequestBase):
    num_type = "ru-transit"
    example = "нт005х77"
    description = __("transit plate")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^([abekmhopctyx]{2})\s*(\d{3})\s*([abekmhopctyx]{1})\s*(\d{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_ru(validated_query, an.CTYPE_RU_NEW_TRANSIT)


class RuPublicTransportRequest(PlateRequestBase):
    num_type = "ru-pt"
    example = "аа12377"
    description = __("public transport plate 🚌")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^([abekmhopctyx]{2})\s*(\d{3})\s*(\d{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_ru(validated_query, an.CTYPE_RU_PUBLIC_TRSNSPORT)


class RuPoliceVehiclesRequest(PlateRequestBase):
    num_type = "ru-police"
    example = "с201799"
    description = __("police vehicles plate 🚓")
    task = tasks.an_paginated_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^([abekmhopctyx]{1})\s*(\d{4})\s*(\d{2})$",
            query
        )
        if res:
            return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_ru(validated_query, an.CTYPE_RU_POLICE_VEHICLES)


class RuRegionInfoRequest(PlateRequestBase):
    num_type = "ru-region"
    example = "ru37"
    description = __("info about region")
    task = tasks.an_listed_search

    @classmethod
    def validate(cls, query):
        res = re.match(r"^ru(\d{2,3})$", query.lower())
        if res:
            region = res.groups()[0]
            if region in an.RU_REGIONS_ID.keys():
                return f"ru{region}"

    @classmethod
    def search(cls, validated_query):
        region = validated_query[2:]
        return an.search_ru(
            ctype=an.CTYPE_RU_CARS,
            regions=[region],
            tags=[an.TAG_NEW_LETTER_COMBINATION],
        )

    @classmethod
    def msg_no_results(cls, validated_query):
        region = validated_query[2:]
        region_name = an.RU_REGIONS_ID.get(region)[0]
        return _("Region *{region}* — {region_name}").format(
            region=region,
            region_name=region_name,
        )

    @classmethod
    def msg_with_results(cls, validated_query, result):
        message = cls.msg_no_results(validated_query)
        message += "\n\n" + _("Latest series:") + "\n"
        message += "\n".join([
            "• {} /{} — {} {}".format(
                car.date,
                translate_to_latin(
                    car.license_plate.replace(" ", "")
                ).upper(),
                car.make,
                car.model,
            )
            for car in result.cars
        ])
        return message


class RuSeriesInfoRequest(PlateRequestBase):
    num_type = "ru-series"
    example = "ааа777"
    description = __("info about vehicle plate series")
    task = tasks.an_listed_search

    @classmethod
    def validate(cls, query):
        query = translate_to_latin(query)
        res = re.match(
            r"^([abekmhopctyx]{1})[\s\*]*([abekmhopctyx]{2})(\d{2,3})$",
            query,
        )
        if res:
            region = res.groups()[2]
            if region in an.RU_REGIONS_ID.keys():
                return "".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        return an.search_ru(
            fastsearch="{}*{}".format(
                validated_query[:1],
                validated_query[1:],
            ),
            ctype=an.CTYPE_RU_CARS,
        )

    @classmethod
    def msg_no_results(cls, validated_query):
        url = an.get_series_ru_url(validated_query)
        series_number = translate_to_cyrillic(validated_query)
        message = _("No plates in the series [{series_number}]({url}) yet")\
            .format(series_number=series_number, url=url)
        return message

    @classmethod
    def msg_with_results(cls, validated_query, result):
        url = an.get_series_ru_url(validated_query)
        series_number = translate_to_cyrillic(validated_query)

        cnt = result.total_results
        message = _("Pictures in the series [{series_number}]({url}): {cnt}")\
            .format(series_number=series_number, url=url, cnt=cnt)
        message += "\n\n" + _("Latest plates:") + "\n"
        message += "\n".join([
            "• {} /{} — {} {}".format(
                car.date,
                translate_to_latin(
                    car.license_plate.replace(" ", "")
                ).upper(),
                car.make,
                car.model,
            )
            for car in result.cars
        ])
        return message


RU_PLATES = [
    RuVehicleRequest,
    RuTrailersRequest,
    RuSpecialVehiclesRequest,
    RuMotorcyclesRequest,
    RuTransitRequest,
    RuPublicTransportRequest,
    RuPoliceVehiclesRequest,
    RuRegionInfoRequest,
    RuSeriesInfoRequest,
]
