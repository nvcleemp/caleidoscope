# p31m tiling

Animates a wallpaper-group-p31m tiling (triangular fundamental domain with
reflections) as its shape parameter `x` sweeps across a range, producing two
LaTeX documents — each a sequence of standalone TikZ pictures, one per frame,
suitable for compiling into an animation:

- `output/tile.tex` — the isolated fundamental tile, unfolded.
- `output/tiling.tex` — the resulting periodic tiling.

Run with:

```bash
uv run --package p31m-tiling python examples/p31m_tiling/main.py --mode {tile,tiling,both}
```

`--mode` defaults to `both`. See `--help` for details.
