"""Alert system for the multi-agent project.

Fires structured alerts when tasks fail repeatedly or stall.
Alert JSONLines are drained by the heartbeat agent → Discord.
"""

import json
from pathlib import Path
from datetime import datetime

WORKLOG_NOTIFY = Path.home() / ".openclaw" / "worklog-notify.jsonl"
ALERTS_LOG = Path(__file__).parent / "alerts.log"


def fire_alert(task_id: int, reason: str, attempts: int) -> None:
    """Append an agent_alert to the worklog-notify drain and alerts.log."""
    ts = datetime.now().isoformat(timespec="seconds")

    # --- JSONLines entry (consumed by heartbeat → Discord) ---
    entry = {
        "type": "agent_alert",
        "task_id": task_id,
        "reason": reason,
        "attempts": attempts,
        "ts": ts,
    }
    WORKLOG_NOTIFY.parent.mkdir(parents=True, exist_ok=True)
    with WORKLOG_NOTIFY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    # --- Plain-text log (served by GET /alerts) ---
    line = f"[{ts}] ALERT task={task_id} attempts={attempts} reason={reason}"
    ALERTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ALERTS_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
