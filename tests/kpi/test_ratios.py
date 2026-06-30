"""
test_ratios.py — Unit tests for profitability & leverage ratio functions.
Day 08 + Day 09 tests.

Run: pytest tests/kpi/test_ratios.py -v
"""

import pytest
from src.analytics.ratios import (
    net_profit_margin, operating_profit_margin,
    return_on_equity, return_on_capital_employed,
    return_on_assets, debt_to_equity,
    interest_coverage_ratio, net_debt, asset_turnover,
)


class TestNetProfitMargin:

    def test_normal_case(self):
        assert net_profit_margin(200, 1000) == pytest.approx(20.0)

    def test_zero_sales_returns_none(self):
        assert net_profit_margin(200, 0) is None

    def test_none_sales_returns_none(self):
        assert net_profit_margin(200, None) is None

    def test_none_profit_returns_none(self):
        assert net_profit_margin(None, 1000) is None

    def test_negative_profit(self):
        assert net_profit_margin(-100, 1000) == pytest.approx(-10.0)


class TestOperatingProfitMargin:

    def test_normal_case(self):
        assert operating_profit_margin(300, 1000) == pytest.approx(30.0)

    def test_zero_sales_returns_none(self):
        assert operating_profit_margin(300, 0) is None

    def test_opm_crosscheck_no_warning(self):
        assert operating_profit_margin(300, 1000, source_opm=30.0) == pytest.approx(30.0)

    def test_opm_crosscheck_mismatch_returns_value(self):
        assert operating_profit_margin(300, 1000, source_opm=27.0, ticker="TEST") == pytest.approx(30.0)


class TestReturnOnEquity:

    def test_normal_case(self):
        assert return_on_equity(200, 100, 900) == pytest.approx(20.0)

    def test_zero_equity_returns_none(self):
        assert return_on_equity(200, 0, 0) is None

    def test_negative_equity_returns_none(self):
        assert return_on_equity(200, 100, -500) is None

    def test_negative_profit_works(self):
        assert return_on_equity(-100, 100, 900) == pytest.approx(-10.0)

    def test_none_input_returns_none(self):
        assert return_on_equity(None, 100, 900) is None


class TestReturnOnCapitalEmployed:

    def test_normal_case(self):
        assert return_on_capital_employed(300, 500, 500, 0) == pytest.approx(30.0)

    def test_zero_capital_employed_returns_none(self):
        assert return_on_capital_employed(300, 0, 0, 0) is None

    def test_financials_sector_returns_value(self):
        assert return_on_capital_employed(100, 50, 50, 900, broad_sector="Financials") is not None


class TestReturnOnAssets:

    def test_normal_case(self):
        assert return_on_assets(200, 2000) == pytest.approx(10.0)

    def test_zero_assets_returns_none(self):
        assert return_on_assets(200, 0) is None

    def test_none_assets_returns_none(self):
        assert return_on_assets(200, None) is None


class TestDebtToEquity:

    def test_normal_case(self):
        ratio, flag = debt_to_equity(500, 100, 400)
        assert ratio == pytest.approx(1.0)
        assert flag is False

    def test_debt_free_returns_zero(self):
        ratio, flag = debt_to_equity(0, 100, 900)
        assert ratio == 0.0
        assert flag is False

    def test_none_borrowings_returns_zero(self):
        ratio, flag = debt_to_equity(None, 100, 900)
        assert ratio == 0.0
        assert flag is False

    def test_negative_equity_returns_none(self):
        ratio, flag = debt_to_equity(500, 100, -600)
        assert ratio is None
        assert flag is False

    def test_high_leverage_flag_non_financial(self):
        ratio, flag = debt_to_equity(6000, 100, 900, broad_sector="Industrials")
        assert ratio == pytest.approx(6.0)
        assert flag is True

    def test_high_leverage_suppressed_for_financials(self):
        ratio, flag = debt_to_equity(6000, 100, 900, broad_sector="Financials")
        assert ratio == pytest.approx(6.0)
        assert flag is False


class TestInterestCoverageRatio:

    def test_normal_case(self):
        icr, label = interest_coverage_ratio(300, 50, 100)
        assert icr == pytest.approx(3.5)
        assert label == "OK"

    def test_zero_interest_returns_debt_free(self):
        icr, label = interest_coverage_ratio(300, 50, 0)
        assert icr is None
        assert label == "Debt Free"

    def test_none_interest_returns_debt_free(self):
        icr, label = interest_coverage_ratio(300, 50, None)
        assert icr is None
        assert label == "Debt Free"

    def test_icr_below_1_5_at_risk(self):
        icr, label = interest_coverage_ratio(100, 0, 100)
        assert icr == pytest.approx(1.0)
        assert label == "At Risk"


class TestNetDebt:

    def test_normal_case(self):
        assert net_debt(1000, 200) == pytest.approx(800.0)

    def test_negative_net_debt(self):
        assert net_debt(100, 500) == pytest.approx(-400.0)

    def test_zero_borrowings(self):
        assert net_debt(0, 300) == pytest.approx(-300.0)

    def test_both_none_returns_none(self):
        assert net_debt(None, None) is None


class TestAssetTurnover:

    def test_normal_case(self):
        assert asset_turnover(2000, 1000) == pytest.approx(2.0)

    def test_zero_assets_returns_none(self):
        assert asset_turnover(2000, 0) is None

    def test_none_sales_returns_none(self):
        assert asset_turnover(None, 1000) is None