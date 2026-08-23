import subprocess
import sys


def run_compose():
    """CLI helper to dispatch poe compose commands."""
    subcommand = sys.argv[1].lower() if len(sys.argv) > 1 else "up"

    if subcommand in ("inspector", "ui", "dev"):
        cmd = [
            "docker",
            "compose",
            "-f",
            "docker-compose.yml",
            "-f",
            "docker-compose.inspector.yml",
            "up",
        ]
    else:
        cmd = ["docker", "compose", "up", "-d"]

    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
