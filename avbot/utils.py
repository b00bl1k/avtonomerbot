import re


def validate_vin(vin) -> str | None:
    vin = vin.upper()
    if re.match(r"^[0-9ABCDEFGHJKLMNPRSTUVWXYZ]{17}$", vin):
        return vin
