#!/usr/bin/env python3
"""Manual-only local Hermes compatibility probe, not a queue worker.

No arbitrary input accepted from the platform API. Only the built-in test
question is sent. This process is NOT a security sandbox.
"""
import argparse
import os
import subprocess
from pathlib import Path

PROMPT = "What is seven multiplied by eight? Answer with the number only."
MODEL = "acer-qwen35-64k:latest"

def command():
    return ["hermes", "chat", "--oneshot", "--quiet", "--model", MODEL,
            "--toolsets", "clarify", "--max-turns", "1",
            "--query-file", "-"]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
                        help="Actually invoke Hermes in this terminal; default is dry-run")
    args = parser.parse_args()
    print("Hermes probe (NO platform jobs, NO unattended execution)")
    print("Command:", " ".join(command()))
    if not args.execute:
        print("DRY RUN. Invoke --execute only after reviewing local tool permissions.")
        return
    # Agent is deliberately launched from a separate directory, not the live repo.
    workspace = Path.home() / "agent-workspace" / "hermes-probe"
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
    env = os.environ.copy()
    env.pop("PLATFORM_API_KEY", None)
    env.pop("PLATFORM_DB_PASSWORD", None)
    try:
        result = subprocess.run(command(), input=PROMPT, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                cwd=workspace, env=env, timeout=180, check=False)
    except FileNotFoundError:
        raise SystemExit("Hermes executable not on PATH")
    except subprocess.TimeoutExpired:
        raise SystemExit("Hermes probe timed out after 180 seconds")
    if result.returncode != 0:
        raise SystemExit(f"Hermes probe failed (exit={result.returncode}); inspect Hermes logs locally")
    answer = result.stdout.strip()
    if len(answer) > 8000:
        raise SystemExit("Hermes response exceeds probe size limit")
    print("Hermes answer:", answer)
    print("MATCH:", answer == "56")

if __name__ == "__main__":
    main()
