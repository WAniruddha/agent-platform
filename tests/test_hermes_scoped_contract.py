"""Contract checks. Integration authorization still requires Acer testing."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_worker_uses_narrow_credentials():
    text = (ROOT / "scripts/hermes_scoped_worker.py").read_text()
    assert 'X-Worker-Key' in text
    assert 'HERMES_WORKER_KEY_FILE' in text
    assert 'keyfile = os.environ.get' in text
    assert '"/v1/hermes-demo"' in text
    assert 'BASE + "/v1/hermes-demo" + path' in text
    assert 'payload") != {}' in text

def test_scoped_api_fails_closed():
    text = (ROOT / "src/agent_platform/hermes_scoped.py").read_text()
    assert 'len(expected) < 32' in text
    assert 'compare_digest(expected, x_worker_key)' in text
    assert 'capabilities=[CAPABILITY]' in text
    assert 'body.worker_id != WORKER_ID' in text

def test_feature_not_automatically_enabled():
    text = (ROOT / "compose.yaml").read_text()
    assert 'HERMES_WORKER_KEY: ${HERMES_WORKER_KEY:-}' in text
