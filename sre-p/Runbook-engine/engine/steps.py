# steps.py — every step type the runbook engine knows how to execute
#
# Each handler receives a step dict from the YAML and a context dict
# that accumulates outputs across steps (used for conditional branching).
# Every handler returns a StepResult.

import re
import json
import time
import subprocess
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class StepResult:
    step_name: str
    step_type: str
    status: str                        # "pass" | "fail" | "skip" | "warn"
    message: str
    output: Optional[str] = None       # raw output captured (logs, command stdout)
    duration_ms: int = 0
    metadata: dict = field(default_factory=dict)

    def passed(self): return self.status == "pass"
    def failed(self): return self.status == "fail"


# ── STEP: http_check ──────────────────────────────────────────────────────────
# Hits an HTTP endpoint and validates status code + optional response body match.
# Used for: health checks, readiness probes, API smoke tests.
#
# YAML shape:
#   type: http_check
#   url: http://localhost:5000/health
#   expect_status: 200
#   expect_body_contains: "ok"        # optional
#   timeout_seconds: 5                # optional, default 5
def run_http_check(step: dict, context: dict) -> StepResult:
    t0 = time.time()
    url = _resolve(step["url"], context)
    expect_status = step.get("expect_status", 200)
    expect_body = step.get("expect_body_contains")
    timeout = step.get("timeout_seconds", 5)

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status_code = resp.status

        if status_code != expect_status:
            return StepResult(
                step_name=step["name"], step_type="http_check",
                status="fail",
                message=f"Expected HTTP {expect_status}, got {status_code}",
                output=body[:500],
                duration_ms=_ms(t0),
            )

        if expect_body and expect_body not in body:
            return StepResult(
                step_name=step["name"], step_type="http_check",
                status="fail",
                message=f"Response body missing expected string: '{expect_body}'",
                output=body[:500],
                duration_ms=_ms(t0),
            )

        # Store response body in context so later steps can branch on it
        context[f"{step['name']}.body"] = body
        context[f"{step['name']}.status_code"] = status_code

        return StepResult(
            step_name=step["name"], step_type="http_check",
            status="pass",
            message=f"HTTP {status_code} — endpoint healthy",
            output=body[:200],
            duration_ms=_ms(t0),
        )

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return StepResult(
            step_name=step["name"], step_type="http_check",
            status="fail",
            message=f"HTTP {e.code}: {e.reason}",
            output=body[:500],
            duration_ms=_ms(t0),
        )
    except Exception as e:
        return StepResult(
            step_name=step["name"], step_type="http_check",
            status="fail",
            message=f"Connection failed: {e}",
            duration_ms=_ms(t0),
        )


# ── STEP: shell ───────────────────────────────────────────────────────────────
# Runs a shell command. Captures stdout+stderr.
# Used for: kubectl commands, log tailing, service restarts, disk checks.
# CRITICAL: never use this with untrusted input — shell=True is intentional
# here for runbook flexibility but must be restricted to trusted operators.
#
# YAML shape:
#   type: shell
#   command: "kubectl get pods -n insurance | grep claims"
#   expect_exit_code: 0               # optional, default 0
#   timeout_seconds: 30               # optional, default 30
#   capture_as: pods_output           # optional — store stdout in context
def run_shell(step: dict, context: dict) -> StepResult:
    t0 = time.time()
    command = _resolve(step["command"], context)
    expect_exit = step.get("expect_exit_code", 0)
    timeout = step.get("timeout_seconds", 30)
    capture_as = step.get("capture_as")

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout + result.stderr).strip()

        if capture_as:
            context[capture_as] = output

        if result.returncode != expect_exit:
            return StepResult(
                step_name=step["name"], step_type="shell",
                status="fail",
                message=f"Exit code {result.returncode}, expected {expect_exit}",
                output=output[:1000],
                duration_ms=_ms(t0),
                metadata={"command": command, "exit_code": result.returncode},
            )

        return StepResult(
            step_name=step["name"], step_type="shell",
            status="pass",
            message=f"Command succeeded (exit 0)",
            output=output[:1000],
            duration_ms=_ms(t0),
            metadata={"command": command},
        )

    except subprocess.TimeoutExpired:
        return StepResult(
            step_name=step["name"], step_type="shell",
            status="fail",
            message=f"Command timed out after {timeout}s",
            duration_ms=_ms(t0),
            metadata={"command": command},
        )
    except Exception as e:
        return StepResult(
            step_name=step["name"], step_type="shell",
            status="fail",
            message=f"Execution error: {e}",
            duration_ms=_ms(t0),
        )


