"""Worktree orchestration for a run."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .config import RunConfig
from . import git_utils
from .logger import info


def prepare_run(config: RunConfig, runs_dir: Path) -> Path:
    repo_root = git_utils.get_repo_root()
    git_utils.ensure_clean_worktree(repo_root)
    base_commit = git_utils.get_head_commit(repo_root)

    runs_root = runs_dir if runs_dir.is_absolute() else repo_root / runs_dir
    run_directory = runs_root / config.run_tag

    if run_directory.exists():
        raise RuntimeError(f"Run directory already exists: {run_directory}")

    run_directory.mkdir(parents=True, exist_ok=False)

    info(f"Preparing run '{config.run_tag}' at {run_directory}")

    attempts: list[dict] = []
    for idx in range(1, config.attempt_count + 1):
        name = f"attempt-{idx}"
        branch = f"arena/{config.run_tag}/{name}"
        worktree_path = run_directory / name
        info(f" - creating worktree {worktree_path} ({branch})")
        git_utils.create_worktree(repo_root, branch, worktree_path, base_commit)
        attempts.append(
            {
                "name": name,
                "branch": branch,
                "worktree_path": str(worktree_path),
            }
        )

    manifest = {
        "run_tag": config.run_tag,
        "attempt_count": config.attempt_count,
        "base_commit": base_commit,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "run_directory": str(run_directory),
        "cli_command": config.cli_command,
        "prompt": config.prompt,
        "attempts": attempts,
    }
    manifest_path = run_directory / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    info(f"Run manifest written to {manifest_path}")
    return manifest_path
