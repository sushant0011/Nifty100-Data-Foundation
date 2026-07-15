"""
valuation.py — Valuation Module for Nifty100.

Day 26: Computes FCF yield, sector median P/E flags, and overvaluation labels.

Run: python -m src.analytics.valuation
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

from src.utils.config import cfg
from src.utils.logger import logger


OUTPUT_DIR = cfg.OUTPUT_DIR


def load_data(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load financial ratios and market cap data."""

    ratios = pd.read_sql_query("""
        SELECT fr.*, c.company_name, s.broad_sector
        FROM financial_ratios fr
        LEFT JOIN companies c ON c.id = fr.company_id
        LEFT JOIN sectors s ON s.company_id = fr.company_id
    """, conn)

    try:
        market_cap = pd.read_sql_query("""
            SELECT company_id, year, market_cap_crore
            FROM market_cap
        """, conn)
    except Exception as e:
        logger.warning(f"market_cap table issue: {e}")
        market_cap = pd.DataFrame()

    return ratios, market_cap


def get_latest_ratios(ratios: pd.DataFrame) -> pd.DataFrame:
    """Get latest year ratios per company."""
    return (
        ratios.sort_values("year")
        .groupby("company_id")
        .last()
        .reset_index()
    )


def compute_fcf_yield(df: pd.DataFrame,
                       market_cap: pd.DataFrame) -> pd.DataFrame:
    """
    FCF Yield = FCF / market_cap_crore x 100

    Merges latest market cap with latest ratios.
    """
    if market_cap.empty:
        logger.warning("No market cap data — FCF yield will be None")
        df["market_cap_crore"] = None
        df["fcf_yield_pct"] = None
        return df

    latest_mc = (
        market_cap.sort_values("year")
        .groupby("company_id")
        .last()
        .reset_index()[["company_id", "market_cap_crore"]]
    )

    df = df.merge(latest_mc, on="company_id", how="left")

    df["fcf_yield_pct"] = df.apply(
        lambda r: (r["free_cash_flow_cr"] / r["market_cap_crore"] * 100)
        if pd.notna(r.get("free_cash_flow_cr")) and pd.notna(r.get("market_cap_crore"))
        and r["market_cap_crore"] > 0
        else None,
        axis=1
    )

    return df


def compute_pe_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute sector median P/E and apply overvaluation flags.

    Since P/E is not directly in financial_ratios, we proxy using:
      P/E proxy = market_cap / net_profit (if available)

    Flags:
      Caution  — P/E > sector_median x 1.5
      Discount — P/E < sector_median x 0.7
      Fair     — otherwise
    """
    # Compute P/E proxy if market cap available
    if "market_cap_crore" in df.columns:
        df["pe_proxy"] = df.apply(
            lambda r: (r["market_cap_crore"] / r["earnings_per_share"])
            if pd.notna(r.get("market_cap_crore")) and pd.notna(r.get("earnings_per_share"))
            and r["earnings_per_share"] > 0
            else None,
            axis=1
        )
    else:
        df["pe_proxy"] = None

    # Sector median P/E
    sector_median_pe = (
        df.groupby("broad_sector")["pe_proxy"]
        .median()
        .reset_index()
        .rename(columns={"pe_proxy": "sector_median_pe"})
    )

    df = df.merge(sector_median_pe, on="broad_sector", how="left")

    # Apply flags
    def get_flag(row):
        pe = row.get("pe_proxy")
        median = row.get("sector_median_pe")
        if pe is None or median is None or pd.isna(pe) or pd.isna(median) or median == 0:
            return "Fair"
        if pe > median * 1.5:
            return "Caution"
        if pe < median * 0.7:
            return "Discount"
        return "Fair"

    df["flag"] = df.apply(get_flag, axis=1)

    # PE vs sector median %
    df["pe_vs_sector_median_pct"] = df.apply(
        lambda r: ((r["pe_proxy"] - r["sector_median_pe"]) / r["sector_median_pe"] * 100)
        if pd.notna(r.get("pe_proxy")) and pd.notna(r.get("sector_median_pe"))
        and r["sector_median_pe"] != 0
        else None,
        axis=1
    )

    return df


def generate_valuation_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build the final valuation_summary DataFrame with required columns."""

    output_cols = {
        "company_id": "company_id",
        "company_name": "company_name",
        "broad_sector": "sector",
        "pe_proxy": "PE",
        "book_value_per_share": "PB",
        "market_cap_crore": "market_cap_crore",
        "fcf_yield_pct": "FCF_yield_pct",
        "sector_median_pe": "5yr_median_PE",
        "pe_vs_sector_median_pct": "PE_vs_sector_median_pct",
        "flag": "flag",
    }

    available = {k: v for k, v in output_cols.items() if k in df.columns}
    summary = df[list(available.keys())].copy()
    summary = summary.rename(columns=available)

    # Round numeric columns
    for col in summary.select_dtypes(include=[float]).columns:
        summary[col] = summary[col].round(2)

    return summary


class ValuationEngine:

    def __init__(self):
        cfg.ensure_dirs()
        self.conn = sqlite3.connect(cfg.DB_PATH)

    def run(self):
        logger.info("=" * 60)
        logger.info("Valuation Engine - Starting Day 26")
        logger.info("=" * 60)

        ratios, market_cap = load_data(self.conn)
        self.conn.close()

        if ratios.empty:
            logger.error("No ratio data found — run ratio engine first")
            return

        logger.info(f"Loaded {len(ratios)} ratio rows")

        # Get latest year per company
        df = get_latest_ratios(ratios)
        logger.info(f"Latest ratios: {len(df)} companies")

        # FCF Yield
        df = compute_fcf_yield(df, market_cap)

        # P/E flags
        df = compute_pe_flags(df)

        # Generate summary
        summary = generate_valuation_summary(df)

        # Export valuation_summary.xlsx
        summary_path = OUTPUT_DIR / "valuation_summary.xlsx"
        summary.to_excel(summary_path, index=False)
        logger.success(f"valuation_summary.xlsx saved -> {summary_path} ({len(summary)} rows)")

        # Export valuation_flags.csv — only Caution and Discount
        if "flag" in summary.columns:
            flags_df = summary[summary["flag"].isin(["Caution", "Discount"])].copy()
            flags_path = OUTPUT_DIR / "valuation_flags.csv"
            flags_df.to_csv(flags_path, index=False)
            logger.success(f"valuation_flags.csv saved -> {flags_path} ({len(flags_df)} rows)")

        logger.info(f"Flag distribution:\n{df['flag'].value_counts().to_string()}")
        logger.success("Valuation Engine complete!")


if __name__ == "__main__":
    ValuationEngine().run()