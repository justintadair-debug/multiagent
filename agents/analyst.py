"""Analyst Director — handles data analysis and reporting tasks."""

import json
from agents.base import BaseDirector
from workers.claude_worker import run as claude_run
from workers.shell_worker import run as shell_run


class AnalystDirector(BaseDirector):
    name = "analyst"

    def run_task(self, task: dict) -> str:
        payload = json.loads(task["payload"]) if task["payload"] else {}
        prompt = payload.get("prompt", "")
        shell_cmd = payload.get("shell_cmd")

        # If a shell command is provided, run it and feed output to Claude
        if shell_cmd:
            try:
                shell_output = shell_run(shell_cmd)
                full_prompt = f"Analyze this data and summarize:\n\n{shell_output}\n\nTask: {prompt}"
            except Exception as e:
                full_prompt = f"Shell command failed: {e}\n\nTask: {prompt}"
        else:
            full_prompt = f"Analysis task: {prompt}\n\nProvide a clear, structured analysis."

        return claude_run(full_prompt)
