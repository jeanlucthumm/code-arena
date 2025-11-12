"""Minimal structured logging helpers."""

from __future__ import annotations

from datetime import datetime

import click


def _stamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def info(message: str) -> None:
    click.secho(f"[{_stamp()}] INFO  {message}", fg="green")


def warning(message: str) -> None:
    click.secho(f"[{_stamp()}] WARN  {message}", fg="yellow")


def error(message: str) -> None:
    click.secho(f"[{_stamp()}] ERROR {message}", fg="red")
