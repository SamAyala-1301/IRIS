
"""
chaospanda/cli.py — argument parsing entry point
"""
import argparse
from .engine import run_experiment, DEFAULTS


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


def main():
    run_experiment(parse_args())


if __name__ == "__main__":
    main()