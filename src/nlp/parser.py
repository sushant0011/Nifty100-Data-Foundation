"""
parser.py — NLP Analysis Text Parser for Nifty100.

Day 29: Parse text fields from analysis table using regex.
Extracts period and value from text like '10 Years: 21%'
"""

import re
import sqlite3
import pandas as pd
from pathlib import Path

from src.utils.config import cfg
from src.utils.logger import logger


OUTPUT_DIR = cfg.OUTPUT_DIR

REGEX_PATTERN = r'(\d+)\s*Years?:?\s*([\d.]+)%'

METRIC_COLUMNS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


def parse_analysis_text(text: str, company_id: str,
                         metric_type: str) -> list[dict]:
    """
    Parse text like '10 Years: 21%' and extract period and value.
    Returns list of dicts with company_id, metric_type, period_years, value_pct.
    """
    if not text or pd.isna(text):
        return []

    matches = re.findall(REGEX_PATTERN, str(text), re.IGNORECASE)
    results = []
    for period, value in matches:
        results.append({
            "company_id": company_id,
            "metric_type": metric_type,
            "period_years": int(period),
            "value_pct": float(value),
        })
    return results


def cross_validate_cagr(parsed_df: pd.DataFrame,
                          ratios_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cross-validate parsed CAGR values against computed CAGR from ratio engine.
    Flag divergence > 5% for manual review.
    """
    flags = []

    metric_map = {
        "compounded_sales_growth": "revenue_cagr_5yr",
        "compounded_profit_growth": "pat_cagr_5yr",
    }

    latest_ratios = (
        ratios_df.sort_values("year")
        .groupby("company_id")
        .last()
        .reset_index()
    )

    for _, row in parsed_df.iterrows():
        metric = row["metric_type"]
        if metric not in metric_map:
            continue
        if row["period_years"] != 5:
            continue

        ratio_col = metric_map[metric]
        company_id = row["company_id"]

        ratio_row = latest_ratios[latest_ratios["company_id"] == company_id]
        if ratio_row.empty:
            continue

        computed = ratio_row[ratio_col].values[0]
        parsed = row["value_pct"]

        if pd.isna(computed):
            continue

        diff = abs(computed - parsed)
        if diff > 5.0:
            flags.append({
                "company_id": company_id,
                "metric_type": metric,
                "period_years": row["period_years"],
                "parsed_value": parsed,
                "computed_value": round(computed, 2),
                "divergence_pct": round(diff, 2),
            })

    return pd.DataFrame(flags)


def run_parser():
    logger.info("=" * 60)
    logger.info("NLP Parser - Starting Day 29")
    logger.info("=" * 60)

    conn = sqlite3.connect(cfg.DB_PATH)

    # Load analysis table
    try:
        analysis = pd.read_sql_query("SELECT * FROM analysis", conn)
        logger.info(f"Loaded analysis table: {len(analysis)} rows")
    except Exception as e:
        logger.error(f"Failed to load analysis table: {e}")
        conn.close()
        return

    # Load ratios for cross-validation
    try:
        ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    except Exception:
        ratios = pd.DataFrame()

    conn.close()

    # Check available columns
    available_cols = [c for c in METRIC_COLUMNS if c in analysis.columns]
    logger.info(f"Available metric columns: {available_cols}")

    if not available_cols:
        logger.warning("No matching metric columns found in analysis table")
        logger.info(f"Available columns: {analysis.columns.tolist()}")

    # Parse all text fields
    parsed_rows = []
    failed_rows = []

    company_col = "company_id" if "company_id" in analysis.columns else "ticker"
    if company_col not in analysis.columns:
        company_col = analysis.columns[0]

    for _, row in analysis.iterrows():
        company_id = row.get(company_col, "UNKNOWN")

        for metric in available_cols:
            text = row.get(metric, "")
            results = parse_analysis_text(str(text), company_id, metric)

            if results:
                parsed_rows.extend(results)
            else:
                if text and str(text) not in ["nan", "None", ""]:
                    failed_rows.append({
                        "company_id": company_id,
                        "metric_type": metric,
                        "raw_text": str(text)[:200],
                    })

    # Save parsed CSV
    parsed_df = pd.DataFrame(parsed_rows)
    parsed_path = OUTPUT_DIR / "analysis_parsed.csv"
    if not parsed_df.empty:
        parsed_df.to_csv(parsed_path, index=False)
        logger.success(f"analysis_parsed.csv -> {parsed_path} ({len(parsed_df)} rows)")
    else:
        logger.warning("No data parsed — saving empty file")
        pd.DataFrame(columns=["company_id", "metric_type",
                               "period_years", "value_pct"]).to_csv(parsed_path, index=False)

    # Save parse failures
    failed_df = pd.DataFrame(failed_rows)
    failed_path = OUTPUT_DIR / "parse_failures.csv"
    failed_df.to_csv(failed_path, index=False)
    logger.info(f"parse_failures.csv -> {failed_path} ({len(failed_df)} rows)")

    # Cross-validate
    if not parsed_df.empty and not ratios.empty:
        flags_df = cross_validate_cagr(parsed_df, ratios)
        if not flags_df.empty:
            flags_path = OUTPUT_DIR / "cagr_divergence_flags.csv"
            flags_df.to_csv(flags_path, index=False)
            logger.warning(f"CAGR divergence flags -> {flags_path} ({len(flags_df)} rows)")
        else:
            logger.success("No CAGR divergence > 5% found")

    logger.success("NLP Parser complete!")


if __name__ == "__main__":
    run_parser()