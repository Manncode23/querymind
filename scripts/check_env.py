"""Checks that this machine is ready for QueryMind. Run from the project root:
    python scripts/check_env.py
"""
import importlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

REQUIRED_PACKAGES = {
    "pandas": "pandas",
    "numpy": "numpy",
    "sklearn": "scikit-learn",
    "pyarrow": "pyarrow",
    "matplotlib": "matplotlib",
    "psycopg2": "psycopg2-binary",
    "sqlalchemy": "SQLAlchemy",
    "dotenv": "python-dotenv",
    "faker": "faker",
    "pyspark": "pyspark",
    "kafka": "kafka-python",
    "pytest": "pytest",
}

EXPECTED_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]

failures = 0


def ok(msg: str) -> None:
    print(f"[OK]   {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def fail(msg: str) -> None:
    global failures
    failures += 1
    print(f"[FAIL] {msg}")


def check_python() -> None:
    v = sys.version_info
    text = f"Python {v.major}.{v.minor}.{v.micro}"
    if (3, 9) <= (v.major, v.minor) < (3, 12):
        ok(text)
    else:
        warn(f"{text} - Python 3.10 or 3.11 is recommended for PySpark and Kafka")


def check_packages() -> None:
    for module, pip_name in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module)
            ok(f"package {pip_name}")
        except ImportError:
            fail(f"package {pip_name} is missing (pip install -r requirements.txt)")


def check_java() -> None:
    java = shutil.which("java")
    if not java:
        warn("Java not found - PySpark needs Java 11 or 17 (needed from Stage 4)")
        return
    result = subprocess.run([java, "-version"], capture_output=True, text=True)
    first_line = (result.stderr or result.stdout).splitlines()[0]
    ok(f"Java found: {first_line}")


def check_docker() -> None:
    if shutil.which("docker"):
        ok("Docker found")
    else:
        warn("Docker not found - we will decide how to run Kafka in the ingestion stage")


def check_csv() -> None:
    try:
        import pandas as pd
        from src.common.config import RAW_CSV
    except ImportError:
        fail("cannot check the dataset until the packages are installed")
        return

    if not RAW_CSV.exists():
        fail(f"dataset not found at {RAW_CSV}")
        return
    columns = list(pd.read_csv(RAW_CSV, nrows=0).columns)
    if columns == EXPECTED_COLUMNS:
        ok(f"dataset found with the expected {len(columns)} columns")
    else:
        fail("dataset found but its columns do not match the Kaggle file")


def check_database() -> None:
    try:
        from sqlalchemy import create_engine, text
        from src.common import config
    except ImportError:
        fail("cannot check the database until the packages are installed")
        return

    try:
        engine = create_engine(config.get_db_url())
        with engine.connect() as conn:
            version = conn.execute(text("SELECT version()")).scalar()
        ok(f"connected to '{config.DB_NAME}' ({version.split(',')[0]})")
    except Exception as exc:
        fail(f"database connection failed: {type(exc).__name__} - check your .env and that Postgres is running")


def main() -> None:
    print("QueryMind environment check\n" + "-" * 40)
    check_python()
    check_packages()
    check_java()
    check_docker()
    check_csv()
    check_database()
    print("-" * 40)
    if failures:
        print(f"{failures} problem(s) to fix before continuing.")
        sys.exit(1)
    print("All critical checks passed.")


if __name__ == "__main__":
    main()