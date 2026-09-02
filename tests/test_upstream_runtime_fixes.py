import swisseph as swe
import pytest

from jhora import config, const, utils
from jhora.horoscope.main import Horoscope
from jhora.panchanga import drik


DATE = drik.Date(2000, 1, 1)
TIME = (17, 30, 0)
PLACE = drik.Place("Delhi", 28.6139, 77.2090, 5.5, elevation=0)
JD = utils.julian_day_number(DATE, TIME)


def test_planetary_positions_uses_dictionary_ids():
    positions = drik.planetary_positions(JD, PLACE)

    assert [row[0] for row in positions] == list(range(9))
    assert all(len(row) == 3 for row in positions)


def test_local_time_to_jdut1_preserves_seconds():
    at_zero = utils.local_time_to_jdut1(2000, 1, 1, 17, 30, 0, 5.5)
    at_59 = utils.local_time_to_jdut1(2000, 1, 1, 17, 30, 59, 5.5)

    assert at_59 > at_zero
    assert (at_59 - at_zero) * 86400 == pytest.approx(59, abs=0.001)


def test_config_updates_runtime_caches():
    config.initialize_runtime(force_reload=True, create_if_missing=False, silent=False)
    try:
        config.set_value("planet_position_type", True, apply=True, save=False)
        true_flags = drik.PLANET_FLAGS
        config.set_value("planet_position_type", False, apply=True, save=False)
        assert drik.PLANET_FLAGS != true_flags

        # Updating the topocentric flag must not require coordinates at config time.
        config.set_value("planet_position_reference_frame", False, apply=True, save=False)
        assert drik.PLANET_FLAGS & swe.FLG_TOPOCTR

        config.set_value("rise_set_use_refraction", False, apply=True, save=False)
        geometric_rise_flags = drik.RISE_FLAGS
        config.set_value("rise_set_use_refraction", True, apply=True, save=False)
        assert drik.RISE_FLAGS != geometric_rise_flags

        drik.set_ayanamsa_mode("TRUE_PUSHYA")
        true_pushya = drik.get_ayanamsa_value(JD)
        config.set_value("default_ayanamsa_mode", "LAHIRI", apply=True, save=False)
        assert const._DEFAULT_AYANAMSA_MODE == "LAHIRI"
        assert drik.get_ayanamsa_value(JD) != pytest.approx(true_pushya)

        config.set_value("include_uranus_to_pluto", False, apply=True, save=False)
        assert len(drik.planet_list) == 9
        config.set_value("include_uranus_to_pluto", True, apply=True, save=False)
        assert len(drik.planet_list) == 12
    finally:
        config.set_value("include_uranus_to_pluto", False, apply=True, save=False)
        config.set_value("rise_set_use_refraction", False, apply=True, save=False)
        config.set_value("planet_position_reference_frame", True, apply=True, save=False)
        config.set_value("planet_position_type", True, apply=True, save=False)
        config.set_value("default_ayanamsa_mode", "TRUE_PUSHYA", apply=True, save=False)


def test_horoscope_accepts_24_hour_and_12_hour_times():
    kwargs = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone_offset": 5.5,
        "date_in": DATE,
        "language": "en",
    }
    twenty_four_hour = Horoscope(birth_time="17:30:00", **kwargs)
    pm = Horoscope(birth_time="05:30:00 PM", **kwargs)
    noon = Horoscope(birth_time="12:00:00 PM", **kwargs)
    midnight = Horoscope(birth_time="12:00:00 AM", **kwargs)

    assert twenty_four_hour.birth_time == pm.birth_time == (17, 30, 0)
    assert twenty_four_hour.julian_day == pm.julian_day
    assert noon.birth_time == (12, 0, 0)
    assert midnight.birth_time == (0, 0, 0)


def test_horoscope_calendar_passes_place_to_weekday(monkeypatch):
    calls = []
    original_vaara = drik.vaara

    def recording_vaara(jd, place):
        calls.append(place)
        return original_vaara(jd, place)

    monkeypatch.setattr(drik, "vaara", recording_vaara)
    horoscope = Horoscope(
        latitude=28.6139,
        longitude=77.2090,
        timezone_offset=5.5,
        date_in=DATE,
        birth_time="17:30:00",
        language="en",
    )

    assert isinstance(horoscope.get_calendar_information(), dict)
    assert calls and calls[0].name == "Not Provided"


def test_horoscope_raises_value_error_for_missing_location():
    with pytest.raises(ValueError, match="latitude, longitude, and timezone_offset"):
        Horoscope(date_in=DATE, birth_time="17:30:00", language="en")


def test_true_lunar_year_method_is_honored(monkeypatch):
    monkeypatch.setattr(drik, "_true_tithi_year_same_phase", lambda *args: 111.0)
    monkeypatch.setattr(drik, "_true_tithi_year_boundary", lambda *args: 222.0)

    assert drik.dhasa_year_duration(
        const.DHASA_YEAR_DURATION.TRUE_LUNAR_YEAR,
        JD,
        PLACE,
        true_lunar_year_method=const.TRUE_LUNAR_YEAR_METHOD.TITHI_AT_DOB,
    ) == 111.0
    assert drik.dhasa_year_duration(
        const.DHASA_YEAR_DURATION.TRUE_LUNAR_YEAR,
        JD,
        PLACE,
        true_lunar_year_method=const.TRUE_LUNAR_YEAR_METHOD.TITHI_BOUNDARY,
    ) == 222.0
