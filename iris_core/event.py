"""
IrisEvent — shared event format for the IRIS ecosystem.
All four tools speak this format.
"""
import json
import uuid
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional


VALID_SOURCES     = {"chaospanda", "rca-gpt", "ciia", "obs-stack"}
VALID_SEVERITIES  = {"healthy", "degraded", "critical"}
VALID_EVENT_TYPES = {
    "pod_kill",
    "rca_classified",
    "ticket_enriched",
    "metric_anomaly",
}


@dataclass
class IrisEvent:
    source:         str
    event_type:     str
    severity:       str
    id:             str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp:      str   = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    ttd_seconds:    Optional[float] = None
    ttr_seconds:    Optional[float] = None
    classification: Optional[str]   = None
    confidence:     Optional[float] = None
    metadata:       dict            = field(default_factory=dict)

    def __post_init__(self):
        if self.source not in VALID_SOURCES:
            raise ValueError(f"Invalid source '{self.source}'. Must be one of {VALID_SOURCES}")
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{self.severity}'. Must be one of {VALID_SEVERITIES}")
        if self.event_type not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type '{self.event_type}'. Must be one of {VALID_EVENT_TYPES}")

    def to_row(self) -> tuple:
        """Return a tuple for direct SQLite insertion."""
        return (
            self.id,
            self.source,
            self.event_type,
            self.timestamp,
            self.severity,
            self.ttd_seconds,
            self.ttr_seconds,
            self.classification,
            self.confidence,
            json.dumps(self.metadata),
        )

    @classmethod
    def from_row(cls, row: tuple) -> "IrisEvent":
        """Reconstruct an IrisEvent from a SQLite row."""
        return cls(
            id             = row[0],
            source         = row[1],
            event_type     = row[2],
            timestamp      = row[3],
            severity       = row[4],
            ttd_seconds    = row[5],
            ttr_seconds    = row[6],
            classification = row[7],
            confidence     = row[8],
            metadata       = json.loads(row[9]) if row[9] else {},
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        return d