from __future__ import annotations

from pathlib import Path

import pytest

from code_arena.git_utils import GitError, get_repo_root


def test_get_repo_root_outside_repo(tmp_path: Path) -> None:
    with pytest.raises(GitError) as ei:
        get_repo_root(start=tmp_path)
    assert "Not inside a Git repository" in str(ei.value)
