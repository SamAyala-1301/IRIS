"""
chaos.py — ChaosPanda core engine
Sprint 1 complete

Usage:
  python chaos.py                                         # defaults
  python chaos.py --deployment my-api --namespace prod
  python chaos.py --deployment my-api --replicas 5 --timeout 120
"""

import argparse
import random
import time
import json
import sqlite3
import datetime
import uuid
import sys
from kubernetes import client, config

# ── defaults (overridden by CLI args) ─────────────────────────────────────────
DEFAULTS = {
    "deployment"  : "chaos-target",
    "namespace"   : "default",
    "replicas"    : 3,
    "timeout"     : 60,     # seconds before declaring no_degradation and exiting
    "db"          : "experiments.db",
    "poll_detect" : 1,      # seconds between polls during degradation watch
    "poll_recover": 2,      # seconds between polls during recovery watch
    "streak"      : 3,      # consecutive healthy polls to confirm recovery
}

# ── cli ────────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="ChaosPanda — Kubernetes chaos engine")
    p.add_argument("--deployment", default=DEFAULTS["deployment"],
                   help=f"Target deployment name (default: {DEFAULTS['deployment']})")
    p.add_argument("--namespace",  default=DEFAULTS["namespace"],
                   help=f"Target namespace (default: {DEFAULTS['namespace']})")
    p.add_argument("--replicas",   default=DEFAULTS["replicas"], type=int,
                   help=f"Expected healthy replica count (default: {DEFAULTS['replicas']})")
    p.add_argument("--timeout",    default=DEFAULTS["timeout"], type=int,
                   help=f"Seconds to wait for degradation before aborting (default: {DEFAULTS['timeout']})")
    p.add_argument("--db",         default=DEFAULTS["db"],
                   help=f"SQLite DB path (default: {DEFAULTS['db']})")
    return p.parse_args()

# ── db ─────────────────────────────────────────────────────────────────────────
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

# ── kubernetes helpers ─────────────────────────────────────────────────────────
def count_ready(v1, namespace, deployment):
    """
    Returns count of pods that are:
      - labeled for this deployment
      - not terminating (deletion_timestamp is None)
      - phase == Running
      - all containers reporting ready
    """
    pods = v1.list_namespaced_pod(
        namespace,
        label_selector=f"app={deployment}"
    )
    ready = 0
    for p in pods.items:
        if p.metadata.deletion_timestamp is not None:
            continue
        if p.status.phase != "Running":
            continue
        containers = p.status.container_statuses or []
        if containers and all(cs.ready for cs in containers):
            ready += 1
    return ready

def get_running_pods(v1, namespace, deployment):
    pods = v1.list_namespaced_pod(
        namespace,
        label_selector=f"app={deployment}"
    )
    return [
        p for p in pods.items
        if p.metadata.deletion_timestamp is None
        and p.status.phase == "Running"
    ]

def kill_pod(v1, pod):
    v1.delete_namespaced_pod(pod.metadata.name, pod.metadata.namespace)
    print(f"[CHAOS]  Killed: {pod.metadata.name}")

# ── rca plugin hook ────────────────────────────────────────────────────────────
def rca_hook(experiment_id, db_path):
    """
    Placeholder for RCA-GPT integration.
    When rca.py is ready, replace this with:
        from rca import analyze
        analyze(experiment_id, db_path)
    """
    print(f"[RCA]    Hook ready — experiment {experiment_id} queued for analysis")
    print(f"[RCA]    Plug in rca.py to activate root cause analysis")

