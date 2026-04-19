# IRIS-Core

Shared event contract for the **IRIS Incident Intelligence Ecosystem**.

IRIS is a portfolio of tools that detect, classify, enrich, and visualize production incidents. This package is the data layer that makes them work as a unified system instead of isolated tools.

---

## 🧩 The Problem

Modern incident tooling often operates in silos:

- Chaos tools generate experiment data but don’t connect to incident systems
- ML classifiers analyze logs but don’t see infrastructure signals
- Ticketing systems contain context but lack structured telemetry
- Observability dashboards show metrics without incident intelligence

Result: **No shared memory. No feedback loop. No system-wide intelligence.**

---

## 💡 The Solution

IRIS-Core defines a **single shared event model** and a **central local store**.

All tools write to and read from the same contract.

### Data Flow

ChaosPanda → emits experiment events  
↓  
IRIS store (`~/.iris/iris.db`)  
↓  
RCA-GPT → classifies incidents  
↓  
CIIA → enriches tickets  
↓  
Observability Stack → visualizes trends

This creates a **closed feedback loop** across the entire incident lifecycle.

---

## 📦 Installation

```bash
pip install -e .
```

Or from another repo:

```bash
pip install -e /path/to/IRIS-Core
```

---

## 🧱 IrisEvent

Core data structure shared across all tools:

```python
from iris_core import IrisEvent

event = IrisEvent(
    source      = "chaospanda",        # chaospanda | rca-gpt | ciia | obs-stack
    event_type  = "pod_kill",          # pod_kill | rca_classified | ticket_enriched | metric_anomaly
    severity    = "degraded",          # healthy | degraded | critical
    ttd_seconds = 1.03,
    ttr_seconds = 7.09,
    metadata    = {
        "deployment": "chaos-target",
        "namespace" : "default",
        "pod_killed": "chaos-target-abc123",
    }
)
```

### Fields added by RCA-GPT

```python
event.classification  # "Timeout" | "Auth Error" | "DB Error"
event.confidence      # 0.87
```

---

## 🗄️ IrisStore

Lightweight shared storage layer (SQLite):

```python
from iris_core import IrisStore

store = IrisStore()              # defaults to ~/.iris/iris.db

store.write(event)               # write event
store.unclassified()             # fetch events without classification
store.update_classification(     # update classification
    event_id       = "9992a840",
    classification = "Timeout",
    confidence     = 0.87,
)
store.latest(n=10)               # fetch latest events
store.get(event_id)              # fetch by ID
```

---

## 🧾 Schema

```sql
CREATE TABLE iris_events (
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
```

Database location:

```
~/.iris/iris.db
```

Persists across repos and is shared by all tools on the same machine.

---

## 🌐 IRIS Ecosystem

| Tool | Role |
|------|------|
| **IRIS-Core** | Shared event contract (this repo) |
| **ChaosPanda** | Chaos engine — emits events |
| **RCA-GPT** | ML classifier — enriches events |
| **CIIA** | Ticket enrichment agent |
| **Observability Stack** | Dashboards + metrics visualization |

---

## 🧠 Design Principles

- **Single source of truth** — all tools share one event model
- **Loose coupling** — tools communicate via data, not direct dependencies
- **Extensibility** — new tools can join by reading/writing IrisEvents
- **Local-first** — runs entirely on developer machine (no cloud dependency)

---

## 👤 Author

Sai Sampath Ayalasomayajula — L3 Production Support Engineer  
Built to solve a real problem: incident systems that couldn’t talk to each other.
