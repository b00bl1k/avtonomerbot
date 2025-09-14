import re
from requests import Request

from avbot import avtonomer as an
from avbot import tasks
from avbot.i18n import _, __
from avbot.cmd.base import PlateRequestBase, translate_to_latin, \
    translate_to_cyrillic

# region, ctype
US_STATES_ID = {
    "ga": {"name": "Georgia", "id": (7510, 91), "query": "{}*"},  # four digits
    "pa": {"name": "Pennsylvania", "id": (7538, 111), "query": "{} *"},
    "oh": {"name": "Ohio", "id": (7535, 71), "query": "{} *"},
    "nc": {"name": "North Carolina", "id": (7527, 101), "query": "{} *"},
    "ny": {"name": "New York", "id": (7534, 21), "query": "{} *"},
}


class UsSeriesInfoRequest(PlateRequestBase):
    num_type = "us"
    example = "ny xxx"
    description = __("info about state plate series (possible states: ga, pa, oh, nc, ny)")
    task = tasks.an_listed_search

    @classmethod
    def validate(cls, query):
        res = re.match(
            r"^([a-z]{2})\s+([a-z]{3})$",
            query.lower(),
        )
        if res:
            state = res.groups()[0]
            if state in US_STATES_ID.keys():
                return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        state, series = validated_query.split()
        state_id, ctype_id = US_STATES_ID[state]["id"]
        query = US_STATES_ID[state]["query"]
        return an.search_us(
            nomer=query.format(series),
            region=state_id,
            ctype=ctype_id,
        )

    @classmethod
    def get_series_us_url(cls, state, series):
        state_id, ctype_id = US_STATES_ID[state]["id"]
        query = US_STATES_ID[state]["query"].format(series)
        return Request(
            "GET",
            f"{an.AN_BASE_URL}/us/gallery.php",
            params={
                "gal": "us",
                "region": state_id,
                "ctype": ctype_id,
                "nomer": query,
            },
        ).prepare().url

    @classmethod
    def msg_no_results(cls, validated_query):
        state, series = validated_query.split()
        url = cls.get_series_us_url(state, series)
        state_name = US_STATES_ID[state]["name"]
        message = _("There are no plates in the series [{series}]({url}) of the state `{state_name}`")\
            .format(series=series, url=url, state_name=state_name)
        return message

    @classmethod
    def msg_with_results(cls, validated_query, result):
        state, series = validated_query.split()
        url = cls.get_series_us_url(state, series)
        cnt = result.total_results
        state_name = US_STATES_ID[state]["name"]
        message = _("Pictures in the series [{series}]({url}) of the state `{state_name}`: {cnt}")\
            .format(series=series, url=url, state_name=state_name, cnt=cnt)
        return message


US_PLATES = [
    UsSeriesInfoRequest,
]
