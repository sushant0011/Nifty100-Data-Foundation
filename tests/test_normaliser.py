from src.etl.normaliser import normalize_year, normalize_ticker


def test_normalize_year_integer():
    assert normalize_year(2024) == 2024


def test_normalize_year_float():
    assert normalize_year(2024.0) == 2024


def test_normalize_year_string():
    assert normalize_year("2024") == 2024


def test_normalize_year_invalid():
    assert normalize_year("abc") is None


def test_normalize_year_none():
    assert normalize_year(None) is None


def test_normalize_ticker_lowercase():
    assert normalize_ticker("tcs") == "TCS"


def test_normalize_ticker_spaces():
    assert normalize_ticker("  infy  ") == "INFY"


def test_normalize_ticker_none():
    assert normalize_ticker(None) is None