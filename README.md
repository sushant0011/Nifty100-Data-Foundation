# Nifty100 Data Foundation

> Financial Intelligence System for India's Top 100 Listed Companies

![Python](https://img.shields.io/badge/Python-3.12-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Tests](https://img.shields.io/badge/Tests-100%20passed-brightgreen)
![Sprint](https://img.shields.io/badge/Sprint%203-Complete-success)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

Nifty100 Data Foundation is a production-grade ETL and analytics pipeline that extracts financial data from 12 Excel source files, validates it against 16 Data Quality rules, loads it into a structured SQLite database, computes 50+ financial KPIs, and powers a fully functional screener and peer comparison engine for India's top 100 listed companies.

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
- [x] ratio_edge_cases.log - 47 documented anomalies
- [x] Manual spot-check: ROE and Revenue 5yr CAGR verified (0.000% diff)
- [x] Screener preview: ROE>15% and D/E<1 returns 34 companies

---

## Sprint 3 - Screener & Peer Comparison Engine (Complete)

| Day    | Task                                                              | Status |
|--------|-------------------------------------------------------------------|--------|
| Day 15 | Filter Engine Core - 15 filterable metrics, YAML config            | Done   |
| Day 16 | 6 Preset Screeners - Quality Compounder, Value Pick, Growth etc.   | Done   |
| Day 17 | Composite Score + screener_output.xlsx - colour-coded cells        | Done   |
| Day 18 | Peer Percentile Rankings - 11 groups, 10 metrics, 560 rows         | Done   |
| Day 19 | Radar Charts - 92 PNG charts with peer group overlay               | Done   |
| Day 20 | peer_comparison.xlsx - 11 sheets, percentile colour-coded          | Done   |
| Day 21 | 21 Screener Tests, 0 failures, Sprint Review                       | Done   |

### Sprint 3 Exit Criteria

- [x] 6 preset screeners each return between 5 and 50 companies
- [x] peer_comparison.xlsx has exactly 11 sheets covering all 11 peer groups
- [x] peer_percentiles table - 560 rows, 11 groups, 10 metrics each
- [x] 92 radar charts generated - reports/radar_charts/
- [x] 21 screener unit tests pass, 0 failures
- [x] Total project tests: 100 passing, 0 failures
- [x] Sprint 3 review completed

---

## Database Stats

| Table              | Rows   | Description              |
|--------------------|--------|--------------------------|
| companies          | 92     | Master company data      |
| profitandloss      | 1,276  | P&L statements           |
| balancesheet       | 1,312  | Balance sheets           |
| cashflow           | 1,187  | Cash flow statements     |
| analysis           | 20     | Growth analysis          |
| documents          | 1,585  | Annual reports           |
| financial_ratios   | 1,073  | Computed KPIs (Sprint 2) |
| market_cap         | 552    | Market cap history       |
| peer_groups        | 56     | Peer group mappings      |
| peer_percentiles   | 560    | Peer rankings (Sprint 3) |
| prosandcons        | 16     | Pros & cons              |
| sectors            | 92     | Sector classifications   |
| stock_prices       | 5,520  | Historical stock prices  |
| **Total**          | **13,341** |                      |

---

## Project Structure
Nifty100_Data_Foundation/
|
|-- config/
|   -- screener_config.yaml      # All threshold definitions, analyst-editable | |-- data/ |   |-- raw/                      # 12 source Excel files |   -- processed/                # Cleaned CSVs
|
|-- db/
|   |-- schema.sql                # 12-table SQLite schema
|   -- nifty100.db               # SQLite database | |-- src/ |   |-- etl/ |   |   |-- loader.py             # Excel -> SQLite loader |   |   |-- normaliser.py         # normalise_year() + normalise_ticker() |   |   -- validator.py          # 16 DQ rules
|   |-- analytics/
|   |   |-- ratios.py             # NPM, OPM, ROE, ROCE, ROA, D/E, ICR
|   |   |-- cagr.py               # CAGR engine, 6 edge cases
|   |   |-- cashflow_kpis.py      # FCF, CFO Quality, CapEx, Capital Allocator
|   |   |-- ratio_engine.py       # Full KPI runner
|   |   |-- peer.py               # Peer percentile rankings
|   |   -- radar.py              # Radar chart generator |   |-- screener/ |   |   |-- engine.py             # Filter engine, 6 presets, composite score |   |   |-- exporter.py           # Excel export (screener + peer comparison) |   |   -- run_sprint3.py        # Sprint 3 full runner
|   -- utils/ |       |-- config.py             # Central config |       -- logger.py             # Loguru logging
|
|-- tests/
|   |-- etl/                      # ETL unit tests
|   |-- kpi/                      # 67 KPI formula tests
|   -- screener/                 # 21 screener + peer tests | |-- output/ |   |-- screener_output.xlsx      # 6 preset sheets, colour-coded |   |-- peer_comparison.xlsx      # 11 peer group sheets, percentile colours |   |-- capital_allocation.csv    # 8-pattern capital allocation labels |   -- ratio_edge_cases.log      # Documented KPI anomalies
|
|-- reports/
|   -- radar_charts/             # 92 PNG radar charts | |-- Makefile |-- requirements.txt -- .env

---

## Tech Stack

| Tool        | Purpose                       |
|-------------|-------------------------------|
| Python 3.12 | Core language                 |
| Pandas      | Data loading & transformation |
| SQLite      | Database                      |
| OpenPyXL    | Excel export with formatting  |
| Matplotlib  | Radar charts                  |
| PyYAML      | Screener config               |
| Pytest      | Unit testing (100 tests)      |
| Loguru      | Structured logging            |

---

## Quick Start

```bash
git clone https://github.com/sushant0011/Nifty100-Data-Foundation.git
cd Nifty100-Data-Foundation

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python src/etl/loader.py
python -m src.analytics.ratio_engine
python -m src.screener.run_sprint3

pytest tests/ -v
```

---

## Screener Presets

| Preset             | Key Filters                                      |
|--------------------|--------------------------------------------------|
| Quality Compounder | ROE>15%, D/E<1, FCF>0, Revenue CAGR 5yr>10%     |
| Value Pick         | P/E<20, P/B<3, D/E<2, Dividend Yield>1%         |
| Growth Accelerator | PAT CAGR>20%, Revenue CAGR>15%, D/E<2           |
| Dividend Champion  | Dividend Yield>2%, FCF>0                         |
| Debt Free Blue Chip| D/E<0.1, ROE>12%, Sales>5000 Cr                 |
| Turnaround Watch   | Revenue CAGR>10%, FCF>0                          |

---

## Author

**Sushant Kumar**
GitHub: [sushant0011](https://github.com/sushant0011)