# MultiAgent System — Project Context

You are operating within a hierarchical multi-agent AI system. This context gives you persistent knowledge about the architecture, rules, and patterns.

## Architecture
- **Neo (CEO)** — routes tasks to the right Director based on keywords
- **Builder Director** — handles: build, code, create, write, fix, implement, develop
- **Researcher Director** — handles: research, find, search, look up, what is, explain, summarize
- **Analyst Director** — handles: analyze, scan, report, compare, SEC scan, AI washing

## Critical Rules
1. All AI calls use `/Users/justinadair/bin/claude-wrapper -p "prompt"` — NEVER raw `claude` binary
2. Shell commands must use the allowlist: git, python3, pip, sec-scanner, ls, cat, echo, mkdir, cp, mv
3. Every task is logged to WorkLog at http://localhost:8092/api/log (header: X-WL-Key: wl-justin-2026)
4. Every action is written to audit.log
5. Tasks timeout at 180 seconds
6. Max 2 retries before marking failed

## Project Paths
- This system: ~/projects/multiagent/
- SEC Scanner: ~/projects/sec-scanner/
- BizPulse: ~/projects/bizpulse/
- WorkLog: ~/projects/worklog/
- Dinner Table: ~/projects/dinner-table/
- All work restricted to ~/projects/

## SEC Scanner Integration
The Analyst director can run SEC scans:
- Single ticker: `sec-scanner NVDA` (positional arg, NOT --ticker)
- Watchlist: `sec-scanner --watchlist`
- Venv: ~/projects/sec-scanner/.venv/bin/sec-scanner

## WorkLog Integration
Every meaningful task should be logged:
```python
import requests
requests.post("http://localhost:8092/api/log",
    headers={"X-WL-Key": "wl-justin-2026"},
    json={"project": "ProjectName", "description": "What was done",
          "task_type": "agent", "actual_hours": 0.1, "manual_estimate": 1.0})
```

## Shared Memory
- Agents can WRITE observations to shared memory DB
- Agents CANNOT skip work based on another agent's memory note without human approval
- Memory is for context, not decision-making

## Services Running
- BizPulse: port 8091
- WorkLog: port 8092
- Dev server: port 8090
- Dinner Table: port 8093
- SEC report server: port 8080

## Discord Notification
Write to ~/.openclaw/worklog-notify.jsonl to notify #logs:
```json
{"channel": "1476717294397952071", "message": "Your message here", "ts": 1234567890}
```
