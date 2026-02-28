# MultiAgent System — Phase 1

CEO → Director → Worker hierarchical AI agent system.

## Usage

```bash
cd ~/projects/multiagent
source .venv/bin/activate

# Run a task
python main.py "Research what CrewAI is and summarize in 3 bullet points"
python main.py "Build a hello world FastAPI endpoint"
python main.py "Analyze last week's WorkLog data"

# Check task queue
python main.py --status
```

## Architecture

- **Neo (CEO)** — routes tasks to the right Director
- **Builder Director** — coding and build tasks
- **Researcher Director** — research and information gathering  
- **Analyst Director** — data analysis and reporting

All tasks logged to WorkLog automatically.
