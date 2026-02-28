"""Shell worker — runs whitelisted commands safely within ~/projects/."""

import subprocess
import shlex
from pathlib import Path

ALLOWED_BASE = Path.home() / "projects"

# Only these base commands are allowed — no raw string execution
ALLOWED_COMMANDS = {
    "git", "python3", "pip", "pip3",
    "sec-scanner", "pytest", "ls", "cat", "echo", "mkdir", "cp", "mv"
}


def run(command: str, timeout: int = 60) -> str:
    """Run a whitelisted shell command restricted to ~/projects/."""
    try:
        parts = shlex.split(command)
    except ValueError as e:
        raise RuntimeError(f"Invalid command syntax: {e}")

    if not parts:
        raise RuntimeError("Empty command")

    base_cmd = Path(parts[0]).name  # handles full paths like /usr/bin/git → git
    if base_cmd not in ALLOWED_COMMANDS:
        raise RuntimeError(
            f"Command '{base_cmd}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"
        )

    result = subprocess.run(
        parts,
        shell=False,           # explicit list, no shell injection
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(ALLOWED_BASE)
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {result.stderr.strip()}")
    return result.stdout.strip()
