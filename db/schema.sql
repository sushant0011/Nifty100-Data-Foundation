-- =============================================================
-- db/schema.sql
-- Nifty100 Data Foundation — Sprint 1, Day 4
-- SQLite schema — 10 tables, PK/FK, PRAGMA foreign_keys = ON
-- =============================================================

PRAGMA foreign_keys = ON;

-- -------------------------------------------------------------
-- 1. companies  (master / dimension table)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    id                  TEXT    PRIMARY KEY,   -- NSE ticker e.g. "RELIANCE"
    company_logo        TEXT,
    company_name        TEXT    NOT NULL,
    chart_link          TEXT,
    about_company       TEXT,
    website             TEXT,
    nse_profile         TEXT,
    bse_profile         TEXT,
    face_value          REAL,
    book_value          REAL,
    roce_percentage     REAL,
    roe_percentage      REAL
);

-- -------------------------------------------------------------
-- 2. profitandloss
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profitandloss (
    id                  INTEGER PRIMARY KEY,
    company_id          TEXT    NOT NULL REFERENCES companies(id),
    year                INTEGER NOT NULL,
    sales               REAL,
    expenses            REAL,
    operating_profit    REAL,
    opm_percentage      REAL,
    other_income        REAL,
    interest            REAL,
    depreciation        REAL,
    profit_before_tax   REAL,
    tax_percentage      REAL,
    net_profit          REAL,
    eps                 REAL,
    dividend_payout     REAL,
    UNIQUE (company_id, year)
);

-- -------------------------------------------------------------
-- 3. balancesheet
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS balancesheet (
    id                  INTEGER PRIMARY KEY,
    company_id          TEXT    NOT NULL REFERENCES companies(id),
    year                INTEGER NOT NULL,
    equity_capital      REAL,
    reserves            REAL,
    borrowings          REAL,
    other_liabilities   REAL,
    total_liabilities   REAL,
    fixed_assets        REAL,
    cwip                REAL,
    investments         REAL,
    other_asset         REAL,
    total_assets        REAL,
    UNIQUE (company_id, year)
);

-- -------------------------------------------------------------
-- 4. cashflow
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cashflow (
    id                  INTEGER PRIMARY KEY,
    company_id          TEXT    NOT NULL REFERENCES companies(id),
    year                INTEGER NOT NULL,
    operating_activity  REAL,
    investing_activity  REAL,
    financing_activity  REAL,
    net_cash_flow       REAL,
    UNIQUE (company_id, year)
);

-- -------------------------------------------------------------
-- 5. analysis
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analysis (
    id                      INTEGER PRIMARY KEY,
    company_id              TEXT    NOT NULL REFERENCES companies(id),
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr        TEXT,
    roe                     TEXT,
    UNIQUE (company_id)
);

-- -------------------------------------------------------------
-- 6. documents
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY,
    company_id  TEXT    NOT NULL REFERENCES companies(id),
    year        INTEGER NOT NULL,
    annual_report TEXT,
    UNIQUE (company_id, year)
);

-- -------------------------------------------------------------
-- 7. prosandcons
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS prosandcons (
    id          INTEGER PRIMARY KEY,
    company_id  TEXT    NOT NULL REFERENCES companies(id),
    pros        TEXT,
    cons        TEXT,
    UNIQUE (company_id)
);

-- -------------------------------------------------------------
-- 8. sectors
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sectors (
    id                  INTEGER PRIMARY KEY,
    company_id          TEXT    NOT NULL REFERENCES companies(id),
    broad_sector        TEXT,
    sub_sector          TEXT,
    index_weight_pct    REAL,
    market_cap_category TEXT,
    UNIQUE (company_id)
);

-- -------------------------------------------------------------
-- 9. financial_ratios
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS financial_ratios (
    id                          INTEGER PRIMARY KEY,
    company_id                  TEXT    NOT NULL REFERENCES companies(id),
    year                        INTEGER NOT NULL,
    net_profit_margin_pct       REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct        REAL,
    debt_to_equity              REAL,
    interest_coverage           REAL,
    asset_turnover              REAL,
    free_cash_flow_cr           REAL,
    capex_cr                    REAL,
    earnings_per_share          REAL,
    book_value_per_share        REAL,
    dividend_payout_ratio_pct   REAL,
    total_debt_cr               REAL,
    cash_from_operations_cr     REAL,
    UNIQUE (company_id, year)
);

-- -------------------------------------------------------------
-- 10. market_cap
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_cap (
    id                      INTEGER PRIMARY KEY,
    company_id              TEXT    NOT NULL REFERENCES companies(id),
    year                    INTEGER NOT NULL,
    market_cap_crore        REAL,
    enterprise_value_crore  REAL,
    pe_ratio                REAL,
    pb_ratio                REAL,
    ev_ebitda               REAL,
    dividend_yield_pct      REAL,
    UNIQUE (company_id, year)
);

-- -------------------------------------------------------------
-- 11. peer_groups
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS peer_groups (
    id              INTEGER PRIMARY KEY,
    peer_group_name TEXT    NOT NULL,
    company_id      TEXT    NOT NULL REFERENCES companies(id),
    is_benchmark    INTEGER DEFAULT 0,   -- 0=False, 1=True
    UNIQUE (peer_group_name, company_id)
);

-- -------------------------------------------------------------
-- 12. stock_prices
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_prices (
    id              INTEGER PRIMARY KEY,
    company_id      TEXT    NOT NULL REFERENCES companies(id),
    date            TEXT    NOT NULL,    -- YYYY-MM-DD
    open_price      REAL,
    high_price      REAL,
    low_price       REAL,
    close_price     REAL,
    volume          INTEGER,
    adjusted_close  REAL,
    UNIQUE (company_id, date)
);