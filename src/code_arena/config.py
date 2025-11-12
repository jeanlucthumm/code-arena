"""Run configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import re

import tomllib


class ConfigError(Exception):
    """Raised when the run configuration is invalid."""


@dataclass(slots=True)
class RunConfig:
    """Normalized configuration for an orchestrator run."""

    run_tag: str
    attempt_count: int
    cli_command: list[str]
    prompt: str

    @classmethod
    def from_file(
        cls, path: Path, *, attempt_override: int | None = None
    ) -> "RunConfig":
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")

        with path.open("rb") as handle:
            raw = tomllib.load(handle)

        run_tag = _expect_str(raw, "run_tag")
        _validate_run_tag(run_tag)
        prompt = _expect_str(raw, "prompt")
        cli_command = _expect_str_list(raw, "cli_command")

        attempt_count = (
            attempt_override
            if attempt_override is not None
            else raw.get("attempt_count")
        )
        if attempt_count is None:
            raise ConfigError("Missing required field: attempt_count")
        if not isinstance(attempt_count, int) or attempt_count <= 0:
            raise ConfigError("attempt_count must be a positive integer")

        if attempt_override is not None and attempt_override <= 0:
            raise ConfigError("attempt override must be a positive integer")

        return cls(
            run_tag=run_tag,
            attempt_count=attempt_count,
            cli_command=cli_command,
            prompt=prompt,
        )


def _expect_str(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{key} must be a non-empty string")
    return value


def _expect_str_list(data: dict, key: str) -> list[str]:
    value = data.get(key)
    if not isinstance(value, Sequence) or not value:
        raise ConfigError(f"{key} must be a non-empty array of strings")

    formatted: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise ConfigError(f"{key}[{idx}] must be a non-empty string")
        formatted.append(item)
    return formatted


_RUN_TAG_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def _validate_run_tag(tag: str) -> None:
    """Ensure run_tag is branch/path safe.

    We allow alphanumerics, dot, underscore, and dash. This keeps branch names like
    `arena/<tag>/attempt-1` safe and portable, and it keeps filesystem paths simple.
    """
    if not _RUN_TAG_RE.match(tag):
        raise ConfigError("run_tag may only contain letters, numbers, '.', '_' and '-'")
