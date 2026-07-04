"""
engine.py — Screener Filter Engine for Nifty100.

Day 15: Load screener_config.yaml and apply threshold filters.
Day 16: 6 preset screeners.
Day 17: Composite quality score with P10/P90 winsorisation.
"""

import sqlite3
import yaml
import numpy as np
import pandas as pd
from pathlib import Path

from src.utils.config import cfg
from src.utils.logger import logger


CONFIG_PATH = Path("config/screener_config.yaml")
FINANCIALS_SECTOR = "financials"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def load_financial_ratios(year: int = None) -> pd.DataFrame:
    """Load financial_ratios table joined with sectors and companies."""
    conn = sqlite3.connect(cfg.DB_PATH)

    query = """
        SELECT
            fr.*,
            s.broad_sector,
            c.company_name
        FROM financial_ratios fr
        LEFT JOIN sectors s ON s.company_id = fr.company_id
        LEFT JOIN companies c ON c.id = fr.company_id
    """
    if year:
        query += f" WHERE fr.year = {year}"

    df = pd.read_sql_query(query, conn)
    conn.close()

    # Normalise sector name for comparison
    df["broad_sector_lower"] = df["broad_sector"].str.lower().fillna("")

    return df


def get_latest_year_df(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the latest year per company."""
    return df.sort_values("year").groupby("company_id").last().reset_index()


def winsorise(series: pd.Series, p_low: float = 10, p_high: float = 90) -> pd.Series:
    """Cap values at P10 and P90 percentiles."""
    low = np.nanpercentile(series.dropna(), p_low)
    high = np.nanpercentile(series.dropna(), p_high)
    return series.clip(lower=low, upper=high)


def scale_to_100(series: pd.Series) -> pd.Series:
    """Min-max scale a series to 0-100."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return (series - mn) / (mx - mn) * 100


def compute_composite_score(df: pd.DataFrame) -> pd.Series:
    """
    Composite Quality Score (0-100):
      35% Profitability  (ROE 15% + ROCE 10% + NPM 10%)
      30% Cash Quality   (FCF 15% + CFO/PAT 10% + FCF positive flag 5%)
      20% Growth         (Revenue CAGR 10% + PAT CAGR 10%)
      15% Leverage       (D/E inverse 10% + ICR 5%)
    """
    def safe_scale(col):
        if col not in df.columns:
            return pd.Series([0.0] * len(df), index=df.index)
        return scale_to_100(winsorise(df[col].fillna(df[col].median())))

    roe_s   = safe_scale("return_on_equity_pct")
    roce_s  = safe_scale("return_on_capital_employed_pct")
    npm_s   = safe_scale("net_profit_margin_pct")

    fcf_s   = safe_scale("free_cash_flow_cr")
    cfo_s   = safe_scale("cfo_quality_score")
    fcf_pos = (df["free_cash_flow_cr"].fillna(0) > 0).astype(float) * 100

    rev_s   = safe_scale("revenue_cagr_5yr")
    pat_s   = safe_scale("pat_cagr_5yr")

    # D/E: lower is better — invert
    de_inv = 100 - safe_scale("debt_to_equity")
    icr_s  = safe_scale("interest_coverage")

    score = (
        0.15 * roe_s  +
        0.10 * roce_s +
        0.10 * npm_s  +
        0.15 * fcf_s  +
        0.10 * cfo_s  +
        0.05 * fcf_pos +
        0.10 * rev_s  +
        0.10 * pat_s  +
        0.10 * de_inv +
        0.05 * icr_s
    )
    return score.round(2)


def apply_filters(df: pd.DataFrame, filters: dict,
                  config: dict, skip_de_for_financials: bool = True) -> pd.DataFrame:
    """Apply threshold filters from a preset to a DataFrame."""
    result = df.copy()
    metric_defs = config.get("metrics", {})

    for metric_key, threshold in filters.items():
        if metric_key not in metric_defs:
            logger.warning(f"Unknown metric: {metric_key}")
            continue

        meta = metric_defs[metric_key]
        col = meta["column"]
        op  = meta["operator"]

        if col not in result.columns:
            logger.warning(f"Column not found: {col} — skipping filter {metric_key}")
            continue

        # D/E filter: skip Financials sector companies
        if metric_key == "de_max" and skip_de_for_financials:
            financial_mask = result["broad_sector_lower"] == FINANCIALS_SECTOR
            non_financial = result[~financial_mask].copy()
            financial = result[financial_mask].copy()

            if op == "<=":
                non_financial = non_financial[
                    non_financial[col].fillna(float("inf")) <= threshold
                ]
            result = pd.concat([non_financial, financial], ignore_index=True)
            continue

        # ICR filter: treat Debt Free label as infinity
        if metric_key == "icr_min":
            icr_label_col = "icr_label"
            debt_free_mask = result.get(icr_label_col, pd.Series(dtype=str)) == "Debt Free"
            numeric_mask = ~debt_free_mask

            if op == ">=":
                passes = debt_free_mask | (
                    numeric_mask & (result[col].fillna(-float("inf")) >= threshold)
                )
            result = result[passes]
            continue

        # Standard filter
        if op == ">=":
            result = result[result[col].fillna(-float("inf")) >= threshold]
        elif op == "<=":
            result = result[result[col].fillna(float("inf")) <= threshold]
        elif op == ">":
            result = result[result[col].fillna(-float("inf")) > threshold]
        elif op == "<":
            result = result[result[col].fillna(float("inf")) < threshold]

    return result


class ScreenerEngine:

    def __init__(self):
        self.config = load_config()
        raw_df = load_financial_ratios()
        self.df = get_latest_year_df(raw_df)
        self.df["composite_quality_score"] = compute_composite_score(self.df)
        logger.info(f"Screener loaded: {len(self.df)} companies, year range {self.df['year'].min()}-{self.df['year'].max()}")

    def run_preset(self, preset_name: str) -> pd.DataFrame:
        """Run a named preset screener and return filtered DataFrame."""
        presets = self.config.get("presets", {})
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}")

        preset = presets[preset_name]
        filters = preset.get("filters", {})

        logger.info(f"Running preset: {preset['label']} ({len(filters)} filters)")
        result = apply_filters(self.df, filters, self.config)
        result = result.sort_values("composite_quality_score", ascending=False)

        logger.info(f"  Result: {len(result)} companies")
        return result

    def run_custom(self, filters: dict) -> pd.DataFrame:
        """Run a custom filter dict and return filtered DataFrame."""
        result = apply_filters(self.df, filters, self.config)
        result = result.sort_values("composite_quality_score", ascending=False)
        return result

    def run_all_presets(self) -> dict[str, pd.DataFrame]:
        """Run all 6 presets and return {preset_name: DataFrame}."""
        results = {}
        presets = self.config.get("presets", {})
        for name in presets:
            results[name] = self.run_preset(name)
        return results