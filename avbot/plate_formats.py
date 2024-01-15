from avbot import models
from avbot.cmd.base import PlateRequestBase
from avbot.cmd.ru import RU_PLATES
from avbot.cmd.su import SU_PLATES
from avbot.cmd.us import US_PLATES
from avbot.cmd.kz import KZ_PLATES
from avbot.cmd.uz import UZ_PLATES
from avbot.cmd.ge import GE_PLATES

PLATE_FORMATS = {
    models.Country.ru.value: RU_PLATES,
    models.Country.su.value: SU_PLATES,
    models.Country.ge.value: GE_PLATES,
    models.Country.kz.value: KZ_PLATES,
    models.Country.uz.value: UZ_PLATES,
    models.Country.us.value: US_PLATES,
}


def get_plate_format_by_type(num_type: str) -> PlateRequestBase | None:
    for country_code, plates in PLATE_FORMATS.items():
        for plate in plates:
            if plate.num_type == num_type:
                return plate
