import sqlite3, json
from pathlib import Path

DATA_DIR = Path("data")
PENDING_DB = DATA_DIR / "pending.db"
PENDING_DB.parent.mkdir(exist_ok=True)
# initialize pending table
conn = sqlite3.connect(PENDING_DB)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS pending (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_db TEXT,
    operation TEXT,
    sql TEXT,
    metadata TEXT,
    status TEXT DEFAULT 'PENDING'  -- PENDING, APPROVED, REJECTED
)''')
conn.commit()
conn.close()

class PendingManager:
    def __init__(self):
        self.db = str(PENDING_DB)

    def add_pending(self, target_db: str, operation: str, sql: str, metadata: dict):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("INSERT INTO pending (target_db,operation,sql,metadata) VALUES (?,?,?,?)",
                  (target_db, operation, sql, json.dumps(metadata)))
        conn.commit()
        pid = c.lastrowid
        conn.close()
        return pid

    def list_pending(self, status_filter=None):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        if status_filter:
            c.execute("SELECT id,target_db,operation,sql,metadata,status FROM pending WHERE status=?", (status_filter,))
        else:
            c.execute("SELECT id,target_db,operation,sql,metadata,status FROM pending")
        rows = c.fetchall()
        conn.close()
        result = []
        for r in rows:
            result.append({"id": r[0], "target_db": r[1], "operation": r[2], "sql": r[3], "metadata": json.loads(r[4]), "status": r[5]})
        return result

    def get(self, pid: int):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT id,target_db,operation,sql,metadata,status FROM pending WHERE id=?", (pid,))
        r = c.fetchone()
        conn.close()
        if not r:
            return None
        return {"id": r[0], "target_db": r[1], "operation": r[2], "sql": r[3], "metadata": json.loads(r[4]), "status": r[5]}

    def set_status(self, pid: int, status: str):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("UPDATE pending SET status=? WHERE id=?", (status, pid))
        conn.commit()
        conn.close()
