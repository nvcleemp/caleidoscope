# Caleidoscope

Creating repeating patterns

## Overview

Caleidoscope is a Python library for creating and working with repeating
patterns and tilings. You describe a fundamental tile (its vertices, edges,
and optionally polygons) together with edge identifications, and Caleidoscope
derives the transformations needed to tile a region with copies of it.

## Requirements

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/) for environment and dependency management

## Installation

This repository is a `uv` workspace. From the repository root:

```bash
uv sync
```

This installs the `caleidoscope` library (`libs/caleidoscope/`) into a shared
`.venv/`, editable, so changes to its source take effect immediately.

## Using the library

A pattern is built from a fundamental tile plus a list of edge
identifications; each identification tells Caleidoscope to derive a
transformation that maps one edge onto another, which becomes a generator
for tiling the plane.

```python
from caleidoscope import Pattern, TikzRenderer

# A unit square, with its left/right and bottom/top edges identified so it
# tiles the plane by translation.
vertices = [(0, 0), (1, 0), (1, 1), (0, 1)]
edges = [(0, 1, "bottom"), (1, 2, "right"), (2, 3, "top"), (3, 0, "left")]
identifications = [
    ((0, 3), (1, 2), True),  # left edge -> right edge
    ((0, 1), (3, 2), True),  # bottom edge -> top edge
]
pattern = Pattern(
    vertices, edges, [], center=(0.5, 0.5), tolerance=0.01, identifications=identifications
)

tikz_code = pattern.render(TikzRenderer(), width=6, height=6)
```

`render()` is a convenience method that constructs the pattern and renders it
in one step. If you need to render the same pattern multiple times (e.g.
with different edge filters or styles), call `pattern.construct(...)` once to
get a `ConstructedPattern`, then call `.render(...)` on it as many times as
needed without redoing the tiling computation.

`TikzRenderer` is the only renderer currently provided; other output formats
can be added by implementing the `Renderer` protocol (see
`caleidoscope.renderers.base`).

## Running the examples

Examples live under `examples/`. Each one is its own directory and its own
`uv` workspace member, with its own `pyproject.toml` depending on
`caleidoscope`. Run any example script with:

```bash
uv run --package <package-name> python examples/<directory>/<script>.py
```

`<package-name>` is the `name` field in that example's `pyproject.toml`
(usually matching its directory name, with underscores as hyphens). This
applies to every example, current and future.

For convenience, the root [`Makefile`](Makefile) defines a shorthand target
per example script, e.g. `make run-basic-classify` or `make run-two-tilings`.
New scripts need a target added manually.

`examples/basic/` contains small, single-feature demo scripts — see
[`examples/basic/README.md`](examples/basic/README.md) for what's there.

## Development

Run the test suite with:

```bash
uv run --package caleidoscope pytest
```

`pytest-cov` is a dev dependency of `caleidoscope`, so you can check test
coverage with:

```bash
uv run --package caleidoscope pytest --cov=caleidoscope --cov-report=term-missing
```

`--cov-report=term-missing` lists the specific lines each file is missing
coverage for. Add `--cov-branch` to also track branch coverage, not just
line coverage.

See [`AGENTS.md`](AGENTS.md) for more on the workspace layout and running
things across workspace members.