# ── STEP: log_grep ────────────────────────────────────────────────────────────
# Searches a log file or docker container logs for a pattern.
# Used for: finding error spikes, confirming restarts, finding OOM events.
#
# YAML shape:
#   type: log_grep
#   source: file                      # "file" | "docker"
#   target: /var/log/claims-api.log   # file path or container name
#   pattern: "ERROR|FATAL|OOM"        # regex
#   last_lines: 200                   # optional, default 100
#   fail_if_found: false              # optional — fail if pattern IS found
#   capture_as: error_lines
def run_log_grep(step: dict, context: dict) -> StepResult:
    t0 = time.time()
    source = step.get("source", "file")
    target = _resolve(step["target"], context)
    pattern = step["pattern"]
    last_lines = step.get("last_lines", 100)
    fail_if_found = step.get("fail_if_found", False)
    capture_as = step.get("capture_as")

    try:
        if source == "docker":
            result = subprocess.run(
                f"docker logs --tail {last_lines} {target} 2>&1",
                shell=True, capture_output=True, text=True, timeout=15
            )
            lines = result.stdout + result.stderr
        else:
            with open(target, "r", errors="replace") as f:
                all_lines = f.readlines()
            lines = "".join(all_lines[-last_lines:])

        regex = re.compile(pattern, re.IGNORECASE)
        matches = [l.strip() for l in lines.splitlines() if regex.search(l)]
        match_count = len(matches)
        matched_output = "\n".join(matches[:20])  # cap at 20 lines in output

        if capture_as:
            context[capture_as] = matched_output

        if fail_if_found and match_count > 0:
            return StepResult(
                step_name=step["name"], step_type="log_grep",
                status="fail",
                message=f"Found {match_count} line(s) matching '{pattern}' — unexpected",
                output=matched_output,
                duration_ms=_ms(t0),
                metadata={"match_count": match_count, "pattern": pattern},
            )

        if not fail_if_found and match_count == 0:
            return StepResult(
                step_name=step["name"], step_type="log_grep",
                status="warn",
                message=f"No lines matched '{pattern}' — expected to find some",
                duration_ms=_ms(t0),
                metadata={"match_count": 0, "pattern": pattern},
            )

        return StepResult(
            step_name=step["name"], step_type="log_grep",
            status="pass",
            message=f"Found {match_count} matching line(s)",
            output=matched_output,
            duration_ms=_ms(t0),
            metadata={"match_count": match_count, "pattern": pattern},
        )

    except FileNotFoundError:
        return StepResult(
            step_name=step["name"], step_type="log_grep",
            status="fail",
            message=f"Log target not found: {target}",
            duration_ms=_ms(t0),
        )
    except Exception as e:
        return StepResult(
            step_name=step["name"], step_type="log_grep",
            status="fail",
            message=f"Log grep error: {e}",
            duration_ms=_ms(t0),
        )


