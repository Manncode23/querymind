"""One-time script: creates the QueryMind folder structure. Safe to re-run."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

DIRS = [
    "dags", "docs", "notebooks", "scripts", "sql", "tests",
    "src/common", "src/ingestion", "src/processing", "src/quality",
    "src/ml", "src/api",
    "data/raw", "data/bronze", "data/silver", "data/gold",
    "models", "logs",
]

PYTHON_PACKAGES = [
    "src", "src/common", "src/ingestion", "src/processing",
    "src/quality", "src/ml", "src/api", "tests",
]

# Folders that must exist in Git even when empty
KEEP_DIRS = [
    "data/raw", "data/bronze", "data/silver", "data/gold",
    "models", "logs", "docs", "notebooks", "sql", "dags",
]


def main() -> None:
    for d in DIRS:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    for pkg in PYTHON_PACKAGES:
        (ROOT / pkg / "__init__.py").touch(exist_ok=True)
    for d in KEEP_DIRS:
        (ROOT / d / ".gitkeep").touch(exist_ok=True)
    print("Project structure created.")


if __name__ == "__main__":
    main()