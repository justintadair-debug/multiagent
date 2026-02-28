# TASK.md — Multi-Agent Phase 1 Build

Build the Phase 1 foundation for a hierarchical multi-agent AI system at `~/projects/multiagent/`.

Read `MULTIAGENT.md` in this directory first for full context and spec.

## What to Build

### 1. Project Structure
```
~/projects/multiagent/
├── main.py           # Neo CEO agent — entry point
├── database.py       # Task queue + shared memory (SQLite)
├── agents/
│   ├── __init__.py
│   ├── base.py       # Base agent class
│   ├── builder.py    # Builder Director
│   ├── researcher.py # Researcher Director
│   └── analyst.py    # Analyst Director
├── workers/
│   ├── __init__.py
│   ├── claude_worker.py  # Runs claude -p subprocess for AI tasks
│   └── shell_worker.py   # Runs shell commands
├── discord_notify.py # Posts results to Discord #logs
├── worklog.py        # Auto-logs sessions to WorkLog API
├── pyproject.toml
└── README.md
```

### 2. SQLite Database (`database.py`)
Two tables:

**tasks** — the task queue
```sql
CREATE TABLE tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at   TEXT DEFAULT (datetime('now')),
    assigned_to  TEXT NOT NULL,  -- 'builder' | 'researcher' | 'analyst'
    task_type    TEXT NOT NULL,
    payload      TEXT,           -- JSON
    status       TEXT DEFAULT 'pending',  -- pending | running | done | failed
    result       TEXT,           -- JSON output
    attempts     INTEGER DEFAULT 0,
    updated_at   TEXT
);
```

**memory** — shared agent context
```sql
CREATE TABLE memory (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    agent      TEXT NOT NULL,
    key        TEXT NOT NULL,
    value      TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

### 3. Neo CEO Agent (`main.py`)
- Accepts a task string as input
- Parses the task and decides which Director to assign it to (builder/researcher/analyst)
- Inserts task into the queue
- Monitors for completion
- Reports result back

Simple routing logic:
- Contains "build", "code", "create", "fix" → Builder
- Contains "research", "find", "search", "look up" → Researcher  
- Contains "scan", "analyze", "report", "summarize" → Analyst

### 4. Builder Director (`agents/builder.py`)
- Picks up tasks assigned to 'builder' from the queue
- Uses `claude_worker.py` to run `claude -p` subprocess with the task
- Writes result back to task queue
- Logs to shared memory

### 5. Researcher Director (`agents/researcher.py`)
- Picks up tasks assigned to 'researcher'
- Uses web search (brave search API via subprocess or requests) OR claude -p with web context
- Writes results back to task queue
- Logs to shared memory

### 6. Analyst Director (`agents/analyst.py`)
- Picks up tasks assigned to 'analyst'
- Runs analysis tasks (can call sec-scanner, read WorkLog data, etc.)
- Writes results back to task queue
- Logs to shared memory

### 7. Workers

**claude_worker.py**
```python
# Runs: claude -p "prompt" 
# Returns stdout as result
# Timeout: 120s
```

**shell_worker.py**
```python
# Runs arbitrary shell commands safely
# Restricted to ~/projects/ only
# Returns stdout/stderr
```

### 8. Failure Handling
- Worker fails → retry (max 2 attempts)
- 2 failures → mark task as 'failed', log error to memory
- Failed tasks → print clear error with context

### 9. WorkLog Integration (`worklog.py`)
After every completed task, POST to WorkLog:
```
POST http://localhost:8092/api/log
X-WL-Key: wl-justin-2026
{project: "MultiAgent", description: task summary, task_type: "agent", actual_hours: elapsed}
```

### 10. pyproject.toml
```toml
[project]
name = "multiagent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "crewai",
    "requests",
]
```

### 11. README.md
Brief usage doc:
```
# MultiAgent System — Phase 1

## Run a task
python main.py "Research 5 Austin restaurants I could pitch BizPulse to"
python main.py "Build a hello world FastAPI endpoint"
python main.py "Analyze last week's WorkLog data and summarize"

## Check task queue
python main.py --status

## View shared memory
python main.py --memory
```

## Important Notes
- Use `claude -p "prompt"` for all AI calls — NOT the anthropic Python SDK (Justin uses Claude Max, not API key)
- Keep it simple — this is Phase 1 proof of concept, not production
- All file operations restricted to `~/projects/`
- Test with a simple end-to-end task before finishing

## Test It
After building, run this test to verify the loop works:
```
python main.py "Research what CrewAI is and summarize in 3 bullet points"
```
Should: route to Researcher → run claude -p → return result → log to WorkLog

## When Done
Run: `openclaw system event --text "Done: MultiAgent Phase 1 built and tested" --mode now`
