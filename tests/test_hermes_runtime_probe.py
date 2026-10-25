from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_readonly_probe_has_no_mutating_commands():
    s = (ROOT / "scripts/check_hermes_runtime_isolation.sh").read_text()
    for forbidden in ("useradd", "usermod", "systemctl enable", "chmod 777", "docker compose"):
        assert forbidden not in s
    assert 'test -r "$HOME/.hermes/config.yaml"' in s
    assert 'test -r "$HOME/agent-platform/.env"' in s

def test_runtime_checker_rejects_admin_secrets():
    s = (ROOT / "scripts/hermes_worker_runtime_env_check.py").read_text()
    assert 'PLATFORM_API_KEY' in s
    assert 'PLATFORM_DB_PASSWORD' in s
    assert 'HERMES_WORKER_KEY' in s
