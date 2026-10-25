from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_systemd_runs_scoped_worker_under_restricted_account():
    u=(ROOT/"deploy/systemd/hermes-scoped-worker.service").read_text()
    for expected in ("User=hermes-worker","ProtectHome=true","NoNewPrivileges=true",
                     "ReadWritePaths=/var/lib/hermes-worker",
                     "IPAddressAllow=localhost","ExecStart=/usr/bin/python3 /opt/agent-platform/scripts/hermes_scoped_worker.py --execute"):
        assert expected in u
    assert "ExecStart=/bin/bash" not in u

def test_installer_never_starts_service():
    s=(ROOT/"scripts/install_hermes_boot_worker.sh").read_text()
    assert "systemctl daemon-reload" in s
    assert "systemctl enable" not in s
    assert "systemctl start" not in s
    assert "HERMES_WORKER_KEY" in s

def test_preflight_requires_isolated_hermes():
    s=(ROOT/"scripts/check_hermes_boot_prereqs.sh").read_text()
    assert "/opt/hermes-worker/bin/hermes" in s
    assert "admin .env readable" in s