# ── STEP: prometheus_query ────────────────────────────────────────────────────
# Runs a PromQL instant query and validates the result against a threshold.
# Used for: checking error rate before restart, confirming SLO breach,
#           verifying recovery after remediation.
#
# YAML shape:
#   type: prometheus_query
#   url: http://localhost:9090
#   query: 'slo_error_rate{service="claims-api"}'
#   condition: gt                     # gt | lt | eq | gte | lte
#   threshold: 0.01
#   capture_as: claims_error_rate
def run_prometheus_query(step: dict, context: dict) -> StepResult:
    t0 = time.time()
    prom_url = step.get("url", "http://localhost:9090")
    query = _resolve(step["query"], context)
    condition = step.get("condition", "gt")
    threshold = float(step.get("threshold", 0))
    capture_as = step.get("capture_as")

    try:
        import urllib.parse
        encoded = urllib.parse.quote(query)
        url = f"{prom_url}/api/v1/query?query={encoded}"

        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        if data["status"] != "success":
            return StepResult(
                step_name=step["name"], step_type="prometheus_query",
                status="fail",
                message=f"Prometheus query failed: {data.get('error', 'unknown')}",
                duration_ms=_ms(t0),
            )

        results = data["data"]["result"]
        if not results:
            return StepResult(
                step_name=step["name"], step_type="prometheus_query",
                status="warn",
                message=f"Query returned no data: {query}",
                duration_ms=_ms(t0),
                metadata={"query": query},
            )

        # Take first result value
        value = float(results[0]["value"][1])

        if capture_as:
            context[capture_as] = value

        # Evaluate condition
        condition_met = _evaluate_condition(value, condition, threshold)
        status = "fail" if condition_met else "pass"
        op_symbol = {"gt": ">", "lt": "<", "eq": "==", "gte": ">=", "lte": "<="}

        return StepResult(
            step_name=step["name"], step_type="prometheus_query",
            status=status,
            message=f"Value {value:.4f} {op_symbol.get(condition,'?')} {threshold} → {'BREACH' if condition_met else 'OK'}",
            duration_ms=_ms(t0),
            metadata={"query": query, "value": value, "threshold": threshold},
        )

    except Exception as e:
        return StepResult(
            step_name=step["name"], step_type="prometheus_query",
            status="fail",
            message=f"Prometheus query error: {e}",
            duration_ms=_ms(t0),
        )


# ── STEP: notify ──────────────────────────────────────────────────────────────
# Sends a notification. Supports Slack webhook or log-only (for local testing).
# Used for: alerting on-call, posting runbook completion summary.
#
# YAML shape:
#   type: notify
#   channel: slack                    # "slack" | "log"
#   webhook_url: https://hooks.slack.com/...
#   message: "P1 runbook complete. claims-api error rate: {{claims_error_rate}}"
def run_notify(step: dict, context: dict) -> StepResult:
    t0 = time.time()
    channel = step.get("channel", "log")
    message = _resolve(step.get("message", "Runbook notification"), context)

    if channel == "log":
        print(f"\n  📢  NOTIFY: {message}\n")
        return StepResult(
            step_name=step["name"], step_type="notify",
            status="pass",
            message=f"Logged notification",
            output=message,
            duration_ms=_ms(t0),
        )

    elif channel == "slack":
        webhook_url = step.get("webhook_url", "")
        if not webhook_url:
            return StepResult(
                step_name=step["name"], step_type="notify",
                status="fail",
                message="Slack webhook_url not configured",
                duration_ms=_ms(t0),
            )
        try:
            payload = json.dumps({"text": message}).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
            return StepResult(
                step_name=step["name"], step_type="notify",
                status="pass",
                message="Slack notification sent",
                output=message,
                duration_ms=_ms(t0),
            )
        except Exception as e:
            return StepResult(
                step_name=step["name"], step_type="notify",
                status="fail",
                message=f"Slack notification failed: {e}",
                duration_ms=_ms(t0),
            )

    return StepResult(
        step_name=step["name"], step_type="notify",
        status="fail",
        message=f"Unknown channel: {channel}",
        duration_ms=_ms(t0),
    )


# ── STEP REGISTRY ─────────────────────────────────────────────────────────────
# Maps YAML step type strings to handler functions.
# Adding a new step type = add a function above + one line here.
STEP_HANDLERS = {
    "http_check":       run_http_check,
    "shell":            run_shell,
    "log_grep":         run_log_grep,
    "prometheus_query": run_prometheus_query,
    "notify":           run_notify,
}


# ── HELPERS ───────────────────────────────────────────────────────────────────
def _ms(t0: float) -> int:
    return int((time.time() - t0) * 1000)

def _evaluate_condition(value: float, condition: str, threshold: float) -> bool:
    return {
        "gt":  value > threshold,
        "lt":  value < threshold,
        "eq":  value == threshold,
        "gte": value >= threshold,
        "lte": value <= threshold,
    }.get(condition, False)

def _resolve(value: str, context: dict) -> str:
    """Replace {{variable}} placeholders with values from context."""
    if not isinstance(value, str):
        return value
    for key, val in context.items():
        value = value.replace(f"{{{{{key}}}}}", str(val))
    return value