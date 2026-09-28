# Caleidoscope

Creating repeating patterns and tilings.

## Structure

This is a `uv` workspace (`pyproject.toml` at the root, `[tool.uv.workspace] members = ["libs/*", "examples/*"]`), with a single shared `.venv` at the repo root:

- `libs/caleidoscope/` — the actual package (`caleidoscope`), source under `src/caleidoscope/`.
- `examples/basic/` — small, single-feature demo scripts.
- Every other directory under `examples/` (e.g. `two_tilings/`, `p31m_tiling/`, `decoration/`) — a larger, self-contained example, each its own workspace member with its own `pyproject.toml` and `README.md`.

The root project itself (`caleidoscope-group`) has no dependencies; it only exists to define the workspace. Anything that needs to `import caleidoscope` must live in a workspace member that declares `caleidoscope` as a dependency (see the `examples/*/pyproject.toml` files for the pattern: `dependencies = ["caleidoscope"]` plus `[tool.uv.sources] caleidoscope = { workspace = true }`).

## Running things

- Requires Python >= 3.13. Never use the system `python`/`python3` directly — always go through `uv`.
- Run a script that belongs to a workspace member: `uv run --package <member-name> python <path/to/script.py>`, e.g. `uv run --package basic-examples python examples/basic/classify.py`.
- Run the test suite: `uv run --package caleidoscope pytest` (or `cd libs/caleidoscope && uv run pytest`).
- If an IDE can't resolve `import caleidoscope`, the shared `.venv` is probably stale (e.g. after moving the repo) — run `uv sync` from the root.

## Code quality

No linter or type checker (ruff, mypy, etc.) is currently configured in this project. Don't assume one is enforcing style — if you introduce one, add it to a `pyproject.toml` rather than relying on unwritten conventions.
