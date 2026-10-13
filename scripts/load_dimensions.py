"""Generate and load the synthetic customers, merchants and accounts.

    python scripts/load_dimensions.py
    python scripts/load_dimensions.py --force   # wipe and regenerate
                                                # (also empties transactions and fraud_scores)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
from faker import Faker
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from src.common import synthetic_world as sw
from src.common.config import RANDOM_SEED
from src.common.db import get_engine
from src.common.logging_setup import get_logger

log = get_logger("load_dimensions")


def build_customers(fake: Faker, rng: np.random.Generator) -> pd.DataFrame:
    ids = np.arange(1, sw.N_CUSTOMERS + 1)
    days_before = rng.integers(30, 365 * 6, size=len(ids))
    signup = pd.Timestamp(sw.DATA_START) - pd.to_timedelta(days_before, unit="D")
    return pd.DataFrame(
        {
            "customer_id": ids,
            "full_name": [fake.name() for _ in ids],
            "country": [fake.country() for _ in ids],
            "signup_date": signup.date,
        }
    )


def build_merchants(fake: Faker, rng: np.random.Generator) -> pd.DataFrame:
    ids = np.arange(1, sw.N_MERCHANTS + 1)
    return pd.DataFrame(
        {
            "merchant_id": ids,
            "merchant_name": [fake.company() for _ in ids],
            "category": rng.choice(sw.MERCHANT_CATEGORIES, size=len(ids)),
        }
    )


def build_accounts(customers: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    account_ids = np.arange(1, sw.N_ACCOUNTS + 1)
    owner_ids = sw.customer_for_account(account_ids)

    signup = pd.to_datetime(
        customers.set_index("customer_id").loc[owner_ids, "signup_date"]
    ).reset_index(drop=True)

    # An account is opened between the owner's signup and the day before the data starts.
    max_offset = (pd.Timestamp(sw.DATA_START) - signup).dt.days.to_numpy() - 1
    offset = rng.integers(0, max_offset + 1)
    opened = signup + pd.to_timedelta(pd.Series(offset), unit="D")

    return pd.DataFrame(
        {
            "account_id": account_ids,
            "customer_id": owner_ids,
            "account_type": rng.choice(sw.ACCOUNT_TYPES, size=len(account_ids), p=[0.5, 0.2, 0.3]),
            "opened_date": opened.dt.date,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Load synthetic dimension tables.")
    parser.add_argument("--force", action="store_true", help="wipe and regenerate")
    args = parser.parse_args()

    engine = get_engine()

    try:
        with engine.connect() as conn:
            existing = conn.execute(text("SELECT COUNT(*) FROM customers")).scalar()
    except ProgrammingError:
        log.error("tables not found - run: python scripts/init_db.py")
        sys.exit(1)

    if existing and not args.force:
        log.info("dimensions already loaded (%d customers). Use --force to regenerate.", existing)
        return

    Faker.seed(RANDOM_SEED)
    fake = Faker()
    rng = np.random.default_rng(RANDOM_SEED)

    customers = build_customers(fake, rng)
    merchants = build_merchants(fake, rng)
    accounts = build_accounts(customers, rng)

    with engine.begin() as conn:
        if args.force:
            conn.execute(text("TRUNCATE accounts, customers, merchants CASCADE"))
        customers.to_sql("customers", conn, if_exists="append", index=False, method="multi")
        merchants.to_sql("merchants", conn, if_exists="append", index=False, method="multi")
        accounts.to_sql("accounts", conn, if_exists="append", index=False, method="multi")

    log.info(
        "loaded %d customers, %d merchants, %d accounts",
        len(customers), len(merchants), len(accounts),
    )


if __name__ == "__main__":
    main()