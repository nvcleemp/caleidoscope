# p31m tiling

Animates a wallpaper-group-p31m tiling (triangular fundamental domain with
reflections) as its shape parameter `x` sweeps across a range, producing
LaTeX documents — each a sequence of standalone TikZ pictures, one per frame,
suitable for compiling into an animation:

- `output/tile.tex` — the isolated fundamental tile, unfolded.
- `output/tiling.tex` — the resulting periodic tiling.
- `output/quadrangle.tex` — the isolated base quadrangle, with construction
  annotations.
- `output/chambers.tex` — the isolated tile with polygon fills suppressed and
  each chamber labeled with its number.

Run with:

```bash
uv run --package p31m-tiling python examples/p31m_tiling/main.py --mode {tile,tiling,quadrangle,chambers,all}
```

`--mode` defaults to `all`. See `--help` for details.

## Building videos

Once the `.tex` files above have been generated, turn any of them into an
`.mp4` (compiling to PDF, rasterizing each page, then encoding with ffmpeg):

```bash
make videos
```

This builds an `.mp4` next to each `.tex` file found in `output/`. Override
the frame rate or rasterization resolution with `FPS`/`DPI`, e.g. `make
videos FPS=24`. `make clean-videos` removes the generated `.mp4` files. See
[`scripts/tex-to-video.sh`](../../scripts/tex-to-video.sh) for the underlying
script, which can also be run directly on a single file.
