# Inverse generators — design

Fixes GitHub issue #3: `Pattern.construct` composes only the generators
derived from the identifications, never their inverses, so a pattern with a
translation generator fills only part of the region (the README's square
example tiles one quadrant: 9 tiles instead of 36 in a 6×6 region).

## Constraint

The current construction order must remain reproducible. The p31m example's
`construction` and `construction_beamer` modes number tiles in construction
order, and that numbering is referred to in texts outside this repository.

## Library changes (`libs/caleidoscope/`)

### `Transform2D`

- `inverse() -> Transform2D`: the inverse of the affine transformation
  (inverse of the 2×2 linear part, translation `-L⁻¹ t`). Raises
  `ValueError` for a singular matrix.
- `is_close(other: Transform2D, tolerance: float = 1e-9) -> bool`: true when
  all six affine entries differ by at most `tolerance`.

### `Pattern`

- New keyword-only constructor argument `include_inverses: bool = True`,
  stored on the instance.
- `generators` builds the generators from the identifications exactly as
  today (same order, indices `0..n-1`). If `include_inverses` is true, it
  then appends, in the same order, the inverse of each of those generators,
  skipping an inverse that `is_close` to a generator already in the list.
  So mirrors and half-turns (self-inverse) and identifications whose reverse
  the caller already listed add nothing.
- With `include_inverses=False` the generators, the construction order and
  the generator sequences are exactly as before this change.
- `Tile.format_generator_sequence` is unchanged (`g{i}`); appended inverses
  show up as `g{n}`, `g{n+1}`, ….

### README

The square example now works as written. Add a short paragraph after it
documenting `include_inverses`: on by default; pass `False` to get the
original construction order (only generators as given), e.g. when tile
numbering in construction order is referenced elsewhere.

## Example changes

- `examples/p31m_tiling/main.py`: pass `include_inverses=False` to the
  `Pattern` in the `construction` and `construction_beamer` modes only, with
  a comment saying the construction order is referenced in external texts.
  The other modes use the default.
- `examples/wallpaper_groups/`: remove the `with_inverses` workaround
  (`construction.py`), its unit test, and the README's note about #3. The
  view-coverage test stays and now checks the library fix.

## Testing

Library tests (`uv run --package caleidoscope pytest`):

- `Transform2D.inverse`: composing with the original gives the identity, for
  a rotation about a non-origin pivot, a translation, and a glide
  reflection; a singular matrix raises `ValueError`.
- `Transform2D.is_close`: true within tolerance, false outside.
- `Pattern`: README square in a 6×6 region gives 36 tiles by default and 9
  with `include_inverses=False`; a pattern of only mirrors keeps its
  generator count; listing both directions of a translation gives 2
  generators, not 4.

Regression check: before the change, generate the output of every example
(`examples/*/main.py` and the basic scripts, all modes) into a scratch
directory; after the change, regenerate and diff. The p31m construction
`.tex` files must be byte-identical. Any other difference is reported with
an explanation, not assumed harmless.

Example tests (`uv run --package wallpaper-groups pytest examples/wallpaper_groups`)
must still pass after removing the workaround.
