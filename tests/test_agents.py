"""Contract tests for the metadata-only agent registry."""
import pytest
from pydantic import ValidationError
from agent_platform.api import AgentIn

def test_agent_registration_payload():
    agent = AgentIn(id="hermes-acer", runtime="hermes", capabilities=["research.web"])
    assert agent.id == "hermes-acer"
    assert agent.capabilities == ["research.web"]

@pytest.mark.parametrize("caps", [
    [], ["research.web", "research.web"], ["shell exec"], ["X" * 81],
])
def test_reject_bad_capabilities(caps):
    with pytest.raises(ValidationError):
        AgentIn(id="hermes-acer", runtime="hermes", capabilities=caps)

def test_reject_invalid_id():
    with pytest.raises(ValidationError):
        AgentIn(id="../unsafe", runtime="hermes", capabilities=["research.web"])
