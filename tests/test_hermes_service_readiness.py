import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "service_readiness", ROOT / "scripts" / "check_hermes_service_readiness.py"
)
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

def test_unattended_execution_blocked():
    checks = MOD.assess()
    assert checks["dedicated_runtime_configured"] is False
    assert checks["scoped_worker_credentials_configured"] is False
    assert not all(checks.values())

def test_unit_does_not_run_as_operator():
    unit = (ROOT / "deploy/systemd/hermes-worker.service.example").read_text()
    assert "User=hermes-worker" in unit
    assert "ProtectHome=yes" in unit
    assert "NoNewPrivileges=yes" in unit
