-- ================================================================
-- notebooks/exploratory_queries.sql
-- Nifty100 Data Foundation -- Sprint 1, Day 7
-- 10 Exploratory SQL Queries on nifty100.db
-- Run: sqlite3 db/nifty100.db < notebooks/exploratory_queries.sql
-- ================================================================

-- ----------------------------------------------------------------
-- Q-01: Total companies in database
-- ----------------------------------------------------------------
SELECT
    'Total Companies' AS metric,
    COUNT(*) AS value
FROM companies;

-- ----------------------------------------------------------------
-- Q-02: Top 10 companies by latest market cap
-- ----------------------------------------------------------------
SELECT
    c.company_name,
    c.id AS ticker,
    m.market_cap_crore,
    m.year
FROM market_cap m
JOIN companies c ON m.company_id = c.id
WHERE m.year = (SELECT MAX(year) FROM market_cap WHERE company_id = m.company_id)
ORDER BY m.market_cap_crore DESC
LIMIT 10;

-- ----------------------------------------------------------------
-- Q-03: Top 10 companies by ROCE (Return on Capital Employed)
-- ----------------------------------------------------------------
SELECT
    company_name,
    id AS ticker,
    ROUND(roce_percentage, 2) AS roce_pct
FROM companies
WHERE roce_percentage IS NOT NULL
ORDER BY roce_percentage DESC
LIMIT 10;

-- ----------------------------------------------------------------
-- Q-04: Sector-wise company count and average index weight
-- ----------------------------------------------------------------
SELECT
    broad_sector,
    COUNT(*) AS company_count,
    ROUND(SUM(index_weight_pct), 2) AS total_weight_pct,
    ROUND(AVG(index_weight_pct), 4) AS avg_weight_pct
FROM sectors
GROUP BY broad_sector
ORDER BY total_weight_pct DESC;

-- ----------------------------------------------------------------
-- Q-05: Year-wise total sales trend (Nifty100 aggregate)
-- ----------------------------------------------------------------
SELECT
    year,
    ROUND(SUM(sales), 2) AS total_sales_cr,
    ROUND(SUM(net_profit), 2) AS total_profit_cr,
    ROUND(SUM(net_profit) * 100.0 / NULLIF(SUM(sales), 0), 2) AS net_margin_pct
FROM profitandloss
WHERE year >= 2018
GROUP BY year
ORDER BY year;

-- ----------------------------------------------------------------
-- Q-06: Top 10 companies by latest EPS
-- ----------------------------------------------------------------
SELECT
    c.company_name,
    p.company_id AS ticker,
    p.year,
    ROUND(p.eps, 2) AS eps
FROM profitandloss p
JOIN companies c ON p.company_id = c.id
WHERE p.year = (SELECT MAX(year) FROM profitandloss WHERE company_id = p.company_id)
  AND p.eps IS NOT NULL
ORDER BY p.eps DESC
LIMIT 10;

-- ----------------------------------------------------------------
-- Q-07: Companies with strongest balance sheets
--        (low debt, high reserves)
-- ----------------------------------------------------------------
SELECT
    c.company_name,
    b.company_id AS ticker,
    b.year,
    ROUND(b.reserves, 2) AS reserves_cr,
    ROUND(b.borrowings, 2) AS borrowings_cr,
    ROUND(b.borrowings / NULLIF(b.reserves, 0), 4) AS debt_to_reserves
FROM balancesheet b
JOIN companies c ON b.company_id = c.id
WHERE b.year = (SELECT MAX(year) FROM balancesheet WHERE company_id = b.company_id)
  AND b.reserves > 0
ORDER BY debt_to_reserves ASC
LIMIT 10;

-- ----------------------------------------------------------------
-- Q-08: Stock price performance -- 52-week high/low per company
-- ----------------------------------------------------------------
SELECT
    c.company_name,
    s.company_id AS ticker,
    ROUND(MAX(s.high_price), 2) AS week52_high,
    ROUND(MIN(s.low_price), 2) AS week52_low,
    ROUND((MAX(s.high_price) - MIN(s.low_price)) * 100.0
          / NULLIF(MIN(s.low_price), 0), 2) AS price_range_pct
FROM stock_prices s
JOIN companies c ON s.company_id = c.id
WHERE s.date >= DATE('now', '-365 days')
GROUP BY s.company_id
ORDER BY price_range_pct DESC
LIMIT 10;

-- ----------------------------------------------------------------
-- Q-09: Companies with consistent profit growth (last 3 years)
-- ----------------------------------------------------------------
SELECT
    p3.company_id AS ticker,
    c.company_name,
    ROUND(p1.net_profit, 2) AS profit_2022,
    ROUND(p2.net_profit, 2) AS profit_2023,
    ROUND(p3.net_profit, 2) AS profit_2024,
    ROUND((p3.net_profit - p1.net_profit) * 100.0
          / NULLIF(ABS(p1.net_profit), 0), 2) AS growth_2yr_pct
FROM profitandloss p1
JOIN profitandloss p2 ON p1.company_id = p2.company_id AND p2.year = p1.year + 1
JOIN profitandloss p3 ON p1.company_id = p3.company_id AND p3.year = p1.year + 2
JOIN companies c ON p1.company_id = c.id
WHERE p1.year = 2022
  AND p1.net_profit > 0
  AND p2.net_profit > p1.net_profit
  AND p3.net_profit > p2.net_profit
ORDER BY growth_2yr_pct DESC
LIMIT 10;

-- ----------------------------------------------------------------
-- Q-10: Load audit summary -- rows per table
-- ----------------------------------------------------------------
SELECT 'companies'        AS tbl, COUNT(*) AS rows FROM companies
UNION ALL
SELECT 'profitandloss',             COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet',              COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow',                  COUNT(*) FROM cashflow
UNION ALL
SELECT 'analysis',                  COUNT(*) FROM analysis
UNION ALL
SELECT 'documents',                 COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons',               COUNT(*) FROM prosandcons
UNION ALL
SELECT 'sectors',                   COUNT(*) FROM sectors
UNION ALL
SELECT 'financial_ratios',          COUNT(*) FROM financial_ratios
UNION ALL
SELECT 'market_cap',                COUNT(*) FROM market_cap
UNION ALL
SELECT 'peer_groups',               COUNT(*) FROM peer_groups
UNION ALL
SELECT 'stock_prices',              COUNT(*) FROM stock_prices
UNION ALL
SELECT '--- TOTAL ---',             (
    SELECT COUNT(*) FROM companies) +
    (SELECT COUNT(*) FROM profitandloss) +
    (SELECT COUNT(*) FROM balancesheet) +
    (SELECT COUNT(*) FROM cashflow) +
    (SELECT COUNT(*) FROM analysis) +
    (SELECT COUNT(*) FROM documents) +
    (SELECT COUNT(*) FROM prosandcons) +
    (SELECT COUNT(*) FROM sectors) +
    (SELECT COUNT(*) FROM financial_ratios) +
    (SELECT COUNT(*) FROM market_cap) +
    (SELECT COUNT(*) FROM peer_groups) +
    (SELECT COUNT(*) FROM stock_prices);
