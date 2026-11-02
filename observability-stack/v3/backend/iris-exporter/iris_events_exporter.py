"""Expose read-only aggregates from the shared IRIS SQLite event store."""
import os
import sqlite3
import time
from pathlib import Path

from prometheus_client import Gauge, start_http_server


DB_PATH = Path(os.environ.get("IRIS_DB_PATH", "/var/lib/iris/iris.db"))
PORT = int(os.environ.get("IRIS_EXPORTER_PORT", "8002"))
POLL_SECONDS = float(os.environ.get("IRIS_EXPORTER_POLL_SECONDS", "5"))

DB_UP = Gauge("iris_event_store_up", "Whether the IRIS event database can be read")
EVENTS = Gauge(
    "iris_events_total",
    "Current event count in the IRIS store",
    ["source", "event_type", "severity", "classification"],
)
UNCLASSIFIED = Gauge(
    "iris_events_unclassified_total",
    "Current events awaiting RCA-GPT classification",
    ["source"],
)
CONFIDENCE = Gauge(
    "iris_event_classification_confidence_avg",
    "Average RCA-GPT confidence by classification",
    ["classification"],
)


def refresh_metrics():
    EVENTS.clear()
    UNCLASSIFIED.clear()
    CONFIDENCE.clear()
    if not DB_PATH.is_file():
        DB_UP.set(0)
        return

    try:
        db_uri = DB_PATH.resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(db_uri, uri=True, timeout=2) as connection:
            rows = connection.execute(
                """SELECT source, event_type, severity,
                          COALESCE(classification, 'unclassified'), COUNT(*)
                   FROM iris_events
                   GROUP BY source, event_type, severity, classification"""
            ).fetchall()
            pending = connection.execute(
                """SELECT source, COUNT(*) FROM iris_events
                   WHERE classification IS NULL GROUP BY source"""
            ).fetchall()
            confidence = connection.execute(
                """SELECT classification, AVG(confidence) FROM iris_events
                   WHERE classification IS NOT NULL AND confidence IS NOT NULL
                   GROUP BY classification"""
            ).fetchall()
        DB_UP.set(1)
        for source in ("chaospanda", "rca-gpt", "ciia", "obs-stack"):
            UNCLASSIFIED.labels(source).set(0)
        for source, event_type, severity, classification, count in rows:
            EVENTS.labels(source, event_type, severity, classification).set(count)
        for source, count in pending:
            UNCLASSIFIED.labels(source).set(count)
        for classification, average in confidence:
            CONFIDENCE.labels(classification).set(average)
    except (OSError, sqlite3.Error):
        DB_UP.set(0)


if __name__ == "__main__":
    start_http_server(PORT, addr="0.0.0.0")
    while True:
        refresh_metrics()
        time.sleep(POLL_SECONDS)
