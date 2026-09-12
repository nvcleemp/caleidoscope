# Glue and split

Builds up a wallpaper pattern from a square fundamental domain, one step at a
time. The square's corners (vertices 1,2,3,4 in cyclic order) can be glued in
several ways (`IDENTIFICATIONS_LIST` in `main.py`); each gluing is fixed for
every step. Each step in `STEPS` instead varies the interior edges, polygons,
and styles used to render the fundamental tile, so the pattern can be shown
splitting into more pieces (or being restyled) across a sequence of frames.

Every identification set in `IDENTIFICATIONS_LIST` gets its own pair of
output files; set 2 and up get a `_N` suffix:

- `output/glue_and_split[_N].tex` — each step as its own standalone TikZ
  picture, in order (suitable for `make videos`).
- `output/glue_and_split_beamer[_N].tex` — the same sequence as a single
  beamer frame, with each step shown on its own `\only<n>` overlay.

Run with:

```bash
uv run --package glue-and-split python examples/glue_and_split/main.py --mode {steps,steps_beamer,all} --identifications {1,2,3,all}
```

`--mode` and `--identifications` both default to `all`. See `--help` for details.

## Building videos

Once `output/glue_and_split.tex` has been generated, turn it into an `.mp4`
(compiling to PDF, rasterizing each page, then encoding with ffmpeg):

```bash
make videos
```

Override the frame rate or rasterization resolution with `FPS`/`DPI`, e.g.
`make videos FPS=24`. `make clean-videos` removes the generated `.mp4` files.
See [`scripts/tex-to-video.sh`](../../scripts/tex-to-video.sh) for the
underlying script, which can also be run directly on a single file.
