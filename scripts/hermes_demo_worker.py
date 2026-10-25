#!/usr/bin/env python3
"""Opt-in, fixed-task Hermes queue worker for local integration testing.

Not a sandbox. No arbitrary model prompts, shell commands or user files
accepted from jobs. Do not run this on an internet-exposed API.
"""
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

CAPABILITY = "hermes.demo.multiply"
TASK_TYPE = CAPABILITY
WORKER_ID = "acer-hermes-demo-1"
QUESTION = "What is seven multiplied by eight? Answer with the number only."
MODEL = "acer-qwen35-64k:latest"
BASE = "http://127.0.0.1:8765"
STOP = threading.Event()


def request(method, path, key, body=None):
    raw = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path, data=raw, method=method,
        headers={"X-Platform-Key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def run_hermes():
    workspace = Path.home() / "agent-workspace" / "hermes-queue-demo"
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Do not pass the platform key to the model process.
    env = {k: v for k, v in os.environ.items()
           if k not in {"PLATFORM_API_KEY", "PLATFORM_DB_PASSWORD"}}
    cmd = ["hermes", "chat", "--oneshot", "--quiet", "--model", MODEL,
           "--toolsets", "clarify", "--ignore-rules", "--max-turns", "1",
           "--run-budget", "90", "--query-file", "-", "--source", "tool"]
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, cwd=workspace, env=env,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(QUESTION, timeout=120)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise RuntimeError("Hermes timed out")
    if proc.returncode:
        raise RuntimeError(f"Hermes exited with code {proc.returncode}")
    if len(stdout.encode()) > 8192:
        raise RuntimeError("Hermes output too large")
    response = stdout.strip()
    if not response:
        raise RuntimeError("Hermes returned empty response")
    return {"answer": response, "expected": "56", "exact_match": response == "56"}


def process_job(job, key):
    job_id = job["id"]
    error = None
    result = None
    if job.get("task_type") != TASK_TYPE or job.get("payload") != {}:
        error = "Invalid demo task or payload"
    else:
        heartbeat_stop = threading.Event()
        heartbeat_failure = threading.Event()

        def heartbeat():
            while not heartbeat_stop.wait(20):
                try:
                    request("POST", f"/v1/jobs/{job_id}/heartbeat", key,
                            {"worker_id": WORKER_ID, "lease_seconds": 300})
                except Exception:
                    heartbeat_failure.set()
                    break

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        try:
            result = run_hermes()
            if heartbeat_failure.is_set():
                raise RuntimeError("Lease heartbeat failed")
        except Exception as exc:
            error = str(exc)[:200]
        finally:
            heartbeat_stop.set()
            thread.join(timeout=3)
    outcome = {"worker_id": WORKER_ID, "success": error is None,
               "result": result if error is None else None, "error": error}
    request("POST", f"/v1/jobs/{job_id}/complete", key, outcome)
    print(f"Job {job_id}: " + ("completed" if error is None else "failed"), flush=True)


def main():
    if "--execute" not in sys.argv[1:]:
        print("Manual local demo worker. Use --execute after reviewing source.")
        return
    # Read only the API key from the existing local .env, without sourcing it.
    envpath = Path.home() / "agent-platform" / ".env"
    if not envpath.is_file():
        raise SystemExit("Missing local agent-platform .env")
    key = next((line.split("=", 1)[1].strip() for line in
                envpath.read_text().splitlines()
                if line.startswith("PLATFORM_API_KEY=")), "")
    if not key:
        raise SystemExit("PLATFORM_API_KEY missing")
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())
    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    print("Hermes demo worker ready. Ctrl+C to stop. No arbitrary prompts.", flush=True)
    while not STOP.is_set():
        try:
            data = request("POST", "/v1/workers/claim", key,
                           {"worker_id": WORKER_ID,
                            "capabilities": [CAPABILITY], "lease_seconds": 300})
            job = data.get("job")
            if job is not None:
                process_job(job, key)
            else:
                STOP.wait(3)
        except (urllib.error.URLError, ValueError, RuntimeError) as exc:
            print(f"Worker error: {type(exc).__name__}", flush=True)
            STOP.wait(5)


if __name__ == "__main__":
    main()
