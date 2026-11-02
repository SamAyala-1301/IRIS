# cli.py — entry point for the runbook engine
#
# Usage:
#   python cli.py run runbooks/claims_api_p1.yaml
#   python cli.py run runbooks/claims_api_p1.yaml --triggered-by sam
#   python cli.py run runbooks/claims_api_p1.yaml --no-color
#   python cli.py list runbooks/
#   python cli.py validate runbooks/claims_api_p1.yaml

import sys
import os
import argparse
import yaml

# Add parent directory to path so engine imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.runner import RunbookRunner
from engine.reporter import TerminalReporter, JSONReporter


def cmd_run(args):
    color = not args.no_color
    terminal = TerminalReporter(color=color)
    json_reporter = JSONReporter(reports_dir=args.reports_dir)

    try:
        runner = RunbookRunner(
            runbook_path=args.runbook,
            triggered_by=args.triggered_by,
        )
    except FileNotFoundError:
        print(f"\n  ✘ Runbook not found: {args.runbook}\n")
        sys.exit(1)
    except ValueError as e:
        print(f"\n  ✘ Runbook validation error: {e}\n")
        sys.exit(1)

    runbook = runner.runbook
    terminal.print_header(
        runbook_name=runbook["name"],
        version=str(runbook["version"]),
        triggered_by=args.triggered_by,
    )

    # We need to intercept step execution to stream live output.
    # RunbookRunner.run() executes all steps internally, so we
    # monkey-patch the handler registry to wrap each call with
    # terminal output before/after.
    from engine import steps as steps_module

    original_handlers = dict(steps_module.STEP_HANDLERS)

    def make_wrapped(handler, step_dict):
        def wrapped(step, context):
            terminal.print_step_start(step)
            result = handler(step, context)
            terminal.print_step_result(result)
            return result
        return wrapped

    # Wrap each handler to print live output
    for step in runbook["steps"]:
        step_type = step["type"]
        if step_type in steps_module.STEP_HANDLERS:
            original = original_handlers[step_type]
            steps_module.STEP_HANDLERS[step_type] = make_wrapped(original, step)

    try:
        result = runner.run()
    finally:
        # Always restore original handlers
        steps_module.STEP_HANDLERS.update(original_handlers)

    terminal.print_summary(result)

    # Write JSON report
    report_path = json_reporter.write(result)
    json_reporter.print_report_path(report_path, color=color)

    # Exit code reflects overall status — useful for CI/CD pipelines
    sys.exit(0 if result.overall_status == "pass" else 1)


def cmd_validate(args):
    try:
        runner = RunbookRunner(args.runbook)
        print(f"\n  ✔ Runbook valid: {args.runbook}")
        print(f"    Name:    {runner.runbook['name']}")
        print(f"    Version: {runner.runbook['version']}")
        print(f"    Steps:   {len(runner.runbook['steps'])}")
        steps = [f"{s['name']} ({s['type']})" for s in runner.runbook["steps"]]
        for i, s in enumerate(steps):
            print(f"      {i+1}. {s}")
        print()
    except Exception as e:
        print(f"\n  ✘ Invalid runbook: {e}\n")
        sys.exit(1)


def cmd_list(args):
    runbooks_dir = args.directory
    if not os.path.isdir(runbooks_dir):
        print(f"\n  ✘ Directory not found: {runbooks_dir}\n")
        sys.exit(1)

    files = [f for f in os.listdir(runbooks_dir) if f.endswith(".yaml")]
    if not files:
        print(f"\n  No runbooks found in {runbooks_dir}\n")
        return

    print(f"\n  Runbooks in {runbooks_dir}:\n")
    for fname in sorted(files):
        fpath = os.path.join(runbooks_dir, fname)
        try:
            with open(fpath) as f:
                data = yaml.safe_load(f)
            name    = data.get("name", "unknown")
            version = data.get("version", "?")
            desc    = data.get("description", "")
            steps   = len(data.get("steps", []))
            print(f"  • {fname}")
            print(f"    {name} v{version} — {steps} steps")
            if desc:
                print(f"    {desc}")
            print()
        except Exception as e:
            print(f"  • {fname}  ✘ parse error: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="runbook",
        description="Insurance SRE — Runbook Automation Engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    run_parser = sub.add_parser("run", help="Execute a runbook")
    run_parser.add_argument("runbook", help="Path to runbook YAML")
    run_parser.add_argument("--triggered-by", default="cli", help="Who triggered this run")
    run_parser.add_argument("--no-color", action="store_true", help="Disable colored output")
    run_parser.add_argument("--reports-dir", default="reports", help="Directory to write JSON reports")
    run_parser.set_defaults(func=cmd_run)

    # validate
    val_parser = sub.add_parser("validate", help="Validate a runbook without executing")
    val_parser.add_argument("runbook", help="Path to runbook YAML")
    val_parser.set_defaults(func=cmd_validate)

    # list
    list_parser = sub.add_parser("list", help="List available runbooks")
    list_parser.add_argument("directory", nargs="?", default="runbooks", help="Runbooks directory")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()