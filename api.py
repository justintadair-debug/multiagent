"""Multiagent status API — read-only FastAPI endpoint for Neo HQ dashboard."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_connection
from datetime import datetime, timezone

app = FastAPI(title="MultiAgent Status API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/status")
def agent_status():
    """Return task counts and recent activity for Neo HQ dashboard."""
    with get_connection() as conn:
        rows = conn.execute("SELECT status, assigned_to, created_at, result FROM tasks ORDER BY id DESC LIMIT 100").fetchall()

    tasks = [dict(r) for r in rows]

    total     = len(tasks)
    done      = sum(1 for t in tasks if t["status"] == "done")
    failed    = sum(1 for t in tasks if t["status"] == "failed")
    pending   = sum(1 for t in tasks if t["status"] == "pending")
    running   = sum(1 for t in tasks if t["status"] == "running")

    # Per-agent counts
    agents = {}
    for name in ["builder", "researcher", "analyst"]:
        agent_tasks = [t for t in tasks if t["assigned_to"] == name]
        agents[name] = {
            "total": len(agent_tasks),
            "done": sum(1 for t in agent_tasks if t["status"] == "done"),
            "failed": sum(1 for t in agent_tasks if t["status"] == "failed"),
        }

    last = tasks[0] if tasks else None

    return {
        "total": total,
        "done": done,
        "failed": failed,
        "pending": pending,
        "running": running,
        "agents": agents,
        "last_task": {
            "assigned_to": last["assigned_to"],
            "status": last["status"],
            "created_at": last["created_at"],
        } if last else None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/recent")
def recent_tasks(limit: int = 10):
    """Return recent tasks for activity feed."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY id DESC LIMIT ?", (min(limit, 50),)
        ).fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8094)
