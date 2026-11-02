# IRIS event store exporter

This service opens `IRIS_HOME/iris.db` in SQLite read-only mode and exposes aggregate event and RCA classification metrics to Prometheus on the internal `obs-stack` network. It does not publish a host port or expose event IDs, metadata, or other raw event contents.

The exporter reports event counts by source, event type, severity, and classification; the number awaiting RCA-GPT; and average classification confidence. Grafana provisions these metrics in the **IRIS Event Store** dashboard.

For the normal local store, start the service with:

```zsh
IRIS_HOME="$HOME/.iris" docker compose -p iris-observability -f observability-stack/v3/backend/docker-compose.yml up -d --build iris-events-exporter
```

`IRIS_HOME` must already exist. The bind mount is read-only and is not created automatically. Prometheus scrapes the exporter inside the Compose network.
