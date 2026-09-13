# Decoration

Renders the p31m tiling's "domain 2" fundamental quadrangle (see
`examples/p31m_tiling/`) at a fixed shape (`x=0.5`), both as the isolated
tile and as the resulting periodic tiling, across a sequence of `Step`s
defined in `STEPS` (`main.py`). Every step shares the same vertices and
edge identifications; each contributes its own edges and polygons (a
"decoration"), plus optionally its own raw TikZ (`extra_tikz_tile` /
`extra_tikz_tiling`) appended after the rendered pattern, inside the same
`tikzpicture`, for annotations that don't fit the edges/polygons model
(same mechanism as `examples/glue_and_split/main.py`'s `Step.extra_tikz`).

- `output/decoration_tile.tex` — the isolated fundamental tile, unfolded,
  one `tikzpicture` per step, in order.
- `output/decoration_tiling.tex` — the resulting periodic tiling, one
  `tikzpicture` per step, in order.

Unlike `p31m_tiling`, `x` is fixed rather than animated, and there's no
construction-order output — this is meant as a starting point for adding
custom decoration steps to the tile/tiling, not a standalone demo.

Run with:

```bash
uv run --package decoration python examples/decoration/main.py --mode {tile,tiling,all}
```

`--mode` defaults to `all`. See `--help` for details.

## Building videos

Once the `.tex` files above have been generated, turn either of them into an
`.mp4` (compiling to PDF, rasterizing each page, then encoding with
ffmpeg):

```bash
make videos
```

Each `.tex` file has one frame per step in `STEPS`, so the video shows the
decorations being added in order. Override the frame rate or
rasterization resolution with `FPS`/`DPI`, e.g.
`make videos FPS=24`. `make clean-videos` removes the generated `.mp4`
files. See [`scripts/tex-to-video.sh`](../../scripts/tex-to-video.sh) for
the underlying script, which can also be run directly on a single file.
