"""Researcher Director — handles research and information gathering."""

import json
from agents.base import BaseDirector
from workers.claude_worker import run as claude_run


class ResearcherDirector(BaseDirector):
    name = "researcher"

    def run_task(self, task: dict) -> str:
        payload = json.loads(task["payload"]) if task["payload"] else {}
        prompt = payload.get("prompt", "")
        full_prompt = f"Research task: {prompt}\n\nProvide a clear, factual summary with specific details. Be concise."
        return claude_run(full_prompt)
