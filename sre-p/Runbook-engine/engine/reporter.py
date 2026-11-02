# reporter.py — terminal output + JSON report writer
#
# Two responsibilities:
#   1. Stream live output to terminal as steps execute (colored pass/fail)
#   2. Write a structured JSON report to disk after run completes
#
# The JSON report is what you'd ship to a ticketing system (ServiceNow, Jira)
# or attach to a post-incident review. In a real environment you'd push this
# to S3 or an object store and link it from the incident record.

import json
import os
from datetime import datetime, timezone
from engine.runner import RunResult
from engine.steps import StepResult

# ── ANSI COLOR CODES ──────────────────────────────────────────────────────────
# These render in any modern terminal. If you pipe output to a file,
# use --no-color flag (wired in cli.py) to strip them.
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"

GREEN  = "\033[32m"
RED    = "\033[31m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"
BLUE   = "\033[34m"

STATUS_COLORS = {
    "pass":  GREEN,
    "fail":  RED,
    "skip":  YELLOW,
    "warn":  YELLOW,
}

STATUS_ICONS = {
    "pass":  "✔",
    "fail":  "✘",
    "skip":  "⊘",
    "warn":  "⚠",
}


# ── TERMINAL REPORTER ─────────────────────────────────────────────────────────
class TerminalReporter:

    def __init__(self, color: bool = True):
        self.color = color

    def _c(self, text: str, *codes: str) -> str:
        """Apply color codes if color is enabled."""
        if not self.color:
            return text
        return "".join(codes) + text + RESET

    def print_header(self, runbook_name: str, version: str, triggered_by: str):
        width = 64
        print()
        print(self._c("─" * width, DIM))
        print(self._c(f"  RUNBOOK EXECUTOR", BOLD, CYAN))
        print(self._c(f"  {runbook_name}", BOLD, WHITE))
        print(self._c(f"  version: {version}   triggered by: {triggered_by}", DIM))
        print(self._c("─" * width, DIM))
        print()

    def print_step_start(self, step: dict):
        step_type = self._c(f"[{step['type']}]", DIM)
        name = self._c(step["name"], BOLD)
        print(f"  {step_type} {name} ...", end="", flush=True)

    def print_step_result(self, result: StepResult):
        color = STATUS_COLORS.get(result.status, WHITE)
        icon  = STATUS_ICONS.get(result.status, "?")

        # Overwrite the "..." with the result
        status_str  = self._c(f" {icon} {result.status.upper()}", color, BOLD)
        duration    = self._c(f"  ({result.duration_ms}ms)", DIM)
        print(f"\r  {self._c(f'[{result.step_type}]', DIM)} "
              f"{self._c(result.step_name, BOLD)}"
              f"{status_str}{duration}")

        # Print message indented
        print(f"      {self._c(result.message, DIM)}")

        # Print truncated output if present and step failed or warned
        if result.output and result.status in ("fail", "warn"):
            lines = result.output.strip().splitlines()[:6]
            for line in lines:
                print(f"      {self._c('│', DIM)} {self._c(line, DIM)}")

        print()

    def print_summary(self, result: RunResult):
        width = 64
        color = STATUS_COLORS.get(result.overall_status, WHITE)
        icon  = STATUS_ICONS.get(result.overall_status, "?")

        print(self._c("─" * width, DIM))
        print()
        print(f"  {self._c('RESULT', BOLD)}  "
              f"{self._c(f'{icon} {result.overall_status.upper()}', color, BOLD)}")
        print()
        print(f"  {self._c('Steps', DIM)}    "
              f"{self._c(str(result.steps_total), BOLD)} total  "
              f"{self._c(str(result.steps_passed), GREEN, BOLD)} passed  "
              f"{self._c(str(result.steps_failed), RED, BOLD)} failed  "
              f"{self._c(str(result.steps_skipped), YELLOW, BOLD)} skipped")
        print(f"  {self._c('Duration', DIM)}  "
              f"{self._c(str(result.duration_ms) + 'ms', BOLD)}")
        print(f"  {self._c('Started', DIM)}   {result.started_at}")
        print()

        # Print context snapshot — shows captured values like error rates
        if result.context_snapshot:
            print(f"  {self._c('Context Snapshot', BOLD, CYAN)}")
            for key, val in result.context_snapshot.items():
                print(f"    {self._c(key, DIM)} = {self._c(str(val)[:80], WHITE)}")
            print()

        print(self._c("─" * width, DIM))
        print()


# ── JSON REPORT WRITER ────────────────────────────────────────────────────────
class JSONReporter:

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)

    def write(self, result: RunResult) -> str:
        """
        Writes a JSON report to disk.
        Filename: reports/<runbook_name>_<timestamp>.json
        Returns the path written.

        In production you'd extend this to:
        - POST to ServiceNow incident record
        - Push to S3 with lifecycle policy
        - Attach to PagerDuty incident via API
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_name = result.runbook_name.lower().replace(" ", "_")
        filename  = f"{safe_name}_{timestamp}.json"
        filepath  = os.path.join(self.reports_dir, filename)

        report = result.to_dict()

        # Add report metadata
        report["_report"] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_version": "1.0",
            "engine": "iris-runbook-engine",
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        return filepath

    def print_report_path(self, path: str, color: bool = True):
        dim   = "\033[2m" if color else ""
        cyan  = "\033[36m" if color else ""
        reset = "\033[0m"  if color else ""
        print(f"  {dim}Report saved →{reset} {cyan}{path}{reset}")
        print()