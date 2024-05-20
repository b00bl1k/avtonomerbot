import requests

from avbot import settings
from avbot.i18n import _


def get_vin_info(vin):
    headers = {"Authorization": f"Token {settings.VIN_PROVIDER_TOKEN}"}
    resp = requests.get(settings.VIN_PROVIDER_URL.format(vin=vin), headers=headers)
    return (
        resp.json()["result"]
        if resp.status_code == requests.codes.ok
        else None
    )


def format_msg(info):
    result = "{}: {}\n".format(_("Model"), info["model_name"])
    if info["plates"]:
        result += "{}: {}\n".format(_("License plate"), info["plates"][0]["number"].replace(" ", ""))
    result += "VIN: {}\n".format(info["vin"])
    if info["manufactured_year"]:
        result += "{}: {}\n".format(_("Manufactured year"), info["manufactured_year"])
    if info["engine_power"]:
        result += "{}: {} {}\n".format(_("Engine power"), info["engine_power"], _("hp"))
    if info["engine_displacement"]:
        result += "{}: {} {}\n".format(_("Engine displacement"), info["engine_displacement"], _("ccm"))
    if info["engine_num"]:
        result += "{}: {}\n".format(_("Engine number"), info["engine_num"])
    return result
