# Pull Request Information

This file maintains context on the current pull request implementation.

## PR Description

Implement the first chunk: Host Orchestrator & Worktree Setup.

- Click-based CLI entrypoint `python -m code_arena run -c <cfg>`
- Simple TOML config with shared `run_tag`, `attempt_count`, `cli_command`, `prompt`
- Creates N worktrees, one per attempt, on branches `arena/<run_tag>/attempt-<n>` at current `HEAD`
- Ensures clean working tree; better git error messages
- Writes `.arena/runs/<run_tag>/manifest.json` with run metadata and attempts
- Docs updated in `README.md`; example config at `examples/sample-run.toml`
- Minimal pytest baseline and unit tests for config + git-utils

## Upcoming work

Immediate next work (i.e. the single next step), to be updated after every log update:

- Container Runner & Agent Bridge: launch per-worktree containers, feed `cli_command` with `prompt`, capture logs.

## Log

Short bullet lists on everything we've done so far. Use one top bullet per update, and nested ones for details.

- Implement Orchestrator & Worktree Setup (v1)
  - Added Click CLI group and `run` command
  - Added TOML config parsing with validation (`run_tag`, `attempt_count`, `cli_command`, `prompt`)
  - `run_tag` validation to keep branch/path safe
  - Created branches `arena/<run_tag>/attempt-<n>` and associated worktrees under `.arena/runs/<run_tag>/`
  - Wrote run manifest `manifest.json` with metadata and attempt entries
  - Improved git error messages; enforced clean working tree
  - Updated README with usage and config; added example config
  - Added pytest baseline and unit tests (config + git repo check)
