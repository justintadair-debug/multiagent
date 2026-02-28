"""Audit logger — writes every agent action to audit.log."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent / "audit.log"

# Set up a dedicated file logger
_logger = logging.getLogger("sayvdo.audit")
_logger.setLevel(logging.INFO)
_handler = logging.FileHandler(LOG_PATH)
_handler.setFormatter(logging.Formatter("%(message)s"))
if not _logger.handlers:
    _logger.addHandler(_handler)


def log(agent: str, action: str, detail: str, result: str = "ok", task_id: int = None):
    """Write a structured audit entry."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "detail": detail[:500],   # truncate long prompts
        "result": result,
    }
    if task_id is not None:
        entry["task_id"] = task_id
    _logger.info(json.dumps(entry))
