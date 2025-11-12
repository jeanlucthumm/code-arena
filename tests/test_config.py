from __future__ import annotations

from pathlib import Path

import pytest

from code_arena.config import ConfigError, RunConfig


def write_toml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_runconfig_loads_valid(tmp_path: Path) -> None:
    cfg = write_toml(
        tmp_path,
        """
run_tag = "demo-1"
attempt_count = 2
prompt = "Do it"
cli_command = ["codex", "run"]
""",
    )

    rc = RunConfig.from_file(cfg)
    assert rc.run_tag == "demo-1"
    assert rc.attempt_count == 2
    assert rc.cli_command == ["codex", "run"]
    assert rc.prompt == "Do it"


def test_attempt_override(tmp_path: Path) -> None:
    cfg = write_toml(
        tmp_path,
        """
run_tag = "tag"
attempt_count = 2
prompt = "p"
cli_command = ["a"]
""",
    )

    rc = RunConfig.from_file(cfg, attempt_override=5)
    assert rc.attempt_count == 5


@pytest.mark.parametrize("bad", ["bad/tag", "has space", "*weird*"])
def test_invalid_run_tag(tmp_path: Path, bad: str) -> None:
    cfg = write_toml(
        tmp_path,
        f"""
run_tag = "{bad}"
attempt_count = 1
prompt = "p"
cli_command = ["x"]
""",
    )
    with pytest.raises(ConfigError):
        RunConfig.from_file(cfg)


def test_missing_attempt_count(tmp_path: Path) -> None:
    cfg = write_toml(
        tmp_path,
        """
run_tag = "ok"
prompt = "p"
cli_command = ["x"]
""",
    )
    with pytest.raises(ConfigError):
        RunConfig.from_file(cfg)


def test_cli_command_validation(tmp_path: Path) -> None:
    cfg = write_toml(
        tmp_path,
        """
run_tag = "ok"
attempt_count = 1
prompt = "p"
cli_command = ["x", ""]
""",
    )
    with pytest.raises(ConfigError):
        RunConfig.from_file(cfg)
