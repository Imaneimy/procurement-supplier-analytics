"""Run the named queries in sql/kpis.sql against the warehouse."""
import re
import sqlite3
from pathlib import Path

import pandas as pd

from etl import DB_PATH

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "kpis.sql"


def load_queries(path: Path = SQL_FILE) -> dict:
    blocks = re.split(r"^-- name: (\w+)\s*$", path.read_text(), flags=re.M)[1:]
    return {name: sql.strip() for name, sql in zip(blocks[::2], blocks[1::2])}


def run_all(db_path: Path = DB_PATH) -> dict:
    with sqlite3.connect(db_path) as con:
        return {name: pd.read_sql(sql, con) for name, sql in load_queries().items()}
