"""Static safety-contract tests for the opt-in demonstration worker.

No network access, database or installed Hermes required.
"""
import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "hermes_demo_worker.py"


def test_script_parses():
    ast.parse(SOURCE.read_text())


def test_demo_task_is_fixed():
    source = SOURCE.read_text()
    assert 'CAPABILITY = "hermes.demo.multiply"' in source
    assert 'QUESTION = "What is seven multiplied by eight?' in source
    assert 'job.get("payload") != {}' in source


def test_not_automatically_started():
    source = SOURCE.read_text()
    assert '"--execute" not in sys.argv[1:]' in source
    assert '"--yolo"' not in source


def test_bounded_runtime_and_no_shell():
    source = SOURCE.read_text()
    assert "timeout=120" in source
    assert '"--run-budget", "90"' in source
    assert "shell=True" not in source
