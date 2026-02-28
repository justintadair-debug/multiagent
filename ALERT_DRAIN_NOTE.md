# Alert Drain — How Alerts Reach Discord

## Flow

1. `fire_alert(task_id, reason, attempts)` in `alerts.py` appends a JSON line to:
   ```
   ~/.openclaw/worklog-notify.jsonl
   ```
   with shape:
   ```json
   {"type": "agent_alert", "task_id": 1, "reason": "Failed 3x: timeout", "attempts": 3, "ts": "2026-02-28T00:00:00"}
   ```

2. The **heartbeat agent** (Neo's periodic poll) reads `worklog-notify.jsonl`, filters for `"type": "agent_alert"` entries not yet posted, and sends them to Discord.

## Discord Target

- **Channel:** `#logs` — ID `1476717294397952071`
- **Message format:**
  ```
  🔔 **Agent Alert** — Task #{task_id} | {reason} | {attempts} attempts
  <@1060631026994524250>
  ```
- **Ping user ID:** `1060631026994524250` (Justin)

## Heartbeat Drain Logic (pseudo-code)

```python
import json
from pathlib import Path

NOTIFY_FILE = Path.home() / ".openclaw" / "worklog-notify.jsonl"
CHANNEL_ID = "1476717294397952071"
USER_ID = "1060631026994524250"

for line in NOTIFY_FILE.read_text().splitlines():
    entry = json.loads(line)
    if entry.get("type") == "agent_alert" and not entry.get("posted"):
        msg = (
            f"🔔 **Agent Alert** — Task #{entry['task_id']} | "
            f"{entry['reason']} | {entry['attempts']} attempts\n"
            f"<@{USER_ID}>"
        )
        post_to_discord(CHANNEL_ID, msg)
        entry["posted"] = True
```

## Local Log

Alerts are also written in plain text to:
```
~/projects/multiagent/alerts.log
```
Served via `GET /alerts` (returns last 20 lines as JSON array).
