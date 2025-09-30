import sqlite3
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_MAP = {
    "hr": str(DATA_DIR / "hr.db"),
    "healthcare": str(DATA_DIR / "healthcare.db"),
    "ecommerce": str(DATA_DIR / "ecommerce.db"),
    "finance": str(DATA_DIR / "finance.db"),
    "education": str(DATA_DIR / "education.db")
}

def get_connection(target_db: str):
    path = DB_MAP.get(target_db)
    if not path:
        raise ValueError("Unknown target_db: " + str(target_db))
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def query_db(target_db: str, sql: str, params: tuple = ()):
    conn = get_connection(target_db)
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def execute_db(target_db: str, sql: str, params: tuple = ()):
    conn = get_connection(target_db)
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    lastrow = cur.lastrowid
    conn.close()
    return lastrow

def init_databases():
    # No-op here; databases created via init_db.py
    return
