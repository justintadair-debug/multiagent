"""WorkLog integration — auto-logs agent sessions."""

import requests
import time

WORKLOG_URL = "http://localhost:8092/api/log"
WORKLOG_KEY = "wl-justin-2026"


def log_to_worklog(project: str, description: str, actual_hours: float, task_type: str = "agent"):
    try:
        requests.post(WORKLOG_URL, json={
            "project": project,
            "description": description,
            "task_type": task_type,
            "actual_hours": actual_hours,
            "manual_estimate": actual_hours * 5,
            "timestamp": int(time.time() * 1000),
        }, headers={"X-WL-Key": WORKLOG_KEY}, timeout=3)
    except Exception:
        pass
