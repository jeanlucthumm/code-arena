"""Click command surface for the orchestrator."""

from __future__ import annotations

from pathlib import Path

import click

from .config import ConfigError, RunConfig
from .logger import info
from .orchestrator import prepare_run


@click.group()
def cli() -> None:
    """code-arena orchestration utilities."""


@cli.command()
@click.option(
    "--config",
    "config_path",
    "-c",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    required=True,
    help="Path to the TOML configuration file.",
)
@click.option(
    "--runs-dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path(".arena") / "runs",
    show_default=True,
    help="Directory under the repo for storing run artifacts.",
)
@click.option(
    "--attempts",
    type=int,
    default=None,
    help="Override attempt_count from config",
)
def run(config_path: Path, runs_dir: Path, attempts: int | None) -> None:
    """Prepare worktrees and manifest for a run."""

    try:
        config = RunConfig.from_file(config_path, attempt_override=attempts)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc

    try:
        manifest_path = prepare_run(config, runs_dir)
    except Exception as exc:  # noqa: BLE001
        raise click.ClickException(str(exc)) from exc

    info("Run setup complete")
    # Read manifest to display a consistent summary
    import json

    with manifest_path.open("r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    click.echo("\nAttempts:")
    for attempt in manifest.get("attempts", []):
        click.echo(
            f" - {attempt['name']}: {attempt['worktree_path']} (branch {attempt['branch']})"
        )
    click.echo(f"\nManifest: {manifest_path}")
