"""
test_screener.py — Unit tests for Screener Engine & Peer Rankings.
Day 21 tests.

Run: pytest tests/screener/test_screener.py -v
"""

import pytest
import sqlite3
import pandas as pd
from pathlib import Path
from src.screener.engine import (
    ScreenerEngine, apply_filters, compute_composite_score,
    load_config, winsorise, scale_to_100
)
from src.analytics.peer import compute_peer_percentiles, percent_rank


# ════════════════════════════════════════════════════════════════════════════
# SCREENER ENGINE TESTS
# ════════════════════════════════════════════════════════════════════════════

class TestScreenerPresets:

    def setup_method(self):
        self.engine = ScreenerEngine()

    def test_quality_compounder_returns_valid_count(self):
        result = self.engine.run_preset("quality_compounder")
        assert 5 <= len(result) <= 50, f"Expected 5-50 companies, got {len(result)}"

    def test_quality_compounder_roe_above_threshold(self):
        result = self.engine.run_preset("quality_compounder")
        if "return_on_equity_pct" in result.columns:
            assert (result["return_on_equity_pct"] >= 15).all(), \
                "All Quality Compounder companies must have ROE >= 15%"

    def test_quality_compounder_de_below_threshold(self):
        result = self.engine.run_preset("quality_compounder")
        if "debt_to_equity" in result.columns:
            non_financial = result[result["broad_sector_lower"] != "financials"]
            assert (non_financial["debt_to_equity"] <= 1.0).all(), \
                "Non-financial companies must have D/E <= 1.0"

    def test_growth_accelerator_returns_valid_count(self):
        result = self.engine.run_preset("growth_accelerator")
        assert 5 <= len(result) <= 50, f"Expected 5-50 companies, got {len(result)}"

    def test_growth_accelerator_pat_cagr_above_threshold(self):
        result = self.engine.run_preset("growth_accelerator")
        if "pat_cagr_5yr" in result.columns:
            assert (result["pat_cagr_5yr"] >= 20).all(), \
                "All Growth Accelerator companies must have PAT CAGR >= 20%"

    def test_debt_free_blue_chip_returns_valid_count(self):
        result = self.engine.run_preset("debt_free_blue_chip")
        assert 5 <= len(result) <= 50, f"Expected 5-50 companies, got {len(result)}"

    def test_turnaround_watch_returns_valid_count(self):
        result = self.engine.run_preset("turnaround_watch")
        assert 5 <= len(result) <= 50, f"Expected 5-50 companies, got {len(result)}"

    def test_all_presets_return_dataframe(self):
        results = self.engine.run_all_presets()
        assert len(results) == 6, f"Expected 6 presets, got {len(results)}"
        for name, df in results.items():
            assert isinstance(df, pd.DataFrame), f"Preset {name} did not return DataFrame"

    def test_results_sorted_by_composite_score(self):
        result = self.engine.run_preset("quality_compounder")
        if len(result) > 1 and "composite_quality_score" in result.columns:
            scores = result["composite_quality_score"].tolist()
            assert scores == sorted(scores, reverse=True), \
                "Results must be sorted by composite_quality_score descending"

    def test_composite_score_range(self):
        result = self.engine.run_preset("quality_compounder")
        if "composite_quality_score" in result.columns:
            assert result["composite_quality_score"].between(0, 100).all(), \
                "Composite score must be between 0 and 100"


class TestFilterEngine:

    def setup_method(self):
        self.config = load_config()
        self.df = pd.DataFrame({
            "company_id": ["A", "B", "C", "D"],
            "return_on_equity_pct": [20, 10, 25, 5],
            "debt_to_equity": [0.5, 2.0, 0.8, 1.5],
            "free_cash_flow_cr": [100, -50, 200, 300],
            "revenue_cagr_5yr": [15, 8, 20, 12],
            "broad_sector_lower": ["it", "financials", "fmcg", "auto"],
            "broad_sector": ["IT", "Financials", "FMCG", "Auto"],
            "icr_label": ["OK", "OK", "Debt Free", "At Risk"],
            "interest_coverage": [5.0, 3.0, None, 1.0],
            "composite_quality_score": [80, 40, 90, 60],
        })

    def test_roe_filter(self):
        filters = {"roe_min": 15}
        result = apply_filters(self.df, filters, self.config)
        assert set(result["company_id"]) == {"A", "C"}

    def test_de_filter_skips_financials(self):
        filters = {"de_max": 1.0}
        result = apply_filters(self.df, filters, self.config)
        # Financials (B) should not be filtered out by D/E
        assert "B" in result["company_id"].values

    def test_fcf_filter(self):
        filters = {"fcf_min": 0}
        result = apply_filters(self.df, filters, self.config)
        assert "B" not in result["company_id"].values

    def test_icr_debt_free_passes_any_threshold(self):
        filters = {"icr_min": 10}
        result = apply_filters(self.df, filters, self.config)
        # C has Debt Free label — should always pass ICR filter
        assert "C" in result["company_id"].values

    def test_multiple_filters(self):
        filters = {"roe_min": 15, "fcf_min": 0}
        result = apply_filters(self.df, filters, self.config)
        assert set(result["company_id"]) == {"A", "C"}


