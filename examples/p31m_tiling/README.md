# p31m tiling

Animates a wallpaper-group-p31m tiling (triangular fundamental domain with
reflections) as its shape parameter `x` sweeps across a range, producing
LaTeX documents — each a sequence of standalone TikZ pictures, one per frame,
suitable for compiling into an animation. The same tiling is generated from
two different fundamental-domain gluings (`--domain 1`, the original
construction, and `--domain 2`, an alternate one); domain 2's files get a
`_2` suffix:

- `output/p31m_tile[_2].tex` — the isolated fundamental tile, unfolded.
- `output/p31m_tiling[_2].tex` — the resulting periodic tiling.
- `output/p31m_quadrangle[_2].tex` — the isolated base quadrangle, with
  construction annotations.
- `output/p31m_chambers[_2].tex` — the isolated tile with polygon fills
  suppressed and each chamber labeled with its number.
- `output/p31m_tiling_construction[_2].tex` — a fixed-shape tiling built up
  one tile at a time, in construction order.
- `output/p31m_tiling_construction_beamer[_2].tex` — the same construction
  sequence as a single beamer frame using `\only<>` overlays instead of one
  picture per step.

Run with:

```bash
uv run --package p31m-tiling python examples/p31m_tiling/main.py --mode {tile,tiling,quadrangle,chambers,construction,construction_beamer,all} --domain {1,2,all}
```

`--mode` and `--domain` both default to `all`. See `--help` for details.

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
