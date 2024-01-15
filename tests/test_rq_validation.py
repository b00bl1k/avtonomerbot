from avbot.cmd import ru, su, ge, kz, uz


def test_validate_ru_car_license_plates():
    assert ru.RuVehicleRequest.validate("a123aa123")
    assert ru.RuVehicleRequest.validate("a123   aa 123")
    assert ru.RuVehicleRequest.validate("a123aa12")
    assert not ru.RuVehicleRequest.validate("a123aa1")
    assert not ru.RuVehicleRequest.validate("aaa123")


def test_validate_ru_trailer_license_plates():
    assert ru.RuTrailersRequest.validate("aa123457")
    assert ru.RuTrailersRequest.validate("aa 1234 57")
    assert not ru.RuTrailersRequest.validate("aaa 1234 57")


def test_validate_ru_special_license_plates():
    assert ru.RuSpecialVehiclesRequest.validate("1234ax50")
    assert ru.RuSpecialVehiclesRequest.validate("1234 ax17")
    assert not ru.RuSpecialVehiclesRequest.validate("1234 a 17")


def test_validate_ru_moto_license_plates():
    assert ru.RuMotorcyclesRequest.validate("1234ax77")
    assert not ru.RuMotorcyclesRequest.validate("1234ax177")
    assert not ru.RuMotorcyclesRequest.validate("123ax77")
    assert not ru.RuMotorcyclesRequest.validate("1234x77")


def test_validate_ru_transit_license_plates():
    assert ru.RuTransitRequest.validate("aa123a77")
    assert ru.RuTransitRequest.validate("ау123 a 77")
    assert not ru.RuTransitRequest.validate("ау123 77")


def test_validate_ru_pt_license_plates():
    assert ru.RuPublicTransportRequest.validate("ax12377")
    assert not ru.RuPublicTransportRequest.validate("ax123177")
    assert not ru.RuPublicTransportRequest.validate("a12399")


def test_validate_ru_plate_series():
    assert ru.RuSeriesInfoRequest.validate("aaa199")
    assert ru.RuSeriesInfoRequest.validate("aaa19")
    assert not ru.RuSeriesInfoRequest.validate("aa199")
    assert not ru.RuSeriesInfoRequest.validate("aaaa199")


def test_validate_ru_region_info():
    assert ru.RuRegionInfoRequest.validate("ru11")
    assert ru.RuRegionInfoRequest.validate("ru199")
    assert not ru.RuRegionInfoRequest.validate("su19")
    assert not ru.RuRegionInfoRequest.validate("ru1991")


def test_validate_su_private_vehicle_license_plates():
    assert su.SuVehicleRequest.validate("ж8028ХА")
    assert su.SuVehicleRequest.validate("ж 8028   ХА")
    assert su.SuVehicleRequest.validate("ж8028ха")
    assert su.SuVehicleRequest.validate("ж8028Н\u0406")
    assert not su.SuVehicleRequest.validate("ж8028Х")
    assert not su.SuVehicleRequest.validate("b8028ХА")


def test_validate_ge_vehicle_plates():
    assert ge.GeVehicles2014Request.validate("aa-123-aa")
    assert not ge.GeVehicles2014Request.validate("aa 123 aa")
    assert not ge.GeVehicles2014Request.validate("na-123-a")
    assert not ge.GeVehicles2014Request.validate("a-123-an")


def test_validate_kz_private_vehicle_plates():
    assert kz.KzPrivateVehicles2012Request.validate("123abc11")
    assert kz.KzPrivateVehicles2012Request.validate("456 def  01")
    assert not kz.KzPrivateVehicles2012Request.validate("45 def 01")
    assert not kz.KzPrivateVehicles2012Request.validate("456 de 01")
    assert not kz.KzPrivateVehicles2012Request.validate("456 def 1")


def test_validate_uz_private_vehicle_plates():
    assert uz.UzPrivateVehiclesRequest.validate("01a123bc")
    assert uz.UzPrivateVehiclesRequest.validate("01 a  123 bc")
    assert not uz.UzPrivateVehiclesRequest.validate("01 123bc")
    assert not uz.UzPrivateVehiclesRequest.validate("01 123aac")
