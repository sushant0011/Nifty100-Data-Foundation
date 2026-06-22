import pandas as pd


def normalize_year(value):
    """
    Convert year values to integer.
    Returns None for invalid values.
    """
    if pd.isna(value):
        return None

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def normalize_ticker(value):
    """
    Normalize stock ticker.
    """
    if pd.isna(value):
        return None

    return str(value).strip().upper()