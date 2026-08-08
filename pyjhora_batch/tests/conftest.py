import os

# Force headless Qt before anything imports the wrapper (which creates a
# QApplication on demand). Belt-and-suspenders: the wrapper sets this too.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture
def base_record_dict():
    """A minimal valid raw record (dict) for the Ujjain reference chart."""
    return {
        "name": "Test Person",
        "date_of_birth": "1985,6,15",
        "time_of_birth": "10:30:00",
        "place_name": "Ujjain",
        "latitude": 23.5,
        "longitude": 75.75,
        "timezone": 5.5,
        "gender": "male",
    }
