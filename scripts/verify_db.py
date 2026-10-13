"""Sanity checks and example analytical queries for the serving layer.
    python scripts/verify_db.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from sqlalchemy import text

from src.common.db import get_engine

COUNT_TABLES = ["customers", "merchants", "accounts", "transactions", "fraud_scores"]

# Each check must return 0 to pass.
INTEGRITY_CHECKS = {
    "customers with no account": """
        SELECT COUNT(*) FROM customers c
        WHERE NOT EXISTS (SELECT 1 FROM accounts a WHERE a.customer_id = c.customer_id)
    """,
    "accounts opened before the owner signed up": """
        SELECT COUNT(*) FROM accounts a
        JOIN customers c ON c.customer_id = a.customer_id
        WHERE a.opened_date < c.signup_date
    """,
    "accounts opened on/after the data start (2013-09-01)": """
        SELECT COUNT(*) FROM accounts WHERE opened_date >= DATE '2013-09-01'
    """,
}

EXAMPLE_QUERIES = {
    "Top 5 countries by customers (CTE + window function)": """
        WITH per_customer AS (
            SELECT c.country, c.customer_id, COUNT(a.account_id) AS n_accounts
            FROM customers c
            JOIN accounts a ON a.customer_id = c.customer_id
            GROUP BY c.country, c.customer_id
        )
        SELECT country,
               COUNT(*)        AS customers,
               SUM(n_accounts) AS accounts,
               RANK() OVER (ORDER BY COUNT(*) DESC) AS country_rank
        FROM per_customer
        GROUP BY country
        ORDER BY country_rank, country
        LIMIT 5
    """,
    "Account type mix": """
        SELECT account_type,
               COUNT(*) AS accounts,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
        FROM accounts
        GROUP BY account_type
        ORDER BY accounts DESC
    """,
    "Merchants per category": """
        SELECT category, COUNT(*) AS merchants
        FROM merchants
        GROUP BY category
        ORDER BY merchants DESC, category
    """,
}


def main() -> None:
    engine = get_engine()
    failures = 0

    with engine.connect() as conn:
        print("Row counts")
        for table in COUNT_TABLES:
            n = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table:<14} {n:>8,}")

        print("\nIntegrity checks (each must be 0)")
        for name, sql in INTEGRITY_CHECKS.items():
            bad = conn.execute(text(sql)).scalar()
            status = "OK  " if bad == 0 else "FAIL"
            if bad != 0:
                failures += 1
            print(f"  [{status}] {name}: {bad}")

        for title, sql in EXAMPLE_QUERIES.items():
            print(f"\n{title}")
            print(pd.read_sql(text(sql), conn).to_string(index=False))

    if failures:
        print(f"\n{failures} integrity check(s) failed.")
        sys.exit(1)
    print("\nAll integrity checks passed.")


if __name__ == "__main__":
    main()