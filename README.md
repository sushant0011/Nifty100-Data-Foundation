# Nifty100 Data Foundation

> Financial Intelligence System for India's Top 100 Listed Companies

![Python](https://img.shields.io/badge/Python-3.12-blue)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Tests](https://img.shields.io/badge/Tests-12%20passed-brightgreen)
![Sprint](https://img.shields.io/badge/Sprint%201-Complete-success)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

Nifty100 Data Foundation is a production-grade ETL pipeline that extracts financial data from 12 Excel source files, validates it against 16 Data Quality rules, and loads it into a structured SQLite database Ã¢â‚¬â€ powering analytics on India's top 100 listed companies.

---

## Sprint 1 Ã¢â‚¬â€ Data Foundation (Complete)

| Day | Task | Status |
|-----|------|--------|
| Day 01 | Environment Setup Ã¢â‚¬â€ venv, libs, Makefile | Ã¢Å“â€¦ Done |
| Day 02 | Excel Loader & Normaliser Ã¢â‚¬â€ 12 files, 35+ tests | Ã¢Å“â€¦ Done |
| Day 03 | Schema Validator Ã¢â‚¬â€ 16 DQ Rules (CRITICAL + WARNING) | Ã¢Å“â€¦ Done |
| Day 04 | SQLite Database Schema Ã¢â‚¬â€ 12 tables, PK/FK | Ã¢Å“â€¦ Done |
| Day 05 | Full Data Load Ã¢â‚¬â€ 13,871 rows, 0 FK violations | Ã¢Å“â€¦ Done |
| Day 06 | Data Quality Manual Review Ã¢â‚¬â€ 5 companies verified | Ã¢Å“â€¦ Done |
| Day 07 | Sprint Wrap-up Ã¢â‚¬â€ Reports, Charts, Analytics | Ã¢Å“â€¦ Done |

---

## Database Stats

| Table | Rows | Description |
|-------|------|-------------|
| companies | 92 | Master company data |
| profitandloss | 1,276 | P&L statements |
| balancesheet | 1,312 | Balance sheets |
| cashflow | 1,187 | Cash flow statements |
| analysis | 20 | Growth analysis |
| documents | 1,585 | Annual reports |
| financial_ratios | 1,184 | Key financial ratios |
| market_cap | 552 | Market cap history |
| peer_groups | 56 | Peer group mappings |
| prosandcons | 16 | Pros & cons |
| sectors | 92 | Sector classifications |
| stock_prices | 5,520 | Historical stock prices |
| **Total** | **13,871** | |

---

## Project Structure

```
Nifty100_Data_Foundation/
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ data/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ raw/                  # 12 source Excel files
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ processed/            # Cleaned CSVs
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ backup/               # Backups
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ db/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ schema.sql            # 12-table SQLite schema
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ nifty100.db           # SQLite database
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ src/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ etl/
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ loader.py         # Excel Ã¢â€ â€™ SQLite loader
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ normaliser.py     # normalise_year() + normalise_ticker()
Ã¢â€â€š   Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ validator.py      # 16 DQ rules
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ main.py
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ tests/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ test_loader.py        # Loader unit tests
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ test_normaliser.py    # Normaliser unit tests (12 tests)
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ output/
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ load_audit.csv        # Per-table row counts
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ validation_failures.csv # DQ violations with severity
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ final_report.txt      # Sprint wrap-up report
Ã¢â€â€š   Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ analytics_summary.csv # Key business metrics
Ã¢â€â€š   Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ charts/               # Visualization PNGs
Ã¢â€â€š
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ notebooks/                # Exploratory SQL queries
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ docs/                     # Documentation
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ Makefile                  # make load | test | validate
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ pyproject.toml
Ã¢â€Å“Ã¢â€â‚¬Ã¢â€â‚¬ requirements.txt
Ã¢â€â€Ã¢â€â‚¬Ã¢â€â‚¬ .env
```

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.12 | Core language |
| Pandas | Data loading & transformation |
| SQLite | Database |
| OpenPyXL | Excel file reading |
| Pytest | Unit testing |
| Matplotlib | Charts & visualizations |

---

## ETL Pipeline

```
12 Excel Files (data/raw/)
        Ã¢â€ â€œ
   ExcelLoader
  (loader.py)
        Ã¢â€ â€œ
  Normalisation
 normalise_year()
normalise_ticker()
        Ã¢â€ â€œ
 16 DQ Validations
  (validator.py)
        Ã¢â€ â€œ
  SQLite Database
  (nifty100.db)
        Ã¢â€ â€œ
  SQL Analytics
        Ã¢â€ â€œ
  Reports + Charts
   (output/)
```

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

# Run tests
pytest tests/ -v

# Run validator
python -m src.etl.validator
```

---

## Makefile Targets

```bash
make load       # Run ETL loader
make test       # Run all unit tests
make validate   # Run 16 DQ rules
make report     # Generate analytics report
make clean      # Clean output files
```

---

## Data Quality Rules

| Rule | Severity | Description |
|------|----------|-------------|
| DQ-01 | CRITICAL | PK uniqueness in companies |
| DQ-02 | CRITICAL | (company_id, year) composite PK |
| DQ-03 | CRITICAL | FK integrity Ã¢â‚¬â€ all company_ids valid |
| DQ-04 | WARNING | Balance sheet: assets = liabilities Ã‚Â±1% |
| DQ-05 | WARNING | OPM% cross-check with P&L |
| DQ-06 | WARNING | Positive sales values |
| DQ-07 | WARNING | Year range 2000Ã¢â‚¬â€œ2030 |
| DQ-08 | CRITICAL | company_name not null |
| DQ-09 | WARNING | OHLC: high >= low in stock prices |
| DQ-10 | WARNING | Positive market cap |
| DQ-11 | WARNING | Net cash flow = sum of activities |
| DQ-12 | WARNING | debt_to_equity >= 0 |
| DQ-13 | WARNING | EPS sign matches net_profit |
| DQ-14 | WARNING | Dividend payout <= 200% |
| DQ-15 | WARNING | Index weights sum ~100% |
| DQ-16 | WARNING | NSE profile URLs valid |

---

## Exit Criteria Ã¢â‚¬â€ Sprint 1

- [x] SELECT COUNT(*) FROM companies = 92
- [x] PRAGMA foreign_key_check = 0 rows
- [x] load_audit.csv = zero CRITICAL rejections
- [x] 12 ETL unit tests pass
- [x] Manual review: 5 companies verified
- [x] Sprint review signed off

---

## Author

**Sushant Kumar**  
GitHub: [sushant0011](https://github.com/sushant0011)
