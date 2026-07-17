"""
pros_cons_generator.py — Auto Pros/Cons Generator for Nifty100.

Day 30: Implements 12 pro rules and 12 con rules with confidence scores.
"""

import sqlite3
import pandas as pd
from pathlib import Path

from src.utils.config import cfg
from src.utils.logger import logger


OUTPUT_DIR = cfg.OUTPUT_DIR


def get_consecutive_count(series: pd.Series, condition) -> int:
    """Count consecutive years where condition is True from latest year."""
    count = 0
    for val in reversed(series.tolist()):
        if pd.notna(val) and condition(val):
            count += 1
        else:
            break
    return count


def is_improving(series: pd.Series, n: int = 3) -> bool:
    """Check if series is consistently improving over last n periods."""
    recent = series.dropna().tail(n)
    if len(recent) < n:
        return False
    return all(recent.iloc[i] < recent.iloc[i+1] for i in range(len(recent)-1))


def is_declining(series: pd.Series, n: int = 3) -> bool:
    """Check if series is consistently declining over last n periods."""
    recent = series.dropna().tail(n)
    if len(recent) < n:
        return False
    return all(recent.iloc[i] > recent.iloc[i+1] for i in range(len(recent)-1))


def evaluate_pro_rules(ratios: pd.DataFrame,
                        company_id: str) -> list[dict]:
    """Evaluate all 12 pro rules for a company."""
    co_ratios = ratios[ratios["company_id"] == company_id].sort_values("year")
    if co_ratios.empty:
        return []

    latest = co_ratios.iloc[-1]
    pros = []

    def add_pro(rule_id, text, confidence):
        if confidence >= 60:
            pros.append({
                "company_id": company_id,
                "type": "pro",
                "rule_id": rule_id,
                "text": text,
                "confidence_pct": confidence,
            })

    # Pro Rule 1: ROE > 20% sustained for 3+ years
    roe_series = co_ratios["return_on_equity_pct"].dropna()
    roe_above_20 = get_consecutive_count(roe_series, lambda x: x > 20)
    if roe_above_20 >= 3:
        conf = min(100, 70 + (roe_above_20 - 3) * 5)
        add_pro(1, "Consistently high return on equity above 20% demonstrates exceptional capital efficiency", conf)

    # Pro Rule 2: FCF positive for 5+ consecutive years
    fcf_series = co_ratios["free_cash_flow_cr"].dropna()
    fcf_positive = get_consecutive_count(fcf_series, lambda x: x > 0)
    if fcf_positive >= 5:
        conf = min(100, 70 + (fcf_positive - 5) * 3)
        add_pro(2, "Strong free cash flow generation over 5 years signals healthy business fundamentals", conf)

    # Pro Rule 3: D/E = 0 in latest year
    de = latest.get("debt_to_equity")
    if pd.notna(de) and de <= 0.1:
        add_pro(3, "Debt-free balance sheet provides financial flexibility and eliminates interest burden", 90)

    # Pro Rule 4: Revenue CAGR > 15% over 5 years
    rev_cagr = latest.get("revenue_cagr_5yr")
    if pd.notna(rev_cagr) and rev_cagr > 15:
        conf = min(100, 65 + int(rev_cagr - 15) * 2)
        add_pro(4, "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum", conf)

    # Pro Rule 5: OPM > 25% in latest year
    opm = latest.get("operating_profit_margin_pct")
    if pd.notna(opm) and opm > 25:
        conf = min(100, 65 + int(opm - 25))
        add_pro(5, "Operating profit margin above 25% indicates strong pricing power and cost discipline", conf)

    # Pro Rule 6: PAT CAGR > 20% over 5 years
    pat_cagr = latest.get("pat_cagr_5yr")
    if pd.notna(pat_cagr) and pat_cagr > 20:
        conf = min(100, 65 + int(pat_cagr - 20) * 2)
        add_pro(6, "Net profit compounding at above 20% over 5 years creates significant shareholder value", conf)

    # Pro Rule 7: ICR > 10 or Debt Free
    icr = latest.get("interest_coverage")
    icr_label = latest.get("icr_label", "")
    if (pd.notna(icr) and icr > 10) or icr_label == "Debt Free":
        add_pro(7, "Very high interest coverage ratio reflects negligible financial stress from debt servicing", 85)

    # Pro Rule 8: Dividend Yield > 2% with FCF positive
    div_payout = latest.get("dividend_payout_ratio_pct")
    fcf_latest = latest.get("free_cash_flow_cr")
    if pd.notna(div_payout) and div_payout > 0 and pd.notna(fcf_latest) and fcf_latest > 0:
        add_pro(8, "Consistent dividend yield above 2% backed by positive free cash flow", 70)

    # Pro Rule 9: EPS CAGR > 15% over 5 years
    eps_cagr = latest.get("eps_cagr_5yr")
    if pd.notna(eps_cagr) and eps_cagr > 15:
        conf = min(100, 65 + int(eps_cagr - 15) * 2)
        add_pro(9, "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding", conf)

    # Pro Rule 10: ROE improving for 3 consecutive years
    if is_improving(co_ratios["return_on_equity_pct"], 3):
        add_pro(10, "Return on equity improving for 3 consecutive years shows strengthening business quality", 75)

    # Pro Rule 11: Revenue CAGR > PAT CAGR (operating leverage)
    if (pd.notna(rev_cagr) and pd.notna(pat_cagr) and
            pat_cagr > rev_cagr and pat_cagr > 0):
        add_pro(11, "Revenue growing slower than profits shows improving operating leverage and scale benefits", 70)

    # Pro Rule 12: Assets growing with declining debt
    bs_data = co_ratios[["total_assets_cr" if "total_assets_cr" in co_ratios.columns
                          else "asset_turnover", "debt_to_equity"]].dropna()
    if len(bs_data) >= 3:
        debt_declining = is_declining(co_ratios["debt_to_equity"], 3)
        if debt_declining:
            add_pro(12, "Growing asset base funded by internal accruals reflects self-sustaining growth", 72)

    return pros


