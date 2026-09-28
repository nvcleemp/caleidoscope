# PNG Decoration

Renders the p31m tiling's "domain 2" fundamental quadrangle (see
`examples/p31m_tiling/`) at a fixed shape (`x=0.5`), with its finished
`rectification` decoration (see `examples/decoration/`) applied — as a
single static picture, using `PngRenderer` instead of TikZ. Same
geometry and decoration as `examples/svg_decoration/`, rendered with
the third renderer instead of the second.

Unlike `examples/decoration/`, there's no step sequence, no video
pipeline, and no CLI flags: this is a minimal demonstration of
`PngRenderer` on a real (non-toy) tiling, not a standalone tool for
exploring the decoration itself.

- `output/png_decoration_tile.png` — the isolated fundamental tile, unfolded.
- `output/png_decoration_tiling.png` — the resulting periodic tiling.

The tiling render uses the same two-pass trick as
`examples/decoration/main.py`'s `render_tiling_steps` and
`examples/svg_decoration/main.py`'s `render_tiling`: render every
tile's polygon fill first, then only the `s2` edges on top, so an edge
isn't hidden under a neighboring tile's fill. Where
`examples/svg_decoration/` does this by appending the second pass's
elements onto the first pass's root `Element`, here it's done with
`PIL.Image.alpha_composite`, layering the second pass's image over the
first — the same underlying idea (finalize() hands back a real object
you can combine further, not a string), expressed in whatever terms
that renderer's own return type supports.

Run with:

```bash
uv run --package png-decoration python examples/png_decoration/main.py
```
