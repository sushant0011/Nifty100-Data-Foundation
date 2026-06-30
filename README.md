# Nifty100 Data Foundation

> Financial Intelligence System for India's Top 100 Listed Companies

![Python](https://img.shields.io/badge/Python-3.12-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Tests](https://img.shields.io/badge/Tests-118%20passed-brightgreen)
![Sprint](https://img.shields.io/badge/Sprint%202-Complete-success)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

Nifty100 Data Foundation is a production-grade ETL and analytics pipeline that extracts financial data from 12 Excel source files, validates it against 16 Data Quality rules, loads it into a structured SQLite database, and computes 50+ financial KPIs across all available years for India's top 100 listed companies.

---

## Sprint 1 - Data Foundation (Complete)

| Day    | Task                                                    | Status |
|--------|---------------------------------------------------------|--------|
| Day 01 | Environment Setup - venv, libs, Makefile                | Done   |
| Day 02 | Excel Loader & Normaliser - 12 files, 35+ tests         | Done   |
| Day 03 | Schema Validator - 16 DQ Rules (CRITICAL + WARNING)     | Done   |
| Day 04 | SQLite Database Schema - 12 tables, PK/FK               | Done   |
| Day 05 | Full Data Load - 13,871 rows, 0 FK violations           | Done   |
| Day 06 | Data Quality Manual Review - 5 companies verified       | Done   |
| Day 07 | Sprint Wrap-up - Reports, Charts, Analytics             | Done   |

---

## Sprint 2 - Financial Ratio Engine (Complete)

| Day    | Task                                                          | Status |
|--------|----------------------------------------------------------------|--------|
| Day 08 | Profitability Ratios - NPM, OPM, ROE, ROCE, ROA                | Done   |
| Day 09 | Leverage & Efficiency - D/E, ICR, Net Debt, Asset Turnover      | Done   |
| Day 10 | CAGR Engine - Revenue/PAT/EPS, 6 edge cases handled             | Done   |
| Day 11 | Cash Flow KPIs - FCF, CFO Quality, CapEx, 8-pattern Allocator   | Done   |
| Day 12 | Populate financial_ratios Table - 92 companies, 14+ KPIs        | Done   |
| Day 13 | Bank ROCE Carve-Out & Edge Case Log                             | Done   |
| Day 14 | 67 KPI Unit Tests + Manual Spot-Check (0% diff)                 | Done   |

### Sprint 2 Exit Criteria

- [x] financial_ratios table populated - 1,073 rows, 92/92 companies covered
- [x] All 14 KPI columns populated, zero null-only columns
- [x] 67 KPI formula unit tests pass, 0 failures
- [x] ratio_edge_cases.log - 47 documented anomalies (FORMULA_DISCREPANCY, DATA_SOURCE_ISSUE)
- [x] Manual spot-check: ROE and Revenue 5yr CAGR for RELIANCE match exactly (0.000% diff)
- [x] Screener preview: ROE>15% and D/E<1 returns 34 companies (within 15-50 range)
- [x] Sprint 2 review completed

**Note:** Row count (1,073) is below the original 1,100 target due to inconsistent fiscal-year coverage across source files (some companies have fewer historical years available than others). All gaps are non-blocking data quality observations, not pipeline defects, and are documented in `output/ratio_edge_cases.log`.

---

## Database Stats

| Table            | Rows   | Description             |
|------------------|--------|-------------------------|
| companies        | 92     | Master company data     |
| profitandloss    | 1,276  | P&L statements          |
| balancesheet     | 1,312  | Balance sheets          |
| cashflow         | 1,187  | Cash flow statements    |
| analysis         | 20     | Growth analysis         |
| documents        | 1,585  | Annual reports          |
| financial_ratios | 1,073  | Computed KPIs (Sprint 2)|
| market_cap       | 552    | Market cap history      |
| peer_groups      | 56     | Peer group mappings     |
| prosandcons      | 16     | Pros & cons             |
| sectors          | 92     | Sector classifications  |
| stock_prices     | 5,520  | Historical stock prices |
| **Total**        | **13,760** |                     |

---

## Project Structure
Nifty100_Data_Foundation/

|

|-- data/

|   |-- raw/                  # 12 source Excel files

|   |-- processed/            # Cleaned CSVs

|   -- backup/               # Backups | |-- db/ |   |-- schema.sql            # 12-table SQLite schema |   -- nifty100.db           # SQLite database

|

|-- src/

|   |-- etl/

|   |   |-- loader.py         # Excel -> SQLite loader

|   |   |-- normaliser.py     # normalise_year() + normalise_ticker()

|   |   -- validator.py      # 16 DQ rules |   |-- analytics/ |   |   |-- ratios.py         # NPM, OPM, ROE, ROCE, ROA, D/E, ICR, Asset Turnover |   |   |-- cagr.py           # Revenue/PAT/EPS CAGR engine, 6 edge cases |   |   |-- cashflow_kpis.py  # FCF, CFO Quality, CapEx Intensity, Capital Allocator |   |   -- ratio_engine.py   # Full KPI runner -> financial_ratios table

|   |-- utils/

|   |   |-- config.py         # Central config (.env based)

|   |   -- logger.py         # Loguru logging |   -- main.py

|

|-- tests/

|   |-- etl/

|   |   |-- test_loader.py        # Loader unit tests

|   |   -- test_normaliser.py    # Normaliser unit tests |   -- kpi/

|       |-- test_ratios.py        # 36 profitability/leverage ratio tests

|       -- test_cagr_cashflow.py # 31 CAGR + cash flow KPI tests | |-- output/ |   |-- load_audit.csv            # Per-table row counts |   |-- validation_failures.csv   # DQ violations with severity |   |-- final_report.txt          # Sprint 1 wrap-up report |   |-- analytics_summary.csv     # Key business metrics |   |-- capital_allocation.csv    # 8-pattern capital allocation labels |   |-- ratio_edge_cases.log      # Documented KPI anomalies |   -- charts/                   # Visualization PNGs

|

|-- notebooks/                # Exploratory SQL queries

|-- docs/                     # Documentation

|-- Makefile                  # make load | test | validate | ratios

|-- pyproject.toml

|-- requirements.txt

`-- .env

---

## Tech Stack

| Tool       | Purpose                      |
|------------|------------------------------|
| Python 3.12 | Core language               |
| Pandas     | Data loading & transformation |
| SQLite     | Database                     |
| OpenPyXL   | Excel file reading           |
| Pytest     | Unit testing                 |
| Loguru     | Structured logging           |
| Matplotlib | Charts & visualizations      |

---

## Pipeline Overview
12 Excel Files (data/raw/)

|

v

ExcelLoader (loader.py)

|

v

Normalisation

normalise_year() + normalise_ticker()

|

v

16 DQ Validations (validator.py)

|

v

SQLite Database (nifty100.db)

|

v

Ratio Engine (ratio_engine.py)

NPM, OPM, ROE, ROCE, ROA, D/E, ICR,

CAGR (Revenue/PAT/EPS), FCF, CFO Quality,

CapEx Intensity, Capital Allocation

|

v

financial_ratios table + CSVs + Edge Case Log

|

v

SQL Analytics / Screener

|

v

Reports + Charts (output/)

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/sushant0011/Nifty100-Data-Foundation.git
cd Nifty100-Data-Foundation

# Setup virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run ETL loader
python src/etl/loader.py

# Run ratio engine
python -m src.analytics.ratio_engine

# Run all tests
pytest tests/ -v

# Run validator
python -m src.etl.validator
```

---

## Makefile Targets

```bash
make load       # Run ETL loader
make ratios     # Run financial ratio engine
make test       # Run all unit tests
make validate   # Run 16 DQ rules
make report     # Generate analytics report
make clean      # Clean output files
```

---

## Data Quality Rules (Sprint 1)

| Rule  | Severity | Description                              |
|-------|----------|------------------------------------------|
| DQ-01 | CRITICAL | PK uniqueness in companies               |
| DQ-02 | CRITICAL | (company_id, year) composite PK          |
| DQ-03 | CRITICAL | FK integrity - all company_ids valid     |
| DQ-04 | WARNING  | Balance sheet: assets = liabilities +-1% |
| DQ-05 | WARNING  | OPM% cross-check with P&L               |
| DQ-06 | WARNING  | Positive sales values                    |
| DQ-07 | WARNING  | Year range 2000-2030                     |
| DQ-08 | CRITICAL | company_name not null                    |
| DQ-09 | WARNING  | OHLC: high >= low in stock prices        |
| DQ-10 | WARNING  | Positive market cap                      |
| DQ-11 | WARNING  | Net cash flow = sum of activities        |
| DQ-12 | WARNING  | debt_to_equity >= 0                      |
| DQ-13 | WARNING  | EPS sign matches net_profit              |
| DQ-14 | WARNING  | Dividend payout <= 200%                  |
| DQ-15 | WARNING  | Index weights sum ~100%                  |
| DQ-16 | WARNING  | NSE profile URLs valid                   |

---

## Financial KPIs (Sprint 2)

| Category       | Metrics                                                          |
|----------------|-------------------------------------------------------------------|
| Profitability  | Net Profit Margin, Operating Profit Margin, ROE, ROCE, ROA        |
| Leverage       | Debt-to-Equity, Interest Coverage Ratio, Net Debt, Asset Turnover |
| Growth         | Revenue/PAT/EPS CAGR (3yr, 5yr, 10yr) with 6 edge case flags       |
| Cash Flow      | Free Cash Flow, CFO Quality Score, CapEx Intensity, FCF Conversion |
| Capital Allocation | 8-pattern classifier (Reinvestor, Distress Signal, etc.)       |
| Composite      | Weighted Quality Score (0-100) combining ROE, ROCE, NPM, D/E, CFO  |

CAGR edge case flags: `NORMAL`, `DECLINE_TO_LOSS`, `TURNAROUND`, `BOTH_NEGATIVE`, `ZERO_BASE`, `INSUFFICIENT`

---

## Exit Criteria - Sprint 1

- [x] SELECT COUNT(*) FROM companies = 92
- [x] PRAGMA foreign_key_check = 0 rows
- [x] load_audit.csv = zero CRITICAL rejections
- [x] 12 ETL unit tests pass
- [x] Manual review: 5 companies verified
- [x] Sprint review signed off

## Exit Criteria - Sprint 2

- [x] financial_ratios table populated (1,073 rows, 92/92 companies)
- [x] All 14 KPI columns populated
- [x] 67 KPI formula unit tests pass, 0 failures
- [x] ratio_edge_cases.log documented (47 entries)
- [x] Manual spot-check: ROE and 5yr Revenue CAGR verified (0.000% diff)
- [x] Screener preview validated (34 companies, within 15-50 range)
- [x] Sprint review signed off

---

## Author

**Sushant Kumar**