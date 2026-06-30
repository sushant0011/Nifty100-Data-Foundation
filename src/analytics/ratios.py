"""
ratios.py — Financial Ratio Engine for Nifty100 Analytics.

Covers:
  Day 08 — Profitability: NPM, OPM, ROE, ROCE, ROA
  Day 09 — Leverage & Efficiency: D/E, ICR, Net Debt, Asset Turnover

All functions:
  - Accept raw numeric values (float | int | None)
  - Return None on invalid denominator (div-by-zero / negative equity etc.)
  - Never raise exceptions — log warnings via loguru
  - Are pure functions (no DB / IO side-effects) for easy unit testing
"""

from typing import Optional
from src.utils.logger import logger


def net_profit_margin(net_profit, sales):
    if sales is None or sales == 0:
        return None
    if net_profit is None:
        return None
    return (net_profit / sales) * 100


def operating_profit_margin(operating_profit, sales, source_opm=None, ticker=""):
    if sales is None or sales == 0:
        return None
    if operating_profit is None:
        return None
    computed = (operating_profit / sales) * 100
    if source_opm is not None:
        diff = abs(computed - source_opm)
        if diff > 1.0:
            logger.warning(f"OPM mismatch [{ticker}]: computed={computed:.2f}% vs source={source_opm:.2f}%")
    return computed


def return_on_equity(net_profit, equity_capital, reserves):
    if net_profit is None or equity_capital is None or reserves is None:
        return None
    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None
    return (net_profit / total_equity) * 100


def return_on_capital_employed(ebit, equity_capital, reserves, borrowings, broad_sector=""):
    if any(v is None for v in [ebit, equity_capital, reserves, borrowings]):
        return None
    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        return None
    return (ebit / capital_employed) * 100


def return_on_assets(net_profit, total_assets):
    if total_assets is None or total_assets == 0:
        return None
    if net_profit is None:
        return None
    return (net_profit / total_assets) * 100


def debt_to_equity(borrowings, equity_capital, reserves, broad_sector=""):
    if equity_capital is None or reserves is None:
        return None, False
    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None, False
    if borrowings is None or borrowings == 0:
        return 0.0, False
    ratio = borrowings / total_equity
    is_financial = broad_sector.strip().lower() == "financials"
    high_flag = (ratio > 5) and (not is_financial)
    return ratio, high_flag


def interest_coverage_ratio(operating_profit, other_income, interest):
    if interest is None or interest == 0:
        return None, "Debt Free"
    if operating_profit is None or other_income is None:
        return None, "N/A"
    icr = (operating_profit + other_income) / interest
    label = "At Risk" if icr < 1.5 else "OK"
    return icr, label


def net_debt(borrowings, investments):
    if borrowings is None and investments is None:
        return None
    return (borrowings or 0.0) - (investments or 0.0)


def asset_turnover(sales, total_assets):
    if total_assets is None or total_assets == 0:
        return None
    if sales is None:
        return None
    return sales / total_assets