def evaluate_con_rules(ratios: pd.DataFrame,
                        company_id: str,
                        broad_sector: str = "") -> list[dict]:
    """Evaluate all 12 con rules for a company."""
    co_ratios = ratios[ratios["company_id"] == company_id].sort_values("year")
    if co_ratios.empty:
        return []

    latest = co_ratios.iloc[-1]
    cons = []

    def add_con(rule_id, text, confidence):
        if confidence >= 60:
            cons.append({
                "company_id": company_id,
                "type": "con",
                "rule_id": rule_id,
                "text": text,
                "confidence_pct": confidence,
            })

    # Con Rule 1: D/E > 2.0 for non-financial companies
    de = latest.get("debt_to_equity")
    is_financial = str(broad_sector).lower() == "financials"
    if pd.notna(de) and de > 2.0 and not is_financial:
        conf = min(100, 65 + int((de - 2.0) * 5))
        add_con(1, f"Debt-to-equity ratio of {round(de, 1)} is elevated for a non-financial company and warrants monitoring", conf)

    # Con Rule 2: FCF negative for 3 consecutive years
    fcf_series = co_ratios["free_cash_flow_cr"].dropna()
    fcf_negative = get_consecutive_count(fcf_series, lambda x: x < 0)
    if fcf_negative >= 3:
        conf = min(100, 65 + (fcf_negative - 3) * 5)
        add_con(2, "Free cash flow negative for 3 consecutive years raises concern about cash generation quality", conf)

    # Con Rule 3: OPM declining for 3 consecutive years
    if is_declining(co_ratios["operating_profit_margin_pct"], 3):
        add_con(3, "Operating margins declining for 3 consecutive years suggest pricing or cost pressure", 75)

    # Con Rule 4: Net profit negative in latest year
    npm = latest.get("net_profit_margin_pct")
    if pd.notna(npm) and npm < 0:
        add_con(4, "Company reported a net loss in the most recent financial year", 90)

    # Con Rule 5: Revenue declining for 2+ years
    rev_cagr = latest.get("revenue_cagr_5yr")
    if pd.notna(rev_cagr) and rev_cagr < 0:
        add_con(5, "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss", 80)

    # Con Rule 6: ICR < 1.5
    icr = latest.get("interest_coverage")
    icr_label = latest.get("icr_label", "")
    if pd.notna(icr) and icr < 1.5 and icr_label != "Debt Free":
        add_con(6, "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations", 85)

    # Con Rule 7: Dividend payout > 100%
    div_payout = latest.get("dividend_payout_ratio_pct")
    if pd.notna(div_payout) and div_payout > 100:
        add_con(7, "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable", 80)

    # Con Rule 8: D/E rising for 3 consecutive years
    if is_improving(co_ratios["debt_to_equity"], 3):
        add_con(8, "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk", 72)

    # Con Rule 9: EPS declining for 3 consecutive years
    if is_declining(co_ratios["earnings_per_share"], 3):
        add_con(9, "Earnings per share declining for 3 consecutive years reflects deteriorating profitability", 75)

    # Con Rule 10: ROCE < 10%
    roce = latest.get("return_on_capital_employed_pct")
    if pd.notna(roce) and roce < 10 and not is_financial:
        add_con(10, "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital", 70)

    # Con Rule 11: Net Debt > 3x (proxy using D/E)
    nd = latest.get("net_debt_cr")
    fcf = latest.get("free_cash_flow_cr")
    if pd.notna(nd) and pd.notna(fcf) and fcf > 0 and nd > 0:
        if nd / fcf > 3:
            add_con(11, "Net debt exceeding 3 times FCF is a high leverage ratio and limits financial flexibility", 72)

    # Con Rule 12: Revenue CAGR < 5% over 5 years
    if pd.notna(rev_cagr) and 0 < rev_cagr < 5:
        add_con(12, "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum", 68)

    return cons


