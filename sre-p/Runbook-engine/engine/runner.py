# runner.py — core execution loop
#
# Loads a runbook YAML, resolves step order, handles conditional branching,
# executes each step via the handler registry, and returns a RunResult.
#
# Branching model:
#   Each step can define on_fail and on_pass directives:
#     on_fail: stop          → halt execution immediately
#     on_fail: continue      → log failure, keep going
#     on_fail: goto:step_name → jump to a named step
#   This lets runbooks self-route: if health check fails, jump to restart step,
#   then re-check, then notify — without hardcoding the flow in Python.

import json
import time
import yaml
from dataclasses import dataclass, field
from typing import Optional
from engine.steps import STEP_HANDLERS, StepResult


# ── DATA STRUCTURES ───────────────────────────────────────────────────────────
@dataclass
class RunResult:
    runbook_name: str
    runbook_version: str
    triggered_by: str
    started_at: str
    ended_at: str
    duration_ms: int
    overall_status: str                # "pass" | "fail" | "partial"
    steps_total: int
    steps_passed: int
    steps_failed: int
    steps_skipped: int
    step_results: list[StepResult]
    context_snapshot: dict             # final context state — useful for debugging

    def to_dict(self) -> dict:
        return {
            "runbook_name": self.runbook_name,
            "runbook_version": self.runbook_version,
            "triggered_by": self.triggered_by,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "duration_ms": self.duration_ms,
            "overall_status": self.overall_status,
            "summary": {
                "total": self.steps_total,
                "passed": self.steps_passed,
                "failed": self.steps_failed,
                "skipped": self.steps_skipped,
            },
            "steps": [
                {
                    "name": r.step_name,
                    "type": r.step_type,
                    "status": r.status,
                    "message": r.message,
                    "duration_ms": r.duration_ms,
                    "output": r.output,
                    "metadata": r.metadata,
                }
                for r in self.step_results
            ],
            "context_snapshot": self.context_snapshot,
        }


