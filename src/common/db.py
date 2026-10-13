"""Shared database engine factory."""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from src.common.config import get_db_url


def get_engine() -> Engine:
    return create_engine(get_db_url(), pool_pre_ping=True)