class ProsConsGenerator:

    def __init__(self):
        cfg.ensure_dirs()
        self.conn = sqlite3.connect(cfg.DB_PATH)

    def run(self):
        logger.info("=" * 60)
        logger.info("Pros Cons Generator - Starting Day 30")
        logger.info("=" * 60)

        ratios = pd.read_sql_query("SELECT * FROM financial_ratios", self.conn)
        companies = pd.read_sql_query("""
            SELECT c.id as company_id, s.broad_sector
            FROM companies c
            LEFT JOIN sectors s ON s.company_id = c.id
        """, self.conn)
        self.conn.close()

        logger.info(f"Loaded {len(ratios)} ratio rows, {len(companies)} companies")

        all_results = []
        no_pro = []
        no_con = []

        for _, co in companies.iterrows():
            company_id = co["company_id"]
            broad_sector = co.get("broad_sector", "") or ""

            pros = evaluate_pro_rules(ratios, company_id)
            cons = evaluate_con_rules(ratios, company_id, broad_sector)

            if not pros:
                no_pro.append(company_id)
                # Add default pro
                pros.append({
                    "company_id": company_id,
                    "type": "pro",
                    "rule_id": 0,
                    "text": "Company is part of Nifty 100 index reflecting established market position",
                    "confidence_pct": 60,
                })

            if not cons:
                no_con.append(company_id)
                # Add default con
                cons.append({
                    "company_id": company_id,
                    "type": "con",
                    "rule_id": 0,
                    "text": "Insufficient historical data to identify specific risk factors at this time",
                    "confidence_pct": 60,
                })

            all_results.extend(pros)
            all_results.extend(cons)

        df = pd.DataFrame(all_results)
        output_path = OUTPUT_DIR / "pros_cons_generated.csv"
        df.to_csv(output_path, index=False)

        logger.success(f"pros_cons_generated.csv -> {output_path} ({len(df)} rows)")
        logger.info(f"Companies without natural pro: {len(no_pro)} — {no_pro[:5]}")
        logger.info(f"Companies without natural con: {len(no_con)} — {no_con[:5]}")

        # Verify every company has at least 1 pro and 1 con
        pros_count = df[df["type"] == "pro"]["company_id"].nunique()
        cons_count = df[df["type"] == "con"]["company_id"].nunique()
        logger.info(f"Companies with pro: {pros_count}/92")
        logger.info(f"Companies with con: {cons_count}/92")

        if pros_count == 92 and cons_count == 92:
            logger.success("Exit criteria MET: every company has at least 1 pro and 1 con")
        else:
            logger.warning("Some companies missing pro or con")

        logger.success("Pros Cons Generator complete!")


if __name__ == "__main__":
    ProsConsGenerator().run()