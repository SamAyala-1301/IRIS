"""
rca_gpt/bridge.py — IRIS ecosystem bridge

Polls ~/.iris/iris.db for unclassified ChaosPanda events,
runs them through the RCA-GPT predictor, and stamps the
classification back onto the shared IrisEvent.

Usage:
    python -m rca_gpt.bridge          # run once
    python -m rca_gpt.bridge --watch  # poll every 30s
"""
import time
import argparse


def build_message(event) -> str:
    """
    Convert an IrisEvent into a string the predictor can classify.
    Combines event fields and metadata into a natural log-like message.
    """
    parts = [f"pod_kill"]
    if event.ttd_seconds is not None:
        parts.append(f"ttd={event.ttd_seconds}s")
    if event.ttr_seconds is not None:
        parts.append(f"ttr={event.ttr_seconds}s")
    m = event.metadata or {}
    if m.get("deployment"):
        parts.append(f"deployment={m['deployment']}")
    if m.get("namespace"):
        parts.append(f"namespace={m['namespace']}")
    if m.get("pod_killed"):
        parts.append(f"pod={m['pod_killed']}")
    if m.get("status"):
        parts.append(f"status={m['status']}")
    return " ".join(parts)


def run_once(verbose: bool = True) -> int:
    """
    Classify all unclassified ChaosPanda events.
    Returns the number of events processed.
    """
    from iris_core import IrisStore
    from rca_gpt.predictor import IncidentPredictor

    store     = IrisStore()
    predictor = IncidentPredictor()
    pending   = store.unclassified()

    if not pending:
        if verbose:
            print("[BRIDGE] No unclassified events.")
        return 0

    print(f"[BRIDGE] Found {len(pending)} unclassified event(s)")

    for event in pending:
        message = build_message(event)
        result  = predictor.predict(message)

        classification = result["incident_type"]
        confidence     = round(result["confidence"], 4)

        store.update_classification(event.id, classification, confidence)

        print(
            f"[BRIDGE] {event.id} → "
            f"{classification} ({confidence:.0%}) | "
            f"TTD={event.ttd_seconds}s TTR={event.ttr_seconds}s"
        )

    return len(pending)


def run_watch(interval: int = 30):
    """Poll for unclassified events on a fixed interval."""
    print(f"[BRIDGE] Watching ~/.iris/iris.db every {interval}s — Ctrl+C to stop")
    while True:
        try:
            run_once(verbose=False)
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[BRIDGE] Stopped.")
            break


def main():
    p = argparse.ArgumentParser(description="RCA-GPT ↔ IRIS bridge")
    p.add_argument("--watch",    action="store_true",
                   help="Poll continuously instead of running once")
    p.add_argument("--interval", type=int, default=30,
                   help="Poll interval in seconds (default: 30)")
    args = p.parse_args()

    if args.watch:
        run_watch(args.interval)
    else:
        processed = run_once()
        print(f"[BRIDGE] Done — {processed} event(s) classified")


if __name__ == "__main__":
    main()