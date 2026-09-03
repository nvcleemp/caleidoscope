# two tilings

Animates a transition between two mutually-aligned pgg-symmetric tilings (a
"starting" tile and an "end" tile) by interpolating each through a shared
midpoint tiling, producing a LaTeX document with a sequence of standalone
TikZ pictures (one per frame) suitable for compiling into an animation.

The starting and end tilings are examples from:

> Olaf Delgado-Friedrichs, "Data structures and algorithms for tilings I",
> Theoretical Computer Science, Volume 303, Issues 2–3, 2003, Pages 431-445,
> ISSN 0304-3975, <https://doi.org/10.1016/S0304-3975(02)00500-5>.

Each frame can optionally show the barycentric-subdivision edges and/or
markers for the rotation centers and glide-reflection axes. A third toggle
controls whether the extra transition frames — where the start/end tile is
rotated and rescaled into alignment with the midpoint tiling — are included.
All eight combinations are written to `output/`:

- `output/animation.tex`
- `output/animation_bary.tex`
- `output/animation_symm.tex`
- `output/animation_align.tex`
- `output/animation_bary_symm.tex`
- `output/animation_bary_align.tex`
- `output/animation_symm_align.tex`
- `output/animation_bary_symm_align.tex`

Run with:

```bash
uv run --package two-tilings python examples/two_tilings/main.py
```
