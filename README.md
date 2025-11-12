# code-arena

Local multi-agent coding arena using Git worktrees and CLI LLMs. Runs N isolated implementations, evaluates them, and selects the best.

## CLI orchestrator (v1)

The first chunk of the system prepares per-attempt Git worktrees so multiple agents can work in parallel.

```bash
python -m code_arena run --config examples/sample-run.toml
```

### Config file

Configs are simple TOML documents:

```toml
run_tag = "demo"
attempt_count = 2
prompt = """
Implement the feature described in ticket ABC-123.
"""
cli_command = ["codex", "run"]
```

- `run_tag` determines the directory (`.arena/runs/<run_tag>`) and branch names (`arena/<tag>/attempt-<n>`).
- Allowed characters for `run_tag`: letters, numbers, `.`, `_`, and `-`.
- `attempt_count` controls how many worktrees will be created.
- `cli_command` is the shared CLI invocation all agents will eventually use.
- `prompt` is stored in the run manifest for downstream stages.

The CLI currently checks for a clean Git tree, creates the worktrees, and writes `.arena/runs/<run_tag>/manifest.json` describing the run.

## Tests

Lightweight pytest baseline is included. Install test deps and run:

```bash
uv pip install -e .[test]
uv run -m pytest -q
```
