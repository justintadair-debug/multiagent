"""Builder Director — handles coding and build tasks."""

import json
from agents.base import BaseDirector
from workers.claude_worker import run as claude_run


class BuilderDirector(BaseDirector):
    name = "builder"

    def run_task(self, task: dict) -> str:
        payload = json.loads(task["payload"]) if task["payload"] else {}
        prompt = payload.get("prompt", "")
        context = payload.get("context", "")
        full_prompt = f"{context}\n\n{prompt}".strip() if context else prompt
        return claude_run(full_prompt)
