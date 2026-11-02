# Database Documentation

## Overview

RCA-GPT uses SQLite to store incident data persistently. The database automatically deduplicates incidents using fingerprinting and tracks historical occurrences.

## Schema

### Table: `incidents`

Stores unique incidents (deduplicated by fingerprint).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment unique ID |
| fingerprint | TEXT UNIQUE | SHA256 hash for deduplication |
| incident_type | TEXT | Classification (Auth Error, Timeout, etc.) |
| severity | TEXT | Log level (INFO, WARN, ERROR) |
| message_template | TEXT | Normalized message pattern |
| first_seen | TIMESTAMP | When first detected |
| last_seen | TIMESTAMP | Most recent occurrence |
| occurrence_count | INTEGER | Total times seen |
| created_at | TIMESTAMP | Record creation time |

**Indexes:**
- `fingerprint` (UNIQUE)
- `incident_type`

### Table: `incident_occurrences`

Stores each individual occurrence with full context.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment unique ID |
| incident_id | INTEGER | Foreign key to incidents |
| timestamp | TIMESTAMP | When this occurred |
| log_level | TEXT | Log severity |
| full_message | TEXT | Complete log message |
| context_before | TEXT | JSON: 5 logs before incident |
| context_after | TEXT | JSON: 5 logs after incident |
| resolved | BOOLEAN | Resolution status |
| resolution_notes | TEXT | How it was fixed |
| resolved_at | TIMESTAMP | When marked resolved |
| resolved_by | TEXT | Who resolved it |
| created_at | TIMESTAMP | Record creation time |

**Indexes:**
- `incident_id`
- `timestamp`

**Relationships:**
- `incident_id` → `incidents.id` (many-to-one)

### Table: `incident_stats`

Daily aggregated statistics (future use).

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment unique ID |
| date | DATE | Stats date |
| incident_type | TEXT | Incident classification |
| total_count | INTEGER | Occurrences that day |
| unique_count | INTEGER | Unique incidents |
| avg_resolution_time | FLOAT | Average seconds to resolve |
| created_at | TIMESTAMP | Record creation time |

**Indexes:**
- `date`

## Fingerprinting

Incidents are deduplicated using SHA256 fingerprints generated from:
1. Incident type
2. Normalized message (lowercase, numbers removed, whitespace normalized)

Example:
```python
message = "Connection timeout after 5000ms"
normalized = "connection timeout after ms"
fingerprint = sha256("Timeout:connection timeout after ms")
```

This ensures similar messages are grouped together.

## Context Storage

Each occurrence stores surrounding logs as JSON:
```json
{
  "context_before": [
    {"level": "INFO", "timestamp": "...", "message": "Starting request"},
    {"level": "INFO", "timestamp": "...", "message": "Loading data"}
  ],
  "context_after": [
    {"level": "ERROR", "timestamp": "...", "message": "Request failed"}
  ]
}
```

Context helps with root cause analysis by showing what happened before/after.

## Querying Examples

### Python API
```python
from rca_gpt.db.manager import IncidentDatabase

db = IncidentDatabase()

# Get recent incidents
incidents = db.get_recent_incidents(limit=50)

# Get incidents in time range
from datetime import datetime, timedelta
start = datetime.utcnow() - timedelta(days=7)
incidents = db.get_incidents_in_timerange(start)

# Get statistics
stats = db.get_incident_stats(days=30)

# Search
results = db.search_incidents("timeout")

# Mark resolved
db.mark_resolved(
    occurrence_id=15,
    resolution_notes="Restarted service",
    resolved_by="ops_team"
)
```

### CLI
```bash
# View recent
rca-gpt history --days 7

# View details
rca-gpt show 42 --verbose

# Statistics
rca-gpt stats --days 30 --top 10

# Search
rca-gpt search "connection"

# Resolve
rca-gpt resolve 15 "Fixed by restarting Redis"

# Export
rca-gpt export --days 7 -o incidents.json
```

## Backup & Restore

### Backup
```bash
python -m rca_gpt.db.backup backup
```

Creates timestamped backup in `data/backups/`.

### List Backups
```bash
python -m rca_gpt.db.backup list
```

### Restore
```bash
python -m rca_gpt.db.backup restore data/backups/incidents_backup_20250112_143022.db
```

## Performance

- **Fingerprint index** enables fast deduplication checks
- **Timestamp index** speeds up time-range queries
- **Type index** allows efficient filtering by incident type
- SQLite handles 100K+ incidents efficiently

## Migration

If schema changes are needed in future sprints:

1. Create migration script in `rca_gpt/db/migrations/`
2. Version the schema
3. Apply migrations on startup

Example migration structure:
```python
# migrations/001_add_severity_column.py
def upgrade(engine):
    engine.execute("ALTER TABLE incidents ADD COLUMN severity TEXT")

def downgrade(engine):
    engine.execute("ALTER TABLE incidents DROP COLUMN severity")
```

## File Location

Default: `data/incidents.db`

Change in `config/config.yaml`:
```yaml
database:
  path: /custom/path/incidents.db
```

## Troubleshooting

### Database locked
SQLite uses file-level locking. Ensure only one process writes at a time.

### Large database size
Export old incidents and archive:
```bash
rca-gpt export --days 365 -o archive_2024.json
# Manually delete old records from DB
```

### Corrupted database
Restore from backup:
```bash
python -m rca_gpt.db.backup list
python -m rca_gpt.db.backup restore <backup_file>
```