# Wallpaper groups example — design

## Goal

A new example, `examples/wallpaper_groups/`, that renders one annotated
teaching image per wallpaper group (all 17), suitable for comparing the
groups. No animation. PNG output first; SVG and TikZ may follow later, and
the design must not need group-specific rework for that.

## Scope

In scope:

- 17 fundamental domains with edge identifications, built with the existing
  `Pattern` API (no library changes).
- An asymmetric F-shaped motif in every domain; copies whose transformation
  is orientation-reversing are coloured differently.
- One fundamental domain (the identity tile) highlighted.
- Symmetry elements derived automatically from the constructed tiling and
  drawn in International Tables style: mirrors as thick lines, glide axes as
  thin grey lines (no dashes: `PngRenderer` doesn't support them), rotation
  centres as lens / triangle / square / hexagon markers for orders
  2 / 3 / 4 / 6.
- One output file per group: `output/<group>.png`. The filename is the only
  label (no text in the image).
- Tests that verify each group's gluings produce the intended group.

Out of scope (possible later additions):

- Unit-cell outline (could become an optional flag).
- SVG/TikZ output (would be a second style dict plus a `--format` flag).
- Running the example's tests in CI.

## Layout

```
examples/wallpaper_groups/
  pyproject.toml      # member "wallpaper-groups"; depends on caleidoscope; dev group: pytest
  README.md
  groups.py           # the 17 group definitions
  motif.py            # F motif + shared tile assembly (motif, domain outline, domain fill)
  symmetry.py         # derive symmetry elements from tile transformations
  main.py             # CLI + PNG rendering
  tests/
    test_groups.py    # signature test per group
  output/             # generated, git-ignored by the existing `output/` rule
```

## Group definitions (`groups.py`)

Each group is a dataclass `WallpaperGroup` with: `name`, domain `vertices`
(in order around the boundary), `identifications` (in `Pattern`'s
`((from_v1, from_v2), (to_v1, to_v2), keep_orientation)` format), and the
motif placement (`anchor`, `scale`, `rotation`). The shared code in
`motif.py` adds the boundary edges (`domain_edge`), the domain polygon
(`domain`) and the motif polygon (`motif`) so no group repeats them.
`Pattern.center` is the domain's centroid. It never lies on a rotation
centre or a mirror. In some groups it lies on a glide axis, which is fine
because a glide fixes no points.

Gluing notation: *mirror* = edge glued to itself orientation-reversed,
`((a,b),(a,b),False)`. *Half-turn* = edge glued to itself reversed about its
midpoint, `((a,b),(b,a),True)`. *Rot θ @ P* = the two edges meeting at P
glued by a rotation about P. *Glide* = an edge glued to the opposite edge by
an orientation-reversing map.

| Group | Domain | Gluings |
|---|---|---|
| p1 | parallelogram (oblique) | 2 translations |
| p2 | half of an oblique cell | bottom and top: half-turn each; left → right: translation |
| pm | rectangle | bottom and top: mirror; left → right: translation |
| pg | rectangle | bottom → top: translation; left → right: glide (x,y)↦(x+w, H−y) |
| cm | rectangle | bottom and top: mirror; left → right: glide |
| pmm | rectangle | all 4 edges: mirror |
| pmg | rectangle | bottom and top: mirror; left and right: half-turn |
| pgg | rectangle | bottom and top: half-turn; left → right: glide |
| cmm | rectangle | bottom, left, right: mirror; top: half-turn |
| p4 | square | rot 90° @ one corner O; rot 180° @ opposite corner |
| p4m | right isosceles triangle | all edges: mirror |
| p4g | square | rot 90° @ O; the two edges at the opposite corner: mirror |
| p3 | 60°/120° rhombus | rot 120° @ each obtuse corner |
| p3m1 | equilateral triangle | all edges: mirror |
| p31m | isosceles triangle, 120° apex | rot 120° @ apex; base: mirror |
| p6 | equilateral triangle | rot 60° @ O; opposite edge: half-turn |
| p6m | 30-60-90 triangle | all edges: mirror |

Rectangles have unequal sides and oblique lattices are clearly
non-rectangular, so no image looks more symmetric than its group.

## Symmetry derivation (`symmetry.py`)

Input: the transformations of all constructed tiles (`Tile.transformation`),
plus the view box. Each one is classified with `Transform2D.classify()`:

- **rotation**: grouped by pivot (within a tolerance). The order at a pivot
  is `round(2π / smallest |angle|)` over the rotations seen there.
- **reflection**: the axis is normalised to a canonical form (unit direction
  in a fixed half-plane, signed offset) and added to the set of mirror lines.
- **glide_reflection**: the axis is normalised the same way. It counts as a
  glide axis only if it is not also a mirror line (a mirror composed with a
  lattice translation along itself also classifies as a glide).

Completeness: the element that puts a mirror or pivot at distance d from the
identity tile maps that tile to about 2d away. So the construction used for
the derivation covers a region about 2.5× the view in each dimension. Only
elements that meet the view are kept.

The result is a `SymmetryElements` value (rotation centres with order;
mirror lines; glide lines) plus two helper functions:

- `signature(elements)` returns (orders of centres on a mirror, orders of
  centres off every mirror, number of distinct mirror directions, has glide
  axes). Used by the tests.
- `to_tiles(elements, view)` returns two synthetic `Tile`s with identity
  transformation and world-coordinate vertices:
  1. a lines tile: mirror and glide lines clipped to the view, edges
     annotated `mirror` / `glide`;
  2. a markers tile: polygons annotated `rot2` (lens approximated by a
     polygon), `rot3`, `rot4` or `rot6`, in a fixed orientation and a
     fixed size.

Because these are ordinary tiles with annotations, any renderer draws them.
Supporting another output format only needs a style dict.

## Rendering (`main.py`)

For each group:

1. Build the `Pattern` and construct it over the enlarged region.
2. Re-annotate the motif polygon of every tile whose transformation has
   determinant −1 from `motif` to `motif_mirrored` (by building new `Tile`s).
3. Derive the symmetry elements from the tile transformations.
4. Build a `ConstructedPattern` sized to the view, containing the pattern
   tiles followed by the lines tile and then the markers tile. Renderers draw
   tiles in order, so markers end up on top of lines, and lines on top of
   the pattern.
5. Render with `PngRenderer(PNG_STYLES, scale=SCALE)`. A polygon filter keeps
   the `domain` fill only on the identity tile
   (`tile.generator_sequence == ()`). Flatten onto a white background and
   save `output/<name>.png`.

Annotations and their roles (colours are chosen during implementation):

| Annotation | Kind | Role |
|---|---|---|
| `domain` | polygon | highlighted fundamental domain (identity tile only) |
| `domain_edge` | edge | thin light-grey domain outlines |
| `motif` | polygon | F motif, orientation-preserving copies |
| `motif_mirrored` | polygon | F motif, orientation-reversing copies |
| `mirror` | edge | thick mirror lines |
| `glide` | edge | thin grey glide axes |
| `rot2`/`rot3`/`rot4`/`rot6` | polygon | rotation-centre markers |

CLI: `--group {p1,…,p6m,all}`, default `all`.

Run:
`uv run --package wallpaper-groups python examples/wallpaper_groups/main.py`.

## Testing

`tests/test_groups.py` constructs each group, derives its symmetry elements
and asserts `signature()` against this table (each of the 17 signatures is
different):

| Group | on mirror | off mirror | mirror dirs | glides |
|---|---|---|---|---|
| p1 | – | – | 0 | no |
| p2 | – | 2 | 0 | no |
| pm | – | – | 1 | no |
| pg | – | – | 0 | yes |
| cm | – | – | 1 | yes |
| pmm | 2 | – | 2 | no |
| pmg | – | 2 | 1 | yes |
| pgg | – | 2 | 0 | yes |
| cmm | 2 | 2 | 2 | yes |
| p4 | – | 2, 4 | 0 | no |
| p4m | 2, 4 | – | 4 | yes |
| p4g | 2 | 4 | 2 | yes |
| p3 | – | 3 | 0 | no |
| p3m1 | 3 | – | 3 | yes |
| p31m | 3 | 3 | 3 | yes |
| p6 | – | 2, 3, 6 | 0 | no |
| p6m | 2, 3, 6 | – | 6 | yes |

Tests also check that the motif polygon lies strictly inside each domain.

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups`.
The root `testpaths` and CI are unchanged.

Rendering is verified by generating all 17 PNGs and inspecting them.
