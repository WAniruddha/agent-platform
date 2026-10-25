#!/usr/bin/env python3
"""Fail-closed readiness report for dedicated persistent Hermes deployment."""
import argparse
import json
import os
from pathlib import Path

def assess():
    repo = Path(__file__).resolve().parents[1]
    worker = repo / "scripts" / "hermes_demo_worker.py"
    service = repo / "deploy" / "systemd" / "hermes-worker.service.example"
    checks = {
        "worker_script_present": worker.is_file(),
        "service_template_present": service.is_file(),
        "dedicated_runtime_configured": False,
        "isolated_hermes_profile_configured": False,
        "scoped_worker_credentials_configured": False,
        "filesystem_policy_verified": False,
        "restart_recovery_tested": False,
    }
    return checks

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    checks = assess()
    if args.json:
        print(json.dumps(checks, indent=2))
    else:
        for name, ok in checks.items():
            print(f'{"PASS" if ok else "BLOCKED"}: {name}')
    if not all(checks.values()):
        print("NOT READY: do not enable a persistent Hermes worker.")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
