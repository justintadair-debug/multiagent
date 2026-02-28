"""Claude worker — runs claude -p subprocess for AI tasks."""

import subprocess
import time


def run(prompt: str, timeout: int = 120) -> str:
    """Run a prompt through Claude CLI and return the result."""
    try:
        result = subprocess.run(
            ["/Users/justinadair/bin/claude-wrapper", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise RuntimeError(f"Claude error: {result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Claude timed out after {timeout}s")
