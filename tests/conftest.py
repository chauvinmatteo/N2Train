from pathlib import Path

import pytest

from database import Database

CSV_PATH = Path(__file__).resolve().parent.parent / "n2_kanji.csv"


@pytest.fixture
def db(tmp_path):

    database = Database(tmp_path / "test.db")
    database.seed(CSV_PATH)
    yield database
    database.close()
