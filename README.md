# IRIS — Incident Response Intelligence System

IRIS is a collection of incident response tools brought together in one monorepo. Its modules detect failures, share incident events, classify root causes, visualize operations, run response playbooks, and enrich ServiceNow tickets.

## Ecosystem flow

1. **ChaosPanda** injects controlled failures and emits experiment events.
2. **iris-core** provides the shared event contract and local SQLite event store.
3. **RCA-GPT** reads events and classifies likely root causes.
4. **Observability Stack** visualizes operational signals and incident trends.
5. **SRE-P** runs operational runbooks and supports service-level objectives.
6. **CIIA-Enrichment** independently enriches ServiceNow incidents using Groq-hosted Llama 3.1. It is a separate ticket workflow, not a required step in the event-processing path.

```text
ChaosPanda → iris-core event store → RCA-GPT → Observability Stack
                                      SRE-P runs response playbooks

CIIA-Enrichment → ServiceNow ticket enrichment (independent workflow)
```

## Repository layout

```text
iris-core/             Shared Python event model and SQLite store
chaos-panda/           Chaos experiments and event production
rca-gpt/               Root-cause classification
observability-stack/   Metrics, dashboards, and visualizations
ciia-enrichment/       ServiceNow ticket enrichment service
sre-p/                 Runbooks and SLO tooling
```

Each module's Git history is included in this repository through Git subtree imports. The `../_src-*` folders are local safety backups; keep them until the consolidation and deployment are verified.

## iris-core development install

From the repository root, with the desired Python environment active:

```sh
python -m pip install -e ./iris-core
python -c 'import iris_core; print(iris_core.__file__)'
```

The editable install makes the shared package available to the other modules in that environment.

## CIIA deployment note

CIIA is deployed separately on Vercel. Its Vercel project should use `ciia-enrichment/` as its Root Directory when connected to this monorepo. Keep credentials in Vercel environment settings or a local ignored `.env` file; never commit environment files or credential values.

## Local data and secrets

The root `.gitignore` excludes environment files, Python caches and environments, Node dependencies, local databases, and build artifacts. Copy any required local `.env` values back into the relevant module after checkout; use the deployment platform's environment settings for production.
