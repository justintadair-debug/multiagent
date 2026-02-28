"""Base Director agent class."""

import time
from database import get_pending_tasks, update_task, write_memory
from worklog import log_to_worklog


class BaseDirector:
    name: str = "base"

    def run_task(self, task: dict) -> str:
        raise NotImplementedError

    def process_pending(self):
        tasks = get_pending_tasks(self.name)
        for task in tasks:
            start = time.time()
            update_task(task["id"], "running")
            try:
                result = self.run_task(task)
                update_task(task["id"], "done", result)
                write_memory(self.name, f"task_{task['id']}_result", result)
                elapsed = (time.time() - start) / 3600
                log_to_worklog(
                    project="MultiAgent",
                    description=f"[{self.name}] {task['task_type']}: {task['payload'][:80]}",
                    actual_hours=round(elapsed, 3),
                    task_type="agent"
                )
                print(f"  ✓ [{self.name}] Task {task['id']} done")
            except Exception as e:
                attempts = task.get("attempts", 0) + 1
                if attempts >= 2:
                    update_task(task["id"], "failed", str(e))
                    print(f"  ✗ [{self.name}] Task {task['id']} FAILED: {e}")
                else:
                    update_task(task["id"], "pending")
                    print(f"  ↻ [{self.name}] Task {task['id']} retry ({attempts}/2)")
