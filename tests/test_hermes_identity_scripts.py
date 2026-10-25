from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_script_is_opt_in():
    s = (ROOT / "scripts/provision_hermes_identity.sh").read_text()
    assert '"--apply"' in s
    assert 'useradd --system' in s
    assert '--shell /usr/sbin/nologin' in s
    assert 'systemctl enable' not in s
    assert 'docker compose' not in s

def test_script_refuses_privileged_groups():
    s = (ROOT / "scripts/provision_hermes_identity.sh").read_text()
    assert 'docker|sudo|adm|lxd' in s
    assert '0700 /var/lib/hermes-worker' in s
