"""Neo CEO Agent — entry point for the multi-agent system."""

import sys
import json
import time
import signal
import subprocess
from database import enqueue_task, get_task, list_tasks, read_memory, init_db, mark_failed
from agents.builder import BuilderDirector
from agents.researcher import ResearcherDirector
from agents.analyst import AnalystDirector
from audit import log as audit_log

DIRECTORS = {
    "builder": BuilderDirector(),
    "researcher": ResearcherDirector(),
    "analyst": AnalystDirector(),
}

# Routing keywords
ROUTING = {
    "builder":    ["build", "code", "create", "write", "fix", "implement", "develop"],
    "researcher": ["research", "find", "search", "look up", "what is", "who is", "explain", "summarize"],
    "analyst":    ["analyze", "analyse", "scan", "report", "compare", "review data", "stats", "metrics",
                   "sec scan", "sec scanner", "ai washing", "watchlist scan", "scan ticker"],
}

# Tasks containing these keywords require human approval before shell execution
SHELL_APPROVAL_KEYWORDS = ["shell", "run command", "execute", "bash", "terminal"]

# Max seconds a task is allowed to run before being killed
TASK_TIMEOUT_SECONDS = 180


def route_task(task_str: str) -> str:
    """Decide which Director should handle this task."""
    lower = task_str.lower()
    scores = {director: 0 for director in ROUTING}
    for director, keywords in ROUTING.items():
        for kw in keywords:
            if kw in lower:
                scores[director] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "researcher"


def needs_approval(task_str: str) -> bool:
    """Return True if this task touches shell execution and needs human sign-off."""
    lower = task_str.lower()
    return any(kw in lower for kw in SHELL_APPROVAL_KEYWORDS)


def request_approval(task_str: str) -> bool:
    """Ask for Discord approval. For CLI use, prompt stdin."""
    print(f"\n⚠️  APPROVAL REQUIRED — this task involves shell execution:")
    print(f"   {task_str[:120]}")
    answer = input("Approve? [y/N]: ").strip().lower()
    approved = answer == "y"
    audit_log("neo", "approval_request", task_str, result="approved" if approved else "denied")
    return approved


def run_task(task_str: str):
    """CEO receives a task, routes it, executes, returns result."""
    init_db()

    # Approval gate for shell tasks
    if needs_approval(task_str):
        if not request_approval(task_str):
            print("❌ Task denied by user.")
            audit_log("neo", "task_denied", task_str, result="denied")
            return None

    director_name = route_task(task_str)
    print(f"\n🧠 Neo → routing to [{director_name}]: {task_str[:80]}")
    audit_log("neo", "route", task_str, result=director_name)

    task_id = enqueue_task(
        assigned_to=director_name,
        task_type="user_request",
        payload={"prompt": task_str}
    )

    director = DIRECTORS[director_name]

    # Run with timeout
    start = time.time()
    director.process_pending()

    for _ in range(TASK_TIMEOUT_SECONDS):
        task = get_task(task_id)
        if task and task["status"] in ("done", "failed"):
            break
        if time.time() - start > TASK_TIMEOUT_SECONDS:
            mark_failed(task_id, "Timed out")
            audit_log(director_name, "timeout", task_str, result="timeout", task_id=task_id)
            print(f"\n⏱️  Task timed out after {TASK_TIMEOUT_SECONDS}s")
            return None
        time.sleep(1)

    if task["status"] == "done":
        audit_log(director_name, "task_done", task_str, result="ok", task_id=task_id)
        print(f"\n✅ Result:\n{task['result']}")
        return task["result"]
    else:
        audit_log(director_name, "task_failed", task_str, result=task["result"] or "unknown", task_id=task_id)
        print(f"\n❌ Task failed: {task['result']}")
        return None


def kill_all():
    """Kill all running agent subprocesses and clear pending tasks."""
    print("🛑 Killing all pending tasks...")
    tasks = list_tasks(50)
    killed = 0
    for t in tasks:
        if t["status"] == "pending":
            mark_failed(t["id"], "Killed by --kill-all")
            killed += 1
    audit_log("neo", "kill_all", f"Killed {killed} pending tasks", result="ok")
    print(f"   Marked {killed} pending tasks as failed.")
    print("   Done. Re-run main.py to start fresh.")


def show_status():
    """Show recent task queue status."""
    tasks = list_tasks(10)
    if not tasks:
        print("No tasks yet.")
        return
    print(f"\n{'ID':<5} {'Director':<12} {'Status':<10} {'Type':<15} {'Created'}")
    print("-" * 65)
    for t in tasks:
        print(f"{t['id']:<5} {t['assigned_to']:<12} {t['status']:<10} {t['task_type']:<15} {t['created_at'][:16]}")


def show_audit(lines: int = 20):
    """Tail the audit log."""
    from pathlib import Path
    log_path = Path(__file__).parent / "audit.log"
    if not log_path.exists():
        print("No audit log yet.")
        return
    entries = log_path.read_text().strip().splitlines()
    for line in entries[-lines:]:
        try:
            e = json.loads(line)
            print(f"{e['ts'][:19]}  {e['agent']:<12} {e['action']:<18} {e['result']:<10} {e['detail'][:60]}")
        except Exception:
            print(line)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 main.py 'Your task here'")
        print("       python3 main.py --status")
        print("       python3 main.py --audit")
        print("       python3 main.py --kill-all")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "--status":
        show_status()
    elif cmd == "--audit":
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        show_audit(lines)
    elif cmd == "--kill-all":
        kill_all()
    else:
        task_str = " ".join(sys.argv[1:])
        run_task(task_str)
