"""Small helpers for interacting with Git."""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a git command fails."""


def _run_git(args: list[str], *, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        msg = stderr or stdout or "git command failed"
        raise GitError(f"git {' '.join(args)}: {msg}")
    return result.stdout.strip()


def get_repo_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    try:
        return Path(_run_git(["rev-parse", "--show-toplevel"], cwd=start))
    except GitError as exc:
        raise GitError(
            "Not inside a Git repository. Initialize or cd into a repo."
        ) from exc


def get_head_commit(repo_root: Path) -> str:
    return _run_git(["rev-parse", "HEAD"], cwd=repo_root)


def ensure_clean_worktree(repo_root: Path) -> None:
    status = _run_git(["status", "--porcelain"], cwd=repo_root)
    if status:
        raise GitError("Working tree must be clean before starting a run")


def create_worktree(
    repo_root: Path, branch: str, worktree_path: Path, base_ref: str
) -> None:
    args = [
        "worktree",
        "add",
        "-b",
        branch,
        str(worktree_path),
        base_ref,
    ]
    _run_git(args, cwd=repo_root)
