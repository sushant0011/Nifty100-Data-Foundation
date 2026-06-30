"""
cagr.py — CAGR Engine for Nifty100 Analytics.

Day 10: Computes Revenue, PAT, and EPS CAGRs for 3yr / 5yr / 10yr windows.

All 6 edge cases handled:
  NORMAL           — both start & end positive → compute normally
  DECLINE_TO_LOSS  — start positive, end negative → return None + flag
  TURNAROUND       — start negative, end positive → return None + flag
  BOTH_NEGATIVE    — start & end negative → return None + flag
  ZERO_BASE        — start == 0 → return None + flag
  INSUFFICIENT     — fewer than n years of data → return None + flag
"""

from typing import Optional
from src.utils.logger import logger

FLAG_NORMAL = "NORMAL"
FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
FLAG_TURNAROUND = "TURNAROUND"
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
FLAG_ZERO_BASE = "ZERO_BASE"
FLAG_INSUFFICIENT = "INSUFFICIENT"


def compute_cagr(start_value, end_value, n_years):
    if start_value is None or end_value is None or n_years < 1:
        return None, FLAG_INSUFFICIENT
    if start_value == 0:
        return None, FLAG_ZERO_BASE
    if start_value < 0 and end_value < 0:
        return None, FLAG_BOTH_NEGATIVE
    if start_value > 0 and end_value < 0:
        return None, FLAG_DECLINE_TO_LOSS
    if start_value < 0 and end_value > 0:
        return None, FLAG_TURNAROUND
    try:
        cagr = ((end_value / start_value) ** (1 / n_years) - 1) * 100
        return cagr, FLAG_NORMAL
    except Exception as e:
        logger.error(f"CAGR error: {e}")
        return None, FLAG_INSUFFICIENT


def _get_value_n_years_ago(series, latest_year, n):
    target = latest_year - n
    if target in series:
        return series[target], target
    for delta in [1, -1]:
        candidate = target + delta
        if candidate in series:
            return series[candidate], candidate
    return None, None


def compute_metric_cagr(series, metric_name, windows=[3, 5, 10]):
    if not series:
        return {f"{metric_name}_cagr_{w}yr": (None, FLAG_INSUFFICIENT) for w in windows}

    latest_year = max(series.keys())
    end_value = series.get(latest_year)

    results = {}
    for n in windows:
        key = f"{metric_name}_cagr_{n}yr"
        if len(series) < n + 1:
            results[key] = (None, FLAG_INSUFFICIENT)
            continue
        start_value, actual_year = _get_value_n_years_ago(series, latest_year, n)
        if start_value is None:
            results[key] = (None, FLAG_INSUFFICIENT)
            continue
        actual_n = latest_year - actual_year
        cagr, flag = compute_cagr(start_value, end_value, actual_n)
        results[key] = (cagr, flag)

    return results


def compute_all_cagrs(revenue_series, pat_series, eps_series, ticker=""):
    logger.debug(f"Computing CAGRs for [{ticker}]")
    results = {}
    results.update(compute_metric_cagr(revenue_series, "revenue"))
    results.update(compute_metric_cagr(pat_series, "pat"))
    results.update(compute_metric_cagr(eps_series, "eps"))
    return results