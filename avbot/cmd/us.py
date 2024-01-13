import re

from avbot import avtonomer as an
from avbot import tasks
from avbot.i18n import _, __
from avbot.cmd.base import PlateRequestBase, translate_to_latin, \
    translate_to_cyrillic


class UsSeriesInfoRequest(PlateRequestBase):
    num_type = "us"
    example = "ny xxx"
    description = __("info about state plate series (possible states: pa, oh, nc, ny)")
    task = tasks.an_listed_search

    @classmethod
    def validate(cls, query):
        res = re.match(
            r"^([a-z]{2})\s+([a-z]{3})$",
            query.lower(),
        )
        if res:
            state = res.groups()[0]
            if state in an.US_STATES_ID.keys():
                return " ".join(res.groups())

    @classmethod
    def search(cls, validated_query):
        state, series = validated_query.split()
        state_id, ctype_id = an.US_STATES_ID[state]
        return an.search_us(
            nomer="{} *".format(series),
            region=state_id,
            ctype=ctype_id,
        )

    @classmethod
    def msg_no_results(cls, validated_query):
        state, series = validated_query.split()
        state_id, ctype_id = an.US_STATES_ID[state]
        url = an.get_series_us_url(state_id, ctype_id, series)
        message = _("There are no plates in the series [{series}]({url}) of the state `{state}`")\
            .format(series=series, url=url, state=state)
        return message

    @classmethod
    def msg_with_results(cls, validated_query, result):
        state, series = validated_query.split()
        state_id, ctype_id = an.US_STATES_ID[state]
        url = an.get_series_us_url(state_id, ctype_id, series)
        cnt = result.total_results
        message = _("Pictures in the series [{series}]({url}) of the state `{state}`: {cnt}")\
            .format(series=series, url=url, state=state, cnt=cnt)
        return message


US_PLATES = [
    UsSeriesInfoRequest,
]
