"""
IrisStore — shared SQLite store for the IRIS ecosystem.
All four tools write and read from ~/.iris/iris.db
"""
import sqlite3
import pathlib
from typing import List, Optional

from .event import IrisEvent

DEFAULT_DB = pathlib.Path.home() / ".iris" / "iris.db"
SCHEMA     = pathlib.Path(__file__).parent / "schema.sql"


class IrisStore:
    def __init__(self, db_path: pathlib.Path = DEFAULT_DB):
        self.db_path = pathlib.Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        schema_sql = SCHEMA.read_text()
        with self._connect() as con:
            con.executescript(schema_sql)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    # ── write ──────────────────────────────────────────────────────────────
    def write(self, event: IrisEvent) -> None:
        """Write a single IrisEvent to the store."""
        sql = """
            INSERT INTO iris_events
                (id, source, event_type, timestamp, severity,
                 ttd_seconds, ttr_seconds, classification, confidence, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._connect() as con:
            con.execute(sql, event.to_row())
            con.commit()

    # ── read ───────────────────────────────────────────────────────────────
    def get(self, event_id: str) -> Optional[IrisEvent]:
        """Fetch a single event by ID."""
        with self._connect() as con:
            row = con.execute(
                "SELECT * FROM iris_events WHERE id = ?", (event_id,)
            ).fetchone()
        return IrisEvent.from_row(tuple(row)) if row else None

    def latest(self, n: int = 10, source: str = None) -> List[IrisEvent]:
        """Return the n most recent events, optionally filtered by source."""
        sql  = "SELECT * FROM iris_events"
        args = []
        if source:
            sql  += " WHERE source = ?"
            args.append(source)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        args.append(n)
        with self._connect() as con:
            rows = con.execute(sql, args).fetchall()
        return [IrisEvent.from_row(tuple(r)) for r in rows]

    def unclassified(self) -> List[IrisEvent]:
        """Return ChaosPanda events not yet classified by RCA-GPT."""
        sql = """
            SELECT * FROM iris_events
            WHERE source = 'chaospanda'
              AND classification IS NULL
            ORDER BY timestamp ASC
        """
        with self._connect() as con:
            rows = con.execute(sql).fetchall()
        return [IrisEvent.from_row(tuple(r)) for r in rows]

    def update_classification(
        self, event_id: str, classification: str, confidence: float
    ) -> None:
        """RCA-GPT calls this to stamp its result onto an existing event."""
        with self._connect() as con:
            con.execute(
                """UPDATE iris_events
                   SET classification = ?, confidence = ?
                   WHERE id = ?""",
                (classification, confidence, event_id),
            )
            con.commit()