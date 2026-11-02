CREATE TABLE IF NOT EXISTS iris_events (
    id             TEXT PRIMARY KEY,
    source         TEXT NOT NULL,
    event_type     TEXT NOT NULL,
    timestamp      TEXT NOT NULL,
    severity       TEXT NOT NULL,
    ttd_seconds    REAL,
    ttr_seconds    REAL,
    classification TEXT,
    confidence     REAL,
    metadata       TEXT
);

CREATE INDEX IF NOT EXISTS idx_source    ON iris_events (source);
CREATE INDEX IF NOT EXISTS idx_timestamp ON iris_events (timestamp);
CREATE INDEX IF NOT EXISTS idx_severity  ON iris_events (severity);