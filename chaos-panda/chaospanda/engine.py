"""
chaospanda/engine.py — core experiment runner
"""
import random
import time
import json
import datetime
import uuid
import sys

from .k8s import load_cluster, count_ready, get_running_pods, kill_pod
from .db  import init_db, write_incident, print_last_incident

DEFAULTS = {
    "deployment"  : "chaos-target",
    "namespace"   : "default",
    "replicas"    : 3,
    "timeout"     : 60,
    "db"          : "experiments.db",
    "poll_detect" : 1,
    "poll_recover": 2,
    "streak"      : 3,
}


def iris_hook(experiment_id, deployment, namespace, pod_killed, ttd, ttr, status):
    """
    Emit an IrisEvent to the shared IRIS store.
    Gracefully no-ops if iris-core is not installed.
    """
    try:
        from iris_core import IrisEvent, IrisStore
        severity = "degraded" if status == "completed" else "healthy"
        event = IrisEvent(
            id         = experiment_id,
            source     = "chaospanda",
            event_type = "pod_kill",
            severity   = severity,
            ttd_seconds = ttd,
            ttr_seconds = ttr,
            metadata   = {
                "deployment": deployment,
                "namespace" : namespace,
                "pod_killed": pod_killed,
                "status"    : status,
            }
        )
        IrisStore().write(event)
        print(f"[IRIS]   Event written → {event.id} | severity={severity}")
    except Exception as e:
        print(f"[IRIS]   Skipped — {e}")


def run_experiment(args):
    v1 = load_cluster()

    experiment_id = str(uuid.uuid4())[:8]
    events        = []
    start_time    = time.time()
    now           = datetime.datetime.now(datetime.timezone.utc).isoformat()

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

    # 3 — fast-poll for degradation
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
            print(f"[TIMEOUT] No degradation detected in {args.timeout}s")
            events.append({"t": elapsed, "event": "no_degradation", "reason": "timeout"})
            con = init_db(args.db)
            write_incident(con, (
                experiment_id, now, args.deployment, args.namespace,
                target_pod.metadata.name, None, None, "no_degradation",
                json.dumps(events),
            ))
            print_last_incident(con)
            con.close()
            iris_hook(experiment_id, args.deployment, args.namespace,
                      target_pod.metadata.name, None, None, "no_degradation")
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

    # 5 — write to experiments.db
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

    # 6 — emit IrisEvent to shared store
    iris_hook(experiment_id, args.deployment, args.namespace,
              target_pod.metadata.name, ttd, ttr, "completed")
