import pytest

from pyjhora_batch.wrapper import BirthRecord, RecordError


def test_valid_record(base_record_dict):
    rec = BirthRecord.from_dict(base_record_dict)
    assert rec.name == "Test Person"
    assert rec.date_of_birth == "1985,6,15"
    assert rec.time_of_birth == "10:30:00"
    assert rec.place_name == "Ujjain"
    assert rec.latitude == 23.5 and rec.longitude == 75.75 and rec.timezone == 5.5
    assert rec.gender == 1                 # "male" -> 1
    assert rec.elevation == 0.0            # default
    assert rec.chart_type == "south_indian" and rec.language == "English"


def test_column_aliases():
    rec = BirthRecord.from_dict({
        "dob": "2000,1,2", "tob": "06:07:08", "city": "X",
        "lat": "10.5", "lng": "20.25", "tz": "5.5",
    })
    assert rec.date_of_birth == "2000,1,2"
    assert rec.place_name == "X" and rec.latitude == 10.5 and rec.longitude == 20.25


def test_spaced_and_hyphen_headers():
    rec = BirthRecord.from_dict({
        "Date of Birth": "2000,1,2", "Time-of-Birth": "06:07:08",
        "Place": "Y", "Latitude": "1.0", "Longitude": "2.0", "Time Zone": "5.5",
    })
    assert rec.place_name == "Y" and rec.timezone == 5.5


@pytest.mark.parametrize("value,expected", [
    (0, 0), (1, 1), (2, 2), (3, 3),
    ("female", 0), ("MALE", 1), ("Trans", 2), ("no preference", 3), ("", 3),
])
def test_gender_normalization(base_record_dict, value, expected):
    base_record_dict["gender"] = value
    assert BirthRecord.from_dict(base_record_dict).gender == expected


def test_gender_boolean_rejected(base_record_dict):
    base_record_dict["gender"] = True
    with pytest.raises(RecordError):
        BirthRecord.from_dict(base_record_dict)


def test_gender_unknown_rejected(base_record_dict):
    base_record_dict["gender"] = "alien"
    with pytest.raises(RecordError):
        BirthRecord.from_dict(base_record_dict)


@pytest.mark.parametrize("missing", ["date_of_birth", "time_of_birth", "place_name",
                                     "latitude", "longitude", "timezone"])
def test_missing_required(base_record_dict, missing):
    del base_record_dict[missing]
    with pytest.raises(RecordError) as e:
        BirthRecord.from_dict(base_record_dict)
    assert missing in str(e.value)


@pytest.mark.parametrize("bad", ["1990-4-18", "1990/4/18", "Apr 18 1990", ""])
def test_bad_date_format(base_record_dict, bad):
    base_record_dict["date_of_birth"] = bad
    with pytest.raises(RecordError):
        BirthRecord.from_dict(base_record_dict)


@pytest.mark.parametrize("bad", ["3:04pm", "15-43-00", "noon", ""])
def test_bad_time_format(base_record_dict, bad):
    base_record_dict["time_of_birth"] = bad
    with pytest.raises(RecordError):
        BirthRecord.from_dict(base_record_dict)


@pytest.mark.parametrize("field,value", [
    ("latitude", 91), ("latitude", -91),
    ("longitude", 181), ("longitude", -181),
    ("timezone", 15), ("timezone", -15),
])
def test_out_of_range(base_record_dict, field, value):
    base_record_dict[field] = value
    with pytest.raises(RecordError):
        BirthRecord.from_dict(base_record_dict)


def test_non_numeric_coord(base_record_dict):
    base_record_dict["latitude"] = "north"
    with pytest.raises(RecordError):
        BirthRecord.from_dict(base_record_dict)


def test_from_dict_requires_dict():
    with pytest.raises(RecordError):
        BirthRecord.from_dict("not a dict")
