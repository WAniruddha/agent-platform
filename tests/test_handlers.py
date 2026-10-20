import pytest
from agent_platform.handlers import dispatch, HANDLERS

def test_add():
    assert dispatch("core.add", {"numbers":[2,3,5]}) == {"total":10}

def test_echo():
    assert dispatch("core.echo", {"text":"hello"}) == {"echo":"hello"}

def test_unknown_handler_rejected():
    with pytest.raises(ValueError):
        dispatch("shell.exec", {"cmd":"whoami"})

def test_invalid_numbers_rejected():
    with pytest.raises(ValueError):
        dispatch("core.add", {"numbers":[True]})
    with pytest.raises(ValueError):
        dispatch("core.add", {"numbers":[]})

def test_handler_names_explicit():
    assert set(HANDLERS) == {"core.echo", "core.add"}
