#!/usr/bin/env python3
"""Validate prerequisites without starting Hermes or reading credential contents."""
import os
import pwd
from pathlib import Path

def check():
    user = pwd.getpwuid(os.getuid())
    assert user.pw_name == "hermes-worker", "Must run as hermes-worker"
    assert user.pw_dir == "/var/lib/hermes-worker", "Unexpected home"
    assert Path.home() == Path(user.pw_dir), "HOME must be isolated"
    workspace = Path(user.pw_dir) / "workspace"
    assert workspace.is_dir() and os.access(workspace, os.W_OK), "Missing writable workspace"
    assert not os.environ.get("PLATFORM_API_KEY"), "Admin API key leaked into runtime"
    assert not os.environ.get("PLATFORM_DB_PASSWORD"), "DB secret leaked into runtime"
    assert not os.environ.get("HERMES_WORKER_KEY"), "Worker key must be file-based"
    print("PASS: dedicated runtime identity and basic environment constraints")
    print("NOTE: Hermes binary, profile and credentials not yet provisioned")

if __name__ == "__main__":
    check()
