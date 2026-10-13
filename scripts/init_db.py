"""Create (or recreate) the QueryMind tables.

WARNING: drops the existing tables in the configured database.
    python scripts/init_db.py
    python scripts/init_db.py --yes     # skip the confirmation prompt
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect

from src.common.config import DB_NAME, PROJECT_ROOT
from src.common.db import get_engine
from src.common.logging_setup import get_logger

log = get_logger("init_db")
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the QueryMind schema.")
    parser.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()

    if not args.yes:
        answer = input(
            f"This DROPS and recreates all QueryMind tables in '{DB_NAME}'. "
            "Type 'yes' to continue: "
        )
        if answer.strip().lower() != "yes":
            print("Aborted.")
            return

    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    engine = get_engine()
    with engine.begin() as conn:
        conn.exec_driver_sql(sql)

    tables = sorted(inspect(engine).get_table_names())
    log.info("schema applied; tables in '%s': %s", DB_NAME, ", ".join(tables))


if __name__ == "__main__":
    main()