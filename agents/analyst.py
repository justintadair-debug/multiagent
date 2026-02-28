"""Analyst Director — handles data analysis, reporting, and SEC scan tasks."""

import json
import subprocess
import sys
from pathlib import Path
from agents.base import BaseDirector
from workers.claude_worker import run as claude_run
from workers.shell_worker import run as shell_run
from audit import log as audit_log

SEC_SCANNER_VENV = Path.home() / "projects/sec-scanner/.venv/bin/sec-scanner"
SEC_SCANNER_DIR  = Path.home() / "projects/sec-scanner"


class AnalystDirector(BaseDirector):
    name = "analyst"

    def run_task(self, task: dict) -> str:
        payload = json.loads(task["payload"]) if task["payload"] else {}
        prompt    = payload.get("prompt", "")
        task_type = payload.get("task_type", "general")
        shell_cmd = payload.get("shell_cmd")

        # ── SEC scan task ──────────────────────────────────────────────
        if task_type == "sec_scan" or any(
            kw in prompt.lower()
            for kw in ["sec scan", "sec scanner", "ai washing", "watchlist scan", "scan ticker"]
        ):
            return self._run_sec_scan(payload)

        # ── Generic shell + analyze ────────────────────────────────────
        if shell_cmd:
            try:
                shell_output = shell_run(shell_cmd)
                full_prompt = f"Analyze this data and summarize:\n\n{shell_output}\n\nTask: {prompt}"
            except Exception as e:
                full_prompt = f"Shell command failed: {e}\n\nTask: {prompt}"
        else:
            full_prompt = f"Analysis task: {prompt}\n\nProvide a clear, structured analysis."

        return claude_run(full_prompt)

    def _run_sec_scan(self, payload: dict) -> str:
        """Run the SEC scanner and return a summary of results."""
        prompt = payload.get("prompt", "")
        ticker = payload.get("ticker")

        # Extract ticker from prompt if not explicitly set
        # Handles: "scan ticker NVDA", "sec scan AAPL", "ai washing MSFT"
        if not ticker:
            import re
            SKIP = {"SEC", "SCAN", "AI", "THE", "FOR", "AND", "RUN", "TICKER",
                    "WATCHLIST", "DO", "A", "AN", "ME", "US", "IS", "IN", "ON"}
            # Look for explicit "ticker SYMBOL" pattern first
            m = re.search(r'ticker\s+([A-Z]{1,5})', prompt, re.IGNORECASE)
            if m:
                ticker = m.group(1).upper()
            else:
                # Fall back: find any isolated all-caps word not in skip list
                for w in re.findall(r'\b([A-Z]{1,5})\b', prompt):
                    if w not in SKIP:
                        ticker = w
                        break

        watchlist = payload.get("watchlist", False) or "watchlist" in prompt.lower()

        cmd = [str(SEC_SCANNER_VENV)]
        if ticker and not watchlist:
            cmd += [ticker.upper()]   # positional arg
        else:
            cmd += ["--watchlist"]

        audit_log(self.name, "sec_scan_start", " ".join(cmd))
        print(f"  [analyst] Running SEC scan: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(SEC_SCANNER_DIR)
            )
            output = result.stdout.strip()
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip()[:300])

            # Extract score lines for summary
            lines = [l.strip() for l in output.splitlines() if "Score:" in l]
            summary = "\n".join(lines) if lines else output[-500:]
            audit_log(self.name, "sec_scan_done", summary[:200])
            return summary or "Scan complete — no score lines found in output."

        except subprocess.TimeoutExpired:
            raise RuntimeError("SEC scan timed out after 600s")
