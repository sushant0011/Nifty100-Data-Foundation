"""
cashflow_kpis.py — Cash Flow KPIs & Capital Allocation Engine.

Day 11:
  - Free Cash Flow (FCF)
  - CFO Quality Score (5-year average CFO/PAT ratio)
  - CapEx Intensity classification
  - FCF Conversion Rate
  - Capital Allocation 8-pattern classifier
"""

import csv
from pathlib import Path
from typing import Optional
from src.utils.logger import logger

# ── Free Cash Flow ─────────────────────────────────────────
def free_cash_flow(cfo, cfi):
    if cfo is None and cfi is None:
        return None
    return (cfo or 0.0) + (cfi or 0.0)


# ── CFO Quality Score ──────────────────────────────────────
def cfo_quality_score(cfo_series, pat_series):
    if not cfo_series or not pat_series:
        return None, "N/A"
    ratios = []
    for cfo, pat in zip(cfo_series, pat_series):
        if cfo is None or pat is None or pat == 0:
            continue
        ratios.append(cfo / pat)
    if not ratios:
        return None, "N/A"
    avg = sum(ratios) / len(ratios)
    if avg >= 1.0:
        label = "High Quality"
    elif avg >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
    return avg, label


# ── CapEx Intensity ────────────────────────────────────────
def capex_intensity(investing_activity, sales):
    if sales is None or sales == 0:
        return None, "N/A"
    if investing_activity is None:
        return None, "N/A"
    intensity = abs(investing_activity) / sales * 100
    if intensity < 3:
        label = "Asset Light"
    elif intensity <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return intensity, label


# ── FCF Conversion Rate ────────────────────────────────────
def fcf_conversion_rate(fcf, operating_profit):
    if operating_profit is None or operating_profit == 0:
        return None
    if fcf is None:
        return None
    return (fcf / operating_profit) * 100


# ── Capital Allocation Classifier ─────────────────────────
CAPITAL_ALLOCATION_PATTERNS = {
    ("+", "-", "-"): "Reinvestor",
    ("+", "+", "-"): "Liquidating Assets",
    ("-", "+", "+"): "Distress Signal",
    ("-", "-", "+"): "Growth Funded by Debt",
    ("+", "+", "+"): "Cash Accumulator",
    ("-", "-", "-"): "Pre-Revenue",
    ("+", "-", "+"): "Mixed",
    ("-", "+", "-"): "Asset Monetiser",
}

def _sign(value):
    if value is None:
        return None
    return "+" if value >= 0 else "-"

def classify_capital_allocation(cfo, cfi, cff, cfo_pat_ratio=None):
    cs = _sign(cfo)
    ii = _sign(cfi)
    ff = _sign(cff)
    if cs is None or ii is None or ff is None:
        return cs or "?", ii or "?", ff or "?", "Unknown"
    label = CAPITAL_ALLOCATION_PATTERNS.get((cs, ii, ff), "Unknown")
    if label == "Reinvestor" and cfo_pat_ratio is not None and cfo_pat_ratio >= 1.5:
        label = "Shareholder Returns"
    return cs, ii, ff, label


# ── Generate Capital Allocation CSV ───────────────────────
def generate_capital_allocation_csv(rows, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"]
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            cs, ii, ff, label = classify_capital_allocation(
                cfo=row.get("cfo"),
                cfi=row.get("cfi"),
                cff=row.get("cff"),
                cfo_pat_ratio=row.get("cfo_pat_ratio"),
            )
            writer.writerow({
                "company_id": row["company_id"],
                "year": row["year"],
                "cfo_sign": cs,
                "cfi_sign": ii,
                "cff_sign": ff,
                "pattern_label": label,
            })
    logger.success(f"✅ Capital allocation CSV → {output_path} ({len(rows)} rows)")