# ── main experiment ────────────────────────────────────────────────────────────
def run_experiment(args):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    experiment_id = str(uuid.uuid4())[:8]
    events        = []
    start_time    = time.time()
    now           = datetime.datetime.now(datetime.UTC).isoformat()

    print(f"\n{'='*55}")
    print(f"  ChaosPanda  [{experiment_id}]")
    print(f"  Target  : {args.deployment} / {args.namespace}")
    print(f"  Replicas: {args.replicas}   Timeout: {args.timeout}s")
    print(f"  DB      : {args.db}")
    print(f"{'='*55}\n")

    # 1 — pre-flight
    ready = count_ready(v1, args.namespace, args.deployment)
    print(f"[PRE]    Ready pods: {ready}/{args.replicas}")
    if ready < args.replicas:
        print("[ABORT]  Cluster not fully healthy. Aborting.")
        sys.exit(1)
    events.append({"t": 0, "event": "pre_check_passed", "ready": ready})

    # 2 — kill a random pod
    pods       = get_running_pods(v1, args.namespace, args.deployment)
    target_pod = random.choice(pods)
    kill_pod(v1, target_pod)
    kill_time  = time.time()
    events.append({
        "t"    : round(kill_time - start_time, 2),
        "event": "pod_killed",
        "pod"  : target_pod.metadata.name,
    })

    # 3 — fast-poll for degradation (with timeout guard)
    print(f"\n[DETECT] Polling every {DEFAULTS['poll_detect']}s "
          f"(timeout {args.timeout}s)...")
    ttd = None
    while ttd is None:
        time.sleep(DEFAULTS["poll_detect"])
        elapsed = round(time.time() - kill_time, 2)
        ready   = count_ready(v1, args.namespace, args.deployment)
        print(f"         t+{elapsed:5.1f}s  ready={ready}/{args.replicas}")

        if ready < args.replicas:
            ttd = elapsed
            print(f"[DETECT] Degradation caught — TTD: {ttd}s")
            events.append({
                "t"              : round(time.time() - start_time, 2),
                "event"          : "degradation_detected",
                "ttd_seconds"    : ttd,
                "ready_at_detect": ready,
            })

        elif elapsed > args.timeout:
            # k8s recovered before we could detect degradation
            print(f"[TIMEOUT] No degradation detected in {args.timeout}s")
            print(f"          Pod replaced too fast — consider killing more replicas")
            events.append({"t": elapsed, "event": "no_degradation", "reason": "timeout"})
            con = init_db(args.db)
            write_incident(con, (
                experiment_id, now, args.deployment, args.namespace,
                target_pod.metadata.name, None, None, "no_degradation",
                json.dumps(events),
            ))
            print_last_incident(con)
            con.close()
            rca_hook(experiment_id, args.db)
            return

    # 4 — poll for recovery
    print(f"\n[RECOVER] Polling every {DEFAULTS['poll_recover']}s...")
    streak = 0
    ttr    = None
    while ttr is None:
        time.sleep(DEFAULTS["poll_recover"])
        elapsed = round(time.time() - kill_time, 2)
        ready   = count_ready(v1, args.namespace, args.deployment)
        if ready >= args.replicas:
            streak += 1
            print(f"          t+{elapsed:5.1f}s  ready={ready}  "
                  f"streak={streak}/{DEFAULTS['streak']}")
            if streak >= DEFAULTS["streak"]:
                ttr = elapsed
                print(f"[RECOVER] Confirmed — TTR: {ttr}s")
                events.append({
                    "t"          : round(time.time() - start_time, 2),
                    "event"      : "recovery_confirmed",
                    "ttr_seconds": ttr,
                })
        else:
            print(f"          t+{elapsed:5.1f}s  ready={ready}  streak reset")
            streak = 0

    # 5 — write incident to sqlite
    con = init_db(args.db)
    write_incident(con, (
        experiment_id, now, args.deployment, args.namespace,
        target_pod.metadata.name, ttd, ttr, "completed",
        json.dumps(events),
    ))

    print(f"\n{'='*55}")
    print(f"  Experiment complete  [{experiment_id}]")
    print(f"  TTD : {ttd}s")
    print(f"  TTR : {ttr}s")
    print(f"{'='*55}")

    print_last_incident(con)
    con.close()

    # 6 — rca plugin hook
    rca_hook(experiment_id, args.db)

if __name__ == "__main__":
    run_experiment(parse_args())