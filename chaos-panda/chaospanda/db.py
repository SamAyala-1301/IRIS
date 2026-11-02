"""
chaospanda/db.py — experiments.db helpers
"""
import sqlite3


def init_db(db_path):
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id           TEXT PRIMARY KEY,
            timestamp    TEXT,
            deployment   TEXT,
            namespace    TEXT,
            pod_killed   TEXT,
            ttd_seconds  REAL,
            ttr_seconds  REAL,
            status       TEXT,
            events       TEXT
        )
    """)
    con.commit()
    return con


def write_incident(con, row):
    con.execute(
        "INSERT INTO experiments VALUES (?,?,?,?,?,?,?,?,?)", row
    )
    con.commit()


def print_last_incident(con):
    row = con.execute(
        "SELECT id, timestamp, pod_killed, ttd_seconds, ttr_seconds, status "
        "FROM experiments ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    if not row:
        return
    print("\n  ── Last incident in DB ──────────────────────────────")
    print(f"  ID         : {row[0]}")
    print(f"  Timestamp  : {row[1]}")
    print(f"  Pod killed : {row[2]}")
    print(f"  TTD        : {row[3]}s")
    print(f"  TTR        : {row[4]}s")
    print(f"  Status     : {row[5]}")
    print(f"  ────────────────────────────────────────────────────\n")