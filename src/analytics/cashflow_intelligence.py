"""
cashflow_intelligence.py — Cash Flow Intelligence Module for Nifty100.

Day 31: CFO Quality, CapEx Intensity, Distress Signal, Deleveraging flags.
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

from src.utils.config import cfg
from src.utils.logger import logger


OUTPUT_DIR = cfg.OUTPUT_DIR


def compute_cfo_quality(co_ratios: pd.DataFrame) -> tuple[float, str]:
    """CFO/PAT ratio averaged over 5 years."""
    recent = co_ratios.sort_values("year").tail(5)
    ratios = []
    for _, row in recent.iterrows():
        cfo = row.get("cash_from_operations_cr")
        npm = row.get("net_profit_margin_pct")
        sales = None
        if pd.notna(cfo) and pd.notna(npm) and npm != 0:
            ratios.append(cfo / npm if npm else None)
    valid = [r for r in ratios if r is not None]
    if not valid:
        return None, "N/A"
    avg = sum(valid) / len(valid)
    if avg >= 1.0:
        return round(avg, 2), "High Quality"
    elif avg >= 0.5:
        return round(avg, 2), "Moderate"
    else:
        return round(avg, 2), "Accrual Risk"


def compute_capex_intensity(co_ratios: pd.DataFrame) -> tuple[float, str]:
    """CapEx Intensity = abs(investing_activity) / sales x 100."""
    latest = co_ratios.sort_values("year").iloc[-1]
    capex = latest.get("capex_cr")
    sales_proxy = latest.get("asset_turnover")

    capex_pct = latest.get("capex_intensity_pct")
    capex_label = latest.get("capex_intensity_label", "")

    if pd.notna(capex_pct):
        return round(capex_pct, 2), capex_label or "N/A"
    return None, "N/A"


def detect_distress(co_cf: pd.DataFrame) -> bool:
    """
    Distress Signal: CFO < 0 AND CFF > 0 in latest year.
    Raising cash from financing while operations burn cash.
    """
    if co_cf.empty:
        return False
    latest = co_cf.sort_values("year").iloc[-1]
    cfo = latest.get("operating_activity")
    cff = latest.get("financing_activity")
    if pd.notna(cfo) and pd.notna(cff):
        return cfo < 0 and cff > 0
    return False


def detect_deleveraging(co_cf: pd.DataFrame,
                         co_bs: pd.DataFrame) -> bool:
    """
    Deleveraging: CFF < 0 AND borrowings declining year-over-year.
    Actively paying down debt.
    """
    if co_cf.empty or co_bs.empty:
        return False
    latest_cf = co_cf.sort_values("year").iloc[-1]
    cff = latest_cf.get("financing_activity")
    if pd.isna(cff) or cff >= 0:
        return False
    # Check borrowings declining
    bs_sorted = co_bs.sort_values("year")
    if len(bs_sorted) < 2:
        return False
    borr = bs_sorted["borrowings"].dropna()
    if len(borr) < 2:
        return False
    return borr.iloc[-1] < borr.iloc[-2]


def compute_fcf_cagr(co_ratios: pd.DataFrame) -> float:
    """Compute FCF CAGR over 5 years."""
    sorted_df = co_ratios.sort_values("year")
    fcf = sorted_df["free_cash_flow_cr"].dropna()
    if len(fcf) < 6:
        return None
    start = fcf.iloc[-6]
    end = fcf.iloc[-1]
    if start <= 0 or end <= 0:
        return None
    try:
        return round(((end / start) ** (1/5) - 1) * 100, 2)
    except Exception:
        return None


def compute_fcf_conversion(co_ratios: pd.DataFrame) -> float:
    """FCF Conversion = FCF / Operating Profit x 100."""
    latest = co_ratios.sort_values("year").iloc[-1]
    fcf = latest.get("free_cash_flow_cr")
    opm = latest.get("operating_profit_margin_pct")
    if pd.notna(fcf) and pd.notna(opm) and opm != 0:
        return round(fcf / opm, 2)
    return None


class CashFlowIntelligence:

    def __init__(self):
        cfg.ensure_dirs()
        self.conn = sqlite3.connect(cfg.DB_PATH)

    def run(self):
        logger.info("=" * 60)
        logger.info("Cash Flow Intelligence - Starting Day 31")
        logger.info("=" * 60)

        ratios = pd.read_sql_query("SELECT * FROM financial_ratios", self.conn)
        companies = pd.read_sql_query("""
            SELECT c.id as company_id, c.company_name, s.broad_sector
            FROM companies c
            LEFT JOIN sectors s ON s.company_id = c.id
        """, self.conn)

        try:
            cf_data = pd.read_sql_query("SELECT * FROM cashflow", self.conn)
        except Exception:
            cf_data = pd.DataFrame()

        try:
            bs_data = pd.read_sql_query("SELECT * FROM balancesheet", self.conn)
        except Exception:
            bs_data = pd.DataFrame()

        # Load capital allocation
        try:
            cap_alloc = pd.read_csv("output/capital_allocation.csv")
            latest_cap = (
                cap_alloc.sort_values("year")
                .groupby("company_id")
                .last()
                .reset_index()[["company_id", "pattern_label"]]
            )
        except Exception:
            latest_cap = pd.DataFrame(columns=["company_id", "pattern_label"])

        self.conn.close()

        results = []
        distress_alerts = []

        for _, co in companies.iterrows():
            company_id = co["company_id"]
            sector = co.get("broad_sector", "") or ""

            co_ratios = ratios[ratios["company_id"] == company_id].sort_values("year")
            co_cf = cf_data[cf_data["company_id"] == company_id] if not cf_data.empty else pd.DataFrame()
            co_bs = bs_data[bs_data["company_id"] == company_id] if not bs_data.empty else pd.DataFrame()

            if co_ratios.empty:
                continue

            latest = co_ratios.iloc[-1]

            cfo_score, cfo_label = compute_cfo_quality(co_ratios)
            capex_pct, capex_label = compute_capex_intensity(co_ratios)
            fcf_cagr = compute_fcf_cagr(co_ratios)
            fcf_conv = compute_fcf_conversion(co_ratios)
            distress = detect_distress(co_cf)
            deleveraging = detect_deleveraging(co_cf, co_bs)

            # Capital allocation label
            cap_row = latest_cap[latest_cap["company_id"] == company_id]
            cap_label = cap_row["pattern_label"].values[0] if not cap_row.empty else "Unknown"

            row = {
                "company_id": company_id,
                "company_name": co.get("company_name", ""),
                "sector": sector,
                "cfo_quality_score": cfo_score,
                "cfo_quality_label": cfo_label,
                "capex_intensity_pct": capex_pct,
                "capex_label": capex_label,
                "fcf_cagr_5yr": fcf_cagr,
                "fcf_conversion_pct": fcf_conv,
                "distress_flag": int(distress),
                "deleveraging_flag": int(deleveraging),
                "capital_allocation_label": cap_label,
            }
            results.append(row)

            if distress:
                cfo_val = None
                cff_val = None
                if not co_cf.empty:
                    latest_cf = co_cf.sort_values("year").iloc[-1]
                    cfo_val = latest_cf.get("operating_activity")
                    cff_val = latest_cf.get("financing_activity")
                distress_alerts.append({
                    "company_id": company_id,
                    "company_name": co.get("company_name", ""),
                    "sector": sector,
                    "cfo_value": cfo_val,
                    "cff_value": cff_val,
                    "latest_net_profit_margin": latest.get("net_profit_margin_pct"),
                })

        # Save cashflow_intelligence.xlsx
        df = pd.DataFrame(results)
        excel_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
        df.to_excel(excel_path, index=False)
        logger.success(f"cashflow_intelligence.xlsx -> {excel_path} ({len(df)} rows)")

        # Save distress_alerts.csv
        distress_df = pd.DataFrame(distress_alerts)
        distress_path = OUTPUT_DIR / "distress_alerts.csv"
        distress_df.to_csv(distress_path, index=False)
        logger.success(f"distress_alerts.csv -> {distress_path} ({len(distress_df)} companies flagged)")

        logger.info(f"Distress signals: {df['distress_flag'].sum()}")
        logger.info(f"Deleveraging: {df['deleveraging_flag'].sum()}")
        logger.success("Cash Flow Intelligence complete!")


if __name__ == "__main__":
    CashFlowIntelligence().run()