# SVG Decoration

Renders the p31m tiling's "domain 2" fundamental quadrangle (see
`examples/p31m_tiling/`) at a fixed shape (`x=0.5`), with its finished
`rectification` decoration (see `examples/decoration/`) applied — as a
single static picture, using `SvgRenderer` instead of TikZ.

Unlike `examples/decoration/`, there's no step sequence, no video
pipeline, and no CLI flags: this is a minimal demonstration of
`SvgRenderer` on a real (non-toy) tiling, not a standalone tool for
exploring the decoration itself.

- `output/svg_decoration_tile.svg` — the isolated fundamental tile, unfolded.
- `output/svg_decoration_tiling.svg` — the resulting periodic tiling.

The tiling render uses the same two-pass trick as
`examples/decoration/main.py`'s `render_tiling_steps`: render every
tile's polygon fill first, then only the `s2` edges on top, so an edge
isn't hidden under a neighboring tile's fill. Where
`examples/decoration/` does this by concatenating two rendered
strings, here it's done by appending the second pass's elements
directly onto the first pass's root `Element` — the extension
mechanism `SvgRenderer.finalize()` is designed for.

Run with:

```bash
uv run --package svg-decoration python examples/svg_decoration/main.py
```