class TestCompositeScore:

    def test_composite_score_returns_series(self):
        df = pd.DataFrame({
            "return_on_equity_pct": [20, 10, 30],
            "return_on_capital_employed_pct": [15, 8, 25],
            "net_profit_margin_pct": [12, 5, 18],
            "free_cash_flow_cr": [100, -50, 200],
            "cfo_quality_score": [1.2, 0.6, 1.5],
            "revenue_cagr_5yr": [15, 8, 20],
            "pat_cagr_5yr": [12, 5, 18],
            "debt_to_equity": [0.5, 2.0, 0.1],
            "interest_coverage": [8.0, 2.0, 15.0],
        })
        score = compute_composite_score(df)
        assert len(score) == 3
        assert score.between(0, 100).all()

    def test_higher_metrics_give_higher_score(self):
        df = pd.DataFrame({
            "return_on_equity_pct": [5, 30],
            "return_on_capital_employed_pct": [4, 25],
            "net_profit_margin_pct": [2, 20],
            "free_cash_flow_cr": [-100, 500],
            "cfo_quality_score": [0.3, 1.5],
            "revenue_cagr_5yr": [2, 20],
            "pat_cagr_5yr": [1, 18],
            "debt_to_equity": [3.0, 0.1],
            "interest_coverage": [1.0, 15.0],
        })
        score = compute_composite_score(df)
        assert score.iloc[1] > score.iloc[0], \
            "Better fundamentals company should have higher composite score"


# ════════════════════════════════════════════════════════════════════════════
# PEER RANKING TESTS
# ════════════════════════════════════════════════════════════════════════════

class TestPeerPercentiles:

    def test_percent_rank_basic(self):
        series = pd.Series([10, 20, 30, 40, 50])
        ranks = percent_rank(series)
        assert ranks.iloc[-1] == pytest.approx(1.0)
        assert ranks.iloc[0] == pytest.approx(0.2)

    def test_percent_rank_handles_nan(self):
        series = pd.Series([10, None, 30])
        ranks = percent_rank(series)
        assert pd.isna(ranks.iloc[1])

    def test_peer_percentiles_highest_roe_gets_highest_rank(self):
        peer_groups = pd.DataFrame({
            "company_id": ["TCS", "INFY", "HCLTECH", "LTIM", "TECHM"],
            "peer_group_name": ["IT Services"] * 5,
        })
        ratios = pd.DataFrame({
            "company_id": ["TCS", "INFY", "HCLTECH", "LTIM", "TECHM"],
            "return_on_equity_pct": [50, 30, 25, 20, 15],
            "return_on_capital_employed_pct": [40, 25, 20, 18, 12],
            "net_profit_margin_pct": [25, 20, 18, 15, 10],
            "debt_to_equity": [0.1, 0.2, 0.3, 0.4, 0.5],
            "free_cash_flow_cr": [5000, 3000, 2000, 1500, 800],
            "pat_cagr_5yr": [15, 12, 10, 8, 5],
            "revenue_cagr_5yr": [12, 10, 9, 8, 6],
            "eps_cagr_5yr": [14, 11, 9, 7, 4],
            "interest_coverage": [50, 30, 25, 20, 15],
            "asset_turnover": [0.8, 0.7, 0.75, 0.65, 0.6],
            "year": [2024] * 5,
        })
        rows = compute_peer_percentiles(peer_groups, ratios)
        roe_rows = [r for r in rows if r["metric"] == "return_on_equity_pct"]
        tcs_roe = next(r for r in roe_rows if r["company_id"] == "TCS")
        techm_roe = next(r for r in roe_rows if r["company_id"] == "TECHM")
        assert tcs_roe["percentile_rank"] > techm_roe["percentile_rank"], \
            "TCS with highest ROE should have highest ROE percentile rank in IT Services"

    def test_de_percentile_inverted(self):
        peer_groups = pd.DataFrame({
            "company_id": ["A", "B", "C"],
            "peer_group_name": ["TestGroup"] * 3,
        })
        ratios = pd.DataFrame({
            "company_id": ["A", "B", "C"],
            "return_on_equity_pct": [20, 15, 10],
            "return_on_capital_employed_pct": [15, 12, 8],
            "net_profit_margin_pct": [10, 8, 5],
            "debt_to_equity": [0.1, 1.0, 3.0],  # A has lowest D/E
            "free_cash_flow_cr": [100, 50, 20],
            "pat_cagr_5yr": [15, 10, 5],
            "revenue_cagr_5yr": [12, 8, 4],
            "eps_cagr_5yr": [14, 9, 3],
            "interest_coverage": [20, 10, 3],
            "asset_turnover": [1.5, 1.0, 0.5],
            "year": [2024] * 3,
        })
        rows = compute_peer_percentiles(peer_groups, ratios)
        de_rows = [r for r in rows if r["metric"] == "debt_to_equity"]
        a_de = next(r for r in de_rows if r["company_id"] == "A")
        c_de = next(r for r in de_rows if r["company_id"] == "C")
        assert a_de["percentile_rank"] > c_de["percentile_rank"], \
            "Company with lowest D/E should have highest D/E percentile rank (inverted)"