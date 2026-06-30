"""
ratio_engine.py — Full Ratio Engine Runner.
Day 12 + Day 13
"""

import sqlite3
import re
from pathlib import Path
from src.utils.config import cfg
from src.utils.logger import logger
from src.analytics.ratios import (
    net_profit_margin, operating_profit_margin,
    return_on_equity, return_on_capital_employed,
    return_on_assets, debt_to_equity,
    interest_coverage_ratio, net_debt, asset_turnover,
)
from src.analytics.cagr import compute_all_cagrs
from src.analytics.cashflow_kpis import (
    free_cash_flow, cfo_quality_score,
    capex_intensity, fcf_conversion_rate,
    classify_capital_allocation, generate_capital_allocation_csv,
)

EDGE_CASE_LOG = cfg.OUTPUT_DIR / "ratio_edge_cases.log"
CAPITAL_ALLOC_CSV = cfg.OUTPUT_DIR / "capital_allocation.csv"


def parse_year(year_str) -> int:
    """Convert various year formats to integer year.
    Handles: 'Mar 2014', 'Dec 2012', 'Mar-13', '2014', 2014, '2024.5'
    Rejects malformed entries like 'Mar 2016 9m' or 'Mar 2023 15' or 'TTM'.
    """
    if isinstance(year_str, int):
        return year_str
    if isinstance(year_str, float):
        return int(year_str)
    if year_str is None:
        return None
    s = str(year_str).strip()
    if s == 'TTM' or '9m' in s.lower():
        return None

    match = re.fullmatch(r'[A-Za-z]{3}\s+(\d{4})', s)
    if match:
        return int(match.group(1))

    match = re.fullmatch(r'[A-Za-z]{3}-(\d{2})', s)
    if match:
        yy = int(match.group(1))
        return 2000 + yy

    match = re.fullmatch(r'(\d{4})(\.\d+)?', s)
    if match:
        return int(match.group(1))

    return None


CREATE_RATIOS_TABLE = """
CREATE TABLE IF NOT EXISTS financial_ratios (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id                      TEXT NOT NULL,
    year                            INTEGER NOT NULL,
    net_profit_margin_pct           REAL,
    operating_profit_margin_pct     REAL,
    return_on_equity_pct            REAL,
    return_on_capital_employed_pct  REAL,
    return_on_assets_pct            REAL,
    debt_to_equity                  REAL,
    high_leverage_flag              INTEGER DEFAULT 0,
    interest_coverage               REAL,
    icr_label                       TEXT,
    net_debt_cr                     REAL,
    asset_turnover                  REAL,
    free_cash_flow_cr               REAL,
    capex_cr                        REAL,
    capex_intensity_pct             REAL,
    capex_intensity_label           TEXT,
    fcf_conversion_rate_pct         REAL,
    cfo_quality_score               REAL,
    cfo_quality_label               TEXT,
    earnings_per_share              REAL,
    book_value_per_share            REAL,
    dividend_payout_ratio_pct       REAL,
    total_debt_cr                   REAL,
    cash_from_operations_cr         REAL,
    revenue_cagr_3yr                REAL,
    revenue_cagr_3yr_flag           TEXT,
    revenue_cagr_5yr                REAL,
    revenue_cagr_5yr_flag           TEXT,
    revenue_cagr_10yr               REAL,
    revenue_cagr_10yr_flag          TEXT,
    pat_cagr_3yr                    REAL,
    pat_cagr_3yr_flag               TEXT,
    pat_cagr_5yr                    REAL,
    pat_cagr_5yr_flag               TEXT,
    pat_cagr_10yr                   REAL,
    pat_cagr_10yr_flag              TEXT,
    eps_cagr_3yr                    REAL,
    eps_cagr_3yr_flag               TEXT,
    eps_cagr_5yr                    REAL,
    eps_cagr_5yr_flag               TEXT,
    eps_cagr_10yr                   REAL,
    eps_cagr_10yr_flag              TEXT,
    composite_quality_score         REAL,
    UNIQUE(company_id, year)
)
"""