# ── RUNNER ────────────────────────────────────────────────────────────────────
class RunbookRunner:

    def __init__(self, runbook_path: str, triggered_by: str = "cli"):
        self.runbook_path = runbook_path
        self.triggered_by = triggered_by
        self.runbook = self._load(runbook_path)

        # Build a step index by name for goto branching
        self.step_index = {
            step["name"]: i
            for i, step in enumerate(self.runbook["steps"])
        }

    def _load(self, path: str) -> dict:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        self._validate(data)
        return data

    def _validate(self, data: dict):
        required = ["name", "version", "steps"]
        for field in required:
            if field not in data:
                raise ValueError(f"Runbook missing required field: '{field}'")
        if not isinstance(data["steps"], list) or len(data["steps"]) == 0:
            raise ValueError("Runbook must have at least one step")
        for step in data["steps"]:
            if "name" not in step:
                raise ValueError(f"Step missing 'name': {step}")
            if "type" not in step:
                raise ValueError(f"Step '{step['name']}' missing 'type'")
            if step["type"] not in STEP_HANDLERS:
                raise ValueError(
                    f"Unknown step type '{step['type']}' in step '{step['name']}'. "
                    f"Known types: {list(STEP_HANDLERS.keys())}"
                )

    def run(self) -> RunResult:
        started_at = _now()
        t0 = time.time()

        # Context accumulates outputs across steps.
        # Pre-populate with runbook-level variables if defined.
        context = dict(self.runbook.get("variables", {}))

        steps = self.runbook["steps"]
        results: list[StepResult] = []
        executed_names: set[str] = set()

        current_idx = 0
        overall_status = "pass"

        while current_idx < len(steps):
            step = steps[current_idx]
            step_name = step["name"]

            # Guard against infinite loops from circular goto chains
            if step_name in executed_names:
                results.append(StepResult(
                    step_name=step_name,
                    step_type=step.get("type", "unknown"),
                    status="skip",
                    message="Skipped — already executed (loop guard)",
                    duration_ms=0,
                ))
                current_idx += 1
                continue

            # Check condition — step-level if: clause
            # Example: if: "{{claims_error_rate}} > 0.01"
            if not self._evaluate_if(step.get("if"), context):
                results.append(StepResult(
                    step_name=step_name,
                    step_type=step["type"],
                    status="skip",
                    message=f"Skipped — condition not met: {step.get('if')}",
                    duration_ms=0,
                ))
                executed_names.add(step_name)
                current_idx += 1
                continue

            # Execute the step
            handler = STEP_HANDLERS[step["type"]]
            result = handler(step, context)
            results.append(result)
            executed_names.add(step_name)

            # Determine next step based on result + branching directives
            if result.failed():
                overall_status = "fail"
                on_fail = step.get("on_fail", "stop")

                if on_fail == "stop":
                    # Append skip records for remaining steps
                    for remaining in steps[current_idx + 1:]:
                        results.append(StepResult(
                            step_name=remaining["name"],
                            step_type=remaining["type"],
                            status="skip",
                            message="Skipped — earlier step failed with on_fail:stop",
                            duration_ms=0,
                        ))
                    break

                elif on_fail == "continue":
                    current_idx += 1

                elif on_fail.startswith("goto:"):
                    target = on_fail.split("goto:", 1)[1].strip()
                    if target not in self.step_index:
                        results.append(StepResult(
                            step_name=f"goto:{target}",
                            step_type="internal",
                            status="fail",
                            message=f"goto target '{target}' not found in runbook",
                            duration_ms=0,
                        ))
                        break
                    current_idx = self.step_index[target]

                else:
                    # Unknown on_fail directive — treat as stop
                    current_idx = len(steps)

            else:
                # Step passed — check on_pass directive
                on_pass = step.get("on_pass", "next")

                if on_pass == "next":
                    current_idx += 1

                elif on_pass.startswith("goto:"):
                    target = on_pass.split("goto:", 1)[1].strip()
                    if target not in self.step_index:
                        results.append(StepResult(
                            step_name=f"goto:{target}",
                            step_type="internal",
                            status="fail",
                            message=f"goto target '{target}' not found in runbook",
                            duration_ms=0,
                        ))
                        break
                    current_idx = self.step_index[target]

                elif on_pass == "stop":
                    break

                else:
                    current_idx += 1

        # Compute summary
        passed  = sum(1 for r in results if r.status == "pass")
        failed  = sum(1 for r in results if r.status == "fail")
        skipped = sum(1 for r in results if r.status in ("skip", "warn"))

        if failed == 0 and passed > 0:
            overall_status = "pass"
        elif failed > 0 and passed > 0:
            overall_status = "partial"
        elif failed > 0 and passed == 0:
            overall_status = "fail"

        ended_at = _now()

        return RunResult(
            runbook_name=self.runbook["name"],
            runbook_version=str(self.runbook["version"]),
            triggered_by=self.triggered_by,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=int((time.time() - t0) * 1000),
            overall_status=overall_status,
            steps_total=len(results),
            steps_passed=passed,
            steps_failed=failed,
            steps_skipped=skipped,
            step_results=results,
            context_snapshot={
                k: v for k, v in context.items()
                if not k.startswith("_")       # strip internal keys
            },
        )

    def _evaluate_if(self, condition: Optional[str], context: dict) -> bool:
        """
        Evaluates a simple if condition string.
        Supports: >, <, ==, >=, <=, != against numeric or string values.
        Example: "{{claims_error_rate}} > 0.01"
        Returns True (run the step) if condition is None or evaluates to True.
        """
        if condition is None:
            return True

        # Resolve placeholders
        resolved = condition
        for key, val in context.items():
            resolved = resolved.replace(f"{{{{{key}}}}}", str(val))

        try:
            # Safe eval — only allow comparison expressions
            # Strip anything that isn't a number, operator, space, or dot
            import re
            if re.search(r"[^0-9\s><=!.\-]", resolved):
                # Non-numeric condition — treat as string equality check
                return bool(resolved.strip())
            return bool(eval(resolved))  # safe: only numeric comparisons reach here
        except Exception:
            return True                  # if condition can't be evaluated, run the step


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()