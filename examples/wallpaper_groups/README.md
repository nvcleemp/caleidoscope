# Wallpaper groups

Renders one annotated PNG for each of the 17 wallpaper groups,
`output/<group>.png` (p1, p2, pm, pg, cm, pmm, pmg, pgg, cmm, p4, p4m, p4g,
p3, p3m1, p31m, p6, p6m). Each image shows:

- an F-shaped motif in every fundamental domain: blue for copies related
  to the original by a rotation or translation, red for mirror images;
- the original fundamental domain, highlighted in yellow;
- the group's symmetry elements, in the style of the International Tables:
  mirrors as thick black lines, glide axes as thin grey lines, and
  rotation centres as a lens, triangle, square or hexagon for 2-, 3-, 4-
  and 6-fold rotations.

Each group is defined in `groups.py` as a fundamental domain plus edge
identifications. The symmetry elements are not drawn by hand: they are
derived from the transformations of the constructed tiles
(`symmetry.py`), so the annotations always match the tiling.

Run with:

```bash
uv run --package wallpaper-groups python examples/wallpaper_groups/main.py --group {p1,...,p6m,all}
```

`--group` defaults to `all`.

## Tests

The tests check, among other things, that each group's gluings produce
the intended group, by comparing the derived symmetry elements against the
standard classification:

```bash
uv run --package wallpaper-groups pytest examples/wallpaper_groups
```

These tests are not part of the root test suite or CI.