class RatioEngine:

    def __init__(self):
        cfg.ensure_dirs()
        self.conn = sqlite3.connect(cfg.DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._edge_log_lines = []
        self._capital_alloc_rows = []

    def _log_edge(self, company_id, year, kpi, computed, source, category, note=""):
        line = (
            f"[{category}] {company_id} | {year} | {kpi} | "
            f"computed={computed} | source={source} | {note}"
        )
        logger.warning(f"Edge case: {line}")
        self._edge_log_lines.append(line)

    def _build_series(self, rows, col):
        """Build {year_int: value} dict, parsing year strings like 'Mar 2014'."""
        result = {}
        for r in rows:
            yr = parse_year(r["year"])
            if yr is not None and r[col] is not None:
                try:
                    result[yr] = float(r[col])
                except (ValueError, TypeError):
                    pass
        return result

    def _composite_quality(self, roe, roce, npm, de, cfo_q):
        score = 0.0
        weight_total = 0
        if roe is not None:
            score += 25 if roe > 15 else (15 if roe > 8 else 0)
            weight_total += 25
        if roce is not None:
            score += 20 if roce > 12 else (10 if roce > 6 else 0)
            weight_total += 20
        if npm is not None:
            score += 20 if npm > 10 else (10 if npm > 5 else 0)
            weight_total += 20
        if de is not None:
            score += 20 if de < 1 else (10 if de < 2 else 0)
            weight_total += 20
        if cfo_q is not None:
            score += 15 if cfo_q >= 1.0 else (8 if cfo_q >= 0.5 else 0)
            weight_total += 15
        if weight_total == 0:
            return None
        return round((score / weight_total) * 100, 2)

    def _process_company(self, company_id, broad_sector, source_roce, source_roe):
        cur = self.conn.cursor()

        pnl = cur.execute(
            "SELECT year, sales, net_profit, operating_profit, "
            "other_income, interest, eps, dividend_payout "
            "FROM profitandloss WHERE company_id=? ORDER BY year",
            (company_id,)
        ).fetchall()

        bs = cur.execute(
            "SELECT year, equity_capital, reserves, borrowings, "
            "total_assets, investments "
            "FROM balancesheet WHERE company_id=? ORDER BY year",
            (company_id,)
        ).fetchall()

        cf = cur.execute(
            "SELECT year, operating_activity, investing_activity, financing_activity "
            "FROM cashflow WHERE company_id=? ORDER BY year",
            (company_id,)
        ).fetchall()

        def build_year_dict(rows):
            """Build {year: row} dict. Prefer 'Mar' (fiscal year-end) entries
            over other months (Sep, Jun, Dec) when the same year appears twice."""
            result = {}
            for r in rows:
                yr = parse_year(r["year"])
                if yr is None:
                    continue
                year_str = str(r["year"]).strip()
                is_march = year_str.startswith("Mar")
                if yr not in result:
                    result[yr] = r
                elif is_march:
                    result[yr] = r
            return result

        pnl_by_year = build_year_dict(pnl)
        bs_by_year  = build_year_dict(bs)
        cf_by_year  = build_year_dict(cf)

        all_years = sorted(set(pnl_by_year) | set(bs_by_year) | set(cf_by_year))

        if not all_years:
            return []

        rev_series = self._build_series(pnl, "sales")
        pat_series = self._build_series(pnl, "net_profit")
        eps_series = self._build_series(pnl, "eps")

        cfo_list = [cf_by_year[y]["operating_activity"] for y in all_years if y in cf_by_year]
        pat_list = [pnl_by_year[y]["net_profit"] for y in all_years if y in pnl_by_year]

        all_cagrs = compute_all_cagrs(rev_series, pat_series, eps_series, ticker=company_id)
        cfo_q_val, cfo_q_label = cfo_quality_score(cfo_list[-5:], pat_list[-5:])

        output_rows = []

        for year in all_years:
            p = pnl_by_year.get(year)
            b = bs_by_year.get(year)
            c = cf_by_year.get(year)

            def pv(col):
                try:
                    return float(p[col]) if p and p[col] is not None else None
                except (ValueError, TypeError):
                    return None

            def bv(col):
                try:
                    return float(b[col]) if b and b[col] is not None else None
                except (ValueError, TypeError):
                    return None

            def cv(col):
                try:
                    return float(c[col]) if c and c[col] is not None else None
                except (ValueError, TypeError):
                    return None

            sales      = pv("sales")
            net_profit = pv("net_profit")
            op_profit  = pv("operating_profit")
            other_inc  = pv("other_income")
            interest   = pv("interest")
            eps        = pv("eps")
            dividends  = pv("dividend_payout")

            equity_cap   = bv("equity_capital")
            reserves     = bv("reserves")
            borrowings   = bv("borrowings")
            total_assets = bv("total_assets")
            investments  = bv("investments")

            cfo = cv("operating_activity")
            cfi = cv("investing_activity")
            cff = cv("financing_activity")

            ebit = (op_profit or 0) + (other_inc or 0) if op_profit is not None else None

            npm  = net_profit_margin(net_profit, sales)
            opm  = operating_profit_margin(op_profit, sales, ticker=str(company_id))
            roe  = return_on_equity(net_profit, equity_cap, reserves)
            roce = return_on_capital_employed(ebit, equity_cap, reserves, borrowings, broad_sector)
            roa  = return_on_assets(net_profit, total_assets)

            de_ratio, high_lev = debt_to_equity(borrowings, equity_cap, reserves, broad_sector)
            icr_val, icr_label = interest_coverage_ratio(op_profit, other_inc, interest)
            nd = net_debt(borrowings, investments)
            at = asset_turnover(sales, total_assets)

            fcf      = free_cash_flow(cfo, cfi)
            cap_pct, cap_label = capex_intensity(cfi, sales)
            fcf_conv = fcf_conversion_rate(fcf, op_profit)

            bvps = None
            if equity_cap and equity_cap > 0 and reserves is not None:
                bvps = (equity_cap + reserves) / equity_cap

            div_payout = None
            if net_profit and net_profit > 0 and dividends is not None:
                div_payout = (dividends / net_profit) * 100

            cs, ii, ff, pattern = classify_capital_allocation(
                cfo, cfi, cff,
                cfo_pat_ratio=(cfo / net_profit) if (cfo and net_profit and net_profit != 0) else None
            )
            self._capital_alloc_rows.append({
                "company_id": company_id, "year": year,
                "cfo": cfo, "cfi": cfi, "cff": cff,
                "cfo_pat_ratio": (cfo / net_profit) if (cfo and net_profit and net_profit != 0) else None
            })

            cqs = self._composite_quality(roe, roce, npm, de_ratio, cfo_q_val)

            latest_year = max(all_years)
            if year == latest_year:
                if source_roce is not None and roce is not None:
                    try:
                        if abs(roce - float(source_roce)) > 5.0:
                            self._log_edge(company_id, year, "ROCE", roce, source_roce,
                                           "FORMULA_DISCREPANCY", "diff > 5%")
                    except (ValueError, TypeError):
                        pass
                if source_roe is not None and roe is not None:
                    try:
                        if abs(roe - float(source_roe)) > 10.0:
                            self._log_edge(company_id, year, "ROE", roe, source_roe,
                                           "DATA_SOURCE_ISSUE", "source may be anomalous")
                    except (ValueError, TypeError):
                        pass

            def cv2(key): return all_cagrs.get(key, (None, None))[0]
            def cf2(key): return all_cagrs.get(key, (None, None))[1]

            row = {
                "company_id": company_id,
                "year": year,
                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe,
                "return_on_capital_employed_pct": roce,
                "return_on_assets_pct": roa,
                "debt_to_equity": de_ratio,
                "high_leverage_flag": int(high_lev),
                "interest_coverage": icr_val,
                "icr_label": icr_label,
                "net_debt_cr": nd,
                "asset_turnover": at,
                "free_cash_flow_cr": fcf,
                "capex_cr": cfi,
                "capex_intensity_pct": cap_pct,
                "capex_intensity_label": cap_label,
                "fcf_conversion_rate_pct": fcf_conv,
                "cfo_quality_score": cfo_q_val,
                "cfo_quality_label": cfo_q_label,
                "earnings_per_share": eps,
                "book_value_per_share": bvps,
                "dividend_payout_ratio_pct": div_payout,
                "total_debt_cr": borrowings,
                "cash_from_operations_cr": cfo,
                "revenue_cagr_3yr": cv2("revenue_cagr_3yr"),
                "revenue_cagr_3yr_flag": cf2("revenue_cagr_3yr"),
                "revenue_cagr_5yr": cv2("revenue_cagr_5yr"),
                "revenue_cagr_5yr_flag": cf2("revenue_cagr_5yr"),
                "revenue_cagr_10yr": cv2("revenue_cagr_10yr"),
                "revenue_cagr_10yr_flag": cf2("revenue_cagr_10yr"),
                "pat_cagr_3yr": cv2("pat_cagr_3yr"),
                "pat_cagr_3yr_flag": cf2("pat_cagr_3yr"),
                "pat_cagr_5yr": cv2("pat_cagr_5yr"),
                "pat_cagr_5yr_flag": cf2("pat_cagr_5yr"),
                "pat_cagr_10yr": cv2("pat_cagr_10yr"),
                "pat_cagr_10yr_flag": cf2("pat_cagr_10yr"),
                "eps_cagr_3yr": cv2("eps_cagr_3yr"),
                "eps_cagr_3yr_flag": cf2("eps_cagr_3yr"),
                "eps_cagr_5yr": cv2("eps_cagr_5yr"),
                "eps_cagr_5yr_flag": cf2("eps_cagr_5yr"),
                "eps_cagr_10yr": cv2("eps_cagr_10yr"),
                "eps_cagr_10yr_flag": cf2("eps_cagr_10yr"),
                "composite_quality_score": cqs,
            }
            output_rows.append(row)

        return output_rows

    def run(self):
        logger.info("=" * 60)
        logger.info("Ratio Engine - Starting Sprint 2")
        logger.info("=" * 60)

        self.conn.execute("DROP TABLE IF EXISTS financial_ratios")
        self.conn.execute(CREATE_RATIOS_TABLE)
        self.conn.commit()

        companies = self.conn.execute("""
            SELECT c.id as company_id, c.roce_percentage, c.roe_percentage,
                   COALESCE(s.broad_sector, '') as broad_sector
            FROM companies c
            LEFT JOIN sectors s ON s.company_id = c.id
            GROUP BY c.id
        """).fetchall()

        if not companies:
            logger.warning("No companies found - run load first!")
            return

        all_rows = []
        for co in companies:
            logger.info(f"  Processing [{co['company_id']}]")
            try:
                rows = self._process_company(
                    co["company_id"],
                    co["broad_sector"] or "",
                    co["roce_percentage"],
                    co["roe_percentage"]
                )
                all_rows.extend(rows)
            except Exception as e:
                logger.error(f"  Failed [{co['company_id']}]: {e}")

        if all_rows:
            cols = list(all_rows[0].keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            self.conn.executemany(
                f"INSERT OR REPLACE INTO financial_ratios ({col_names}) VALUES ({placeholders})",
                [tuple(r[c] for c in cols) for r in all_rows]
            )
            self.conn.commit()

        count = self.conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
        logger.info(f"financial_ratios rows: {count}")
        if count >= 1100:
            logger.success(f"Exit criteria MET: {count} rows >= 1,100")
        else:
            logger.warning(f"Only {count} rows - check source data")

        generate_capital_allocation_csv(self._capital_alloc_rows, CAPITAL_ALLOC_CSV)
        self._write_edge_log()
        self.conn.close()
        logger.success("Ratio Engine complete!")

    def _write_edge_log(self):
        EDGE_CASE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(EDGE_CASE_LOG, "w") as f:
            f.write("# Nifty100 Ratio Engine - Edge Case Log\n")
            f.write("# [CATEGORY] company | year | kpi | computed | source | note\n\n")
            if self._edge_log_lines:
                f.write("\n".join(self._edge_log_lines) + "\n")
            else:
                f.write("# No anomalies detected.\n")
        logger.success(f"Edge log -> {EDGE_CASE_LOG} ({len(self._edge_log_lines)} entries)")


if __name__ == "__main__":
    RatioEngine().run()