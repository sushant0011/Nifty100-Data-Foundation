"""
test_cagr_cashflow.py — Unit tests for CAGR engine and Cash Flow KPIs.
Day 10 + Day 11 tests.

Run: pytest tests/kpi/test_cagr_cashflow.py -v
"""

import pytest
from src.analytics.cagr import (
    compute_cagr, compute_metric_cagr,
    FLAG_NORMAL, FLAG_DECLINE_TO_LOSS, FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE, FLAG_ZERO_BASE, FLAG_INSUFFICIENT,
)
from src.analytics.cashflow_kpis import (
    free_cash_flow, cfo_quality_score,
    capex_intensity, fcf_conversion_rate,
    classify_capital_allocation,
)


class TestComputeCAGR:

    def test_normal_cagr(self):
        cagr, flag = compute_cagr(1000, 1610.51, 5)
        assert cagr == pytest.approx(10.0, abs=0.01)
        assert flag == FLAG_NORMAL

    def test_flat_growth_zero_cagr(self):
        cagr, flag = compute_cagr(1000, 1000, 5)
        assert cagr == pytest.approx(0.0, abs=0.001)
        assert flag == FLAG_NORMAL

    def test_decline_to_loss(self):
        cagr, flag = compute_cagr(1000, -200, 5)
        assert cagr is None
        assert flag == FLAG_DECLINE_TO_LOSS

    def test_turnaround(self):
        cagr, flag = compute_cagr(-500, 800, 5)
        assert cagr is None
        assert flag == FLAG_TURNAROUND

    def test_both_negative(self):
        cagr, flag = compute_cagr(-500, -300, 5)
        assert cagr is None
        assert flag == FLAG_BOTH_NEGATIVE

    def test_zero_base(self):
        cagr, flag = compute_cagr(0, 1000, 5)
        assert cagr is None
        assert flag == FLAG_ZERO_BASE

    def test_none_start_insufficient(self):
        cagr, flag = compute_cagr(None, 1000, 5)
        assert cagr is None
        assert flag == FLAG_INSUFFICIENT

    def test_none_end_insufficient(self):
        cagr, flag = compute_cagr(1000, None, 5)
        assert cagr is None
        assert flag == FLAG_INSUFFICIENT

    def test_zero_n_years_insufficient(self):
        cagr, flag = compute_cagr(1000, 2000, 0)
        assert cagr is None
        assert flag == FLAG_INSUFFICIENT

    def test_single_year_cagr(self):
        cagr, flag = compute_cagr(1000, 1200, 1)
        assert cagr == pytest.approx(20.0, abs=0.001)
        assert flag == FLAG_NORMAL


class TestComputeMetricCAGR:

    def test_5yr_cagr_10pct(self):
        series = {y: 1000 * (1.10 ** (y - 2013)) for y in range(2013, 2024)}
        results = compute_metric_cagr(series, "revenue", windows=[5])
        cagr, flag = results["revenue_cagr_5yr"]
        assert cagr == pytest.approx(10.0, abs=0.05)
        assert flag == FLAG_NORMAL

    def test_insufficient_data(self):
        series = {2022: 1000, 2023: 1200}
        results = compute_metric_cagr(series, "revenue", windows=[5])
        cagr, flag = results["revenue_cagr_5yr"]
        assert cagr is None
        assert flag == FLAG_INSUFFICIENT

    def test_empty_series(self):
        results = compute_metric_cagr({}, "revenue", windows=[3, 5])
        for key, (val, flag) in results.items():
            assert val is None
            assert flag == FLAG_INSUFFICIENT


class TestFreeCashFlow:

    def test_normal_positive(self):
        assert free_cash_flow(500, -200) == pytest.approx(300.0)

    def test_negative_fcf_allowed(self):
        assert free_cash_flow(100, -500) == pytest.approx(-400.0)

    def test_both_none_returns_none(self):
        assert free_cash_flow(None, None) is None

    def test_one_none_treated_as_zero(self):
        assert free_cash_flow(500, None) == pytest.approx(500.0)


class TestCFOQualityScore:

    def test_high_quality(self):
        _, label = cfo_quality_score([120, 110, 130, 125, 115], [100]*5)
        assert label == "High Quality"

    def test_moderate(self):
        _, label = cfo_quality_score([70, 80, 60, 75, 65], [100]*5)
        assert label == "Moderate"

    def test_accrual_risk(self):
        _, label = cfo_quality_score([30, 40, 20, 35, 25], [100]*5)
        assert label == "Accrual Risk"

    def test_zero_pat_skipped(self):
        score, _ = cfo_quality_score([100, 0, 100], [100, 0, 100])
        assert score == pytest.approx(1.0, abs=0.01)


class TestCapexIntensity:

    def test_asset_light(self):
        pct, label = capex_intensity(-20, 1000)
        assert pct == pytest.approx(2.0)
        assert label == "Asset Light"

    def test_moderate(self):
        _, label = capex_intensity(-50, 1000)
        assert label == "Moderate"

    def test_capital_intensive(self):
        _, label = capex_intensity(-100, 1000)
        assert label == "Capital Intensive"

    def test_zero_sales_returns_none(self):
        pct, label = capex_intensity(-100, 0)
        assert pct is None
        assert label == "N/A"


class TestCapitalAllocationClassifier:

    def test_reinvestor(self):
        _, _, _, label = classify_capital_allocation(500, -300, -100)
        assert label == "Reinvestor"

    def test_distress_signal(self):
        _, _, _, label = classify_capital_allocation(-200, 300, 500)
        assert label == "Distress Signal"

    def test_growth_funded_by_debt(self):
        _, _, _, label = classify_capital_allocation(-100, -300, 500)
        assert label == "Growth Funded by Debt"

    def test_shareholder_returns(self):
        _, _, _, label = classify_capital_allocation(500, -300, -100, cfo_pat_ratio=2.0)
        assert label == "Shareholder Returns"

    def test_liquidating_assets(self):
        _, _, _, label = classify_capital_allocation(200, 300, -500)
        assert label == "Liquidating Assets"