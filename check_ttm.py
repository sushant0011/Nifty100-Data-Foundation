import sqlite3

conn = sqlite3.connect('db/nifty100.db')

row = conn.execute("""
    SELECT p.year, p.net_profit, b.equity_capital, b.reserves
    FROM profitandloss p
    JOIN balancesheet b ON b.company_id = p.company_id AND b.year = p.year
    WHERE p.company_id = 'RELIANCE' AND p.year = 'Mar 2024'
""").fetchone()

net_profit, equity_cap, reserves = row[1], row[2], row[3]
manual_roe = (net_profit / (equity_cap + reserves)) * 100
print(f"Manual ROE: {manual_roe:.4f}%")

computed = conn.execute("""
    SELECT return_on_equity_pct FROM financial_ratios
    WHERE company_id = 'RELIANCE' AND year = 2024
""").fetchone()
print(f"Engine computed ROE: {computed[0]:.4f}%")

diff = abs(manual_roe - computed[0])
print(f"Difference: {diff:.6f}% -- {'PASS' if diff < 0.1 else 'FAIL'}")

conn.close()