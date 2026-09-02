# Basic examples

Small, single-feature scripts, as opposed to the larger examples elsewhere in `examples/`.

Run with:

```
uv run --package basic-examples python examples/basic/<script>.py
```

- `classify.py` — machine-readable classification of `Transform2D` instances via `classify()`.
- `from_two_segments.py` — building a `Transform2D` that maps one segment onto another, with and without orientation preserved.
- `transformation_tracking.py` — inspecting a tile's `transformation` and `generator_sequence`.
- `filtered_rendering.py` — constructing a pattern once and rendering it multiple times with different edge filters; writes TikZ output to `output/`.
