# Wallpaper Groups Example Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new example, `examples/wallpaper_groups/`, that writes one annotated PNG per wallpaper group (all 17) to `output/<group>.png`.

**Architecture:** Each group is a fundamental domain plus edge identifications, fed to the existing `caleidoscope.Pattern`. The symmetry elements (rotation centres, mirrors, glide axes) are derived from the constructed tiles' transformations with `Transform2D.classify()`. They are emitted as two extra synthetic `Tile`s, so everything is drawn as annotated edges and polygons by any renderer. Correctness of each group's gluings is tested by comparing a derived signature against the standard table.

**Tech Stack:** Python ≥ 3.13, uv workspace, `caleidoscope` (workspace library), Pillow (via caleidoscope), pytest.

**Spec:** `docs/superpowers/specs/2026-10-03-wallpaper-groups-design.md`

## Global Constraints

- Requires Python >= 3.13; never call system `python` — always `uv run ...` from the repository root.
- No changes to `libs/caleidoscope/` (the library).
- New workspace member name: `wallpaper-groups`; directory `examples/wallpaper_groups/`.
- `uv.lock` must be updated and committed (CI runs `uv run --locked`).
- Root `[tool.pytest.ini_options] testpaths` and `.github/workflows/tests.yml` stay unchanged.
- Output: `examples/wallpaper_groups/output/<group>.png` (already git-ignored by the root `output/` rule). Filename is the only label; no text in images.
- Commit messages: `<type>(<scope>): <subject>`, scope `wallpaper-groups`, subject ≤ 50 chars, imperative, no period; end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Work on branch `feat/wallpaper-groups` (already checked out; it contains the spec commit).
- Modules are imported as top-level modules (`from groups import ...`): `main.py` runs as a script from its own directory, and pytest gets `pythonpath = ["."]` from the member's `pyproject.toml`.

## File Structure

```
examples/wallpaper_groups/
  pyproject.toml      # member + dev group (pytest) + pytest config
  README.md
  groups.py           # WallpaperGroup dataclass, GROUPS (17 definitions)
  motif.py            # F motif, automatic placement, fundamental_tile()
  symmetry.py         # View, Line, derive(), signature(), to_tiles()
  construction.py     # with_inverses(), view_for(), construct_tiles()
  main.py             # PNG_STYLES, render_png(), CLI
  tests/
    test_groups.py    # per-group: defined, motif inside, coverage, signature
    test_symmetry.py  # unit tests for Line, derive, to_tiles
```

---

### Task 1: Group definitions, motif and tile construction

**Files:**
- Create: `examples/wallpaper_groups/pyproject.toml`
- Create: `examples/wallpaper_groups/groups.py`
- Create: `examples/wallpaper_groups/motif.py`
- Create: `examples/wallpaper_groups/symmetry.py` (only `View` for now)
- Create: `examples/wallpaper_groups/construction.py`
- Test: `examples/wallpaper_groups/tests/test_groups.py`
- Modify: `uv.lock` (via `uv lock`)

**Interfaces:**
- Consumes: `caleidoscope.Pattern(vertices, edges, polygons, center, tolerance, identifications)`, `Pattern.construct(center_x, center_y, width, height) -> ConstructedPattern`, `ConstructedPattern.get_tiles() -> list[Tile]`, `caleidoscope.Tile(vertices, edges, polygons, transformation, generator_sequence)` (fields are stored as tuples), `Transform2D.matrix` (3×3 nested lists).
- Produces:
  - `groups.Point = tuple[float, float]`, `groups.Identification = tuple[tuple[int, int], tuple[int, int], bool]`
  - `groups.WallpaperGroup(name: str, vertices: list[Point], identifications: list[Identification])`
  - `groups.GROUPS: dict[str, WallpaperGroup]` in the order p1, p2, pm, pg, cm, pmm, pmg, pgg, cmm, p4, p4m, p4g, p3, p3m1, p31m, p6, p6m
  - `motif.centroid(vertices) -> Point`, `motif.motif_polygon(vertices) -> list[Point]`, `motif.fundamental_tile(group) -> (vertices, edges, polygons)` with annotations `domain_edge`, `domain`, `motif`
  - `symmetry.View(center_x, center_y, width, height)` with `.contains(p) -> bool`
  - `construction.VIEW_SIZE = 8.0`, `construction.with_inverses(identifications) -> list[Identification]`, `construction.view_for(group) -> View`, `construction.construct_tiles(group) -> list[caleidoscope.Tile]` (mirror-image copies have their motif annotated `motif_mirrored`)

- [ ] **Step 1: Create the workspace member**

`examples/wallpaper_groups/pyproject.toml`:

```toml
[project]
name = "wallpaper-groups"
version = "0.1.0"
description = "Annotated PNG for each of the 17 wallpaper groups"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "caleidoscope",
]

[dependency-groups]
dev = [
    "pytest>=9.1.1",
]

[tool.uv.sources]
caleidoscope = { workspace = true }

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

Also create a placeholder `examples/wallpaper_groups/README.md` containing just `# Wallpaper groups` (Task 3 fills it in; `readme` must exist for the build).

Run: `uv lock && uv sync`
Expected: `uv.lock` now lists `wallpaper-groups`; no errors.

- [ ] **Step 2: Write the failing tests**

`examples/wallpaper_groups/tests/test_groups.py`:

```python
import pytest

from construction import construct_tiles, view_for, with_inverses
from groups import GROUPS
from motif import motif_polygon

GROUP_NAMES = [
    "p1", "p2", "pm", "pg", "cm", "pmm", "pmg", "pgg", "cmm",
    "p4", "p4m", "p4g", "p3", "p3m1", "p31m", "p6", "p6m",
]


def test_all_seventeen_groups_are_defined():
    assert list(GROUPS) == GROUP_NAMES


def test_with_inverses_skips_self_gluings():
    mirror = ((0, 1), (0, 1), False)
    half_turn = ((1, 2), (2, 1), True)
    translation = ((0, 3), (1, 2), True)
    assert with_inverses([mirror, half_turn, translation]) == [
        mirror, half_turn, translation, ((1, 2), (0, 3), True),
    ]


def _inside_convex(point, polygon):
    """Strictly inside a counter-clockwise convex polygon."""
    px, py = point
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
        if (bx - ax) * (py - ay) - (by - ay) * (px - ax) <= 0:
            return False
    return True


@pytest.mark.parametrize("name", GROUP_NAMES)
def test_motif_inside_domain(name):
    domain = GROUPS[name].vertices
    assert all(_inside_convex(p, domain) for p in motif_polygon(domain))


def _inside_polygon(point, polygon):
    """Inside (or on the boundary of) a convex polygon of either orientation."""
    px, py = point
    signs = {
        (bx - ax) * (py - ay) - (by - ay) * (px - ax) > 0
        for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1])
        if abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) > 1e-9
    }
    return len(signs) <= 1


@pytest.mark.parametrize("name", GROUP_NAMES)
def test_tiles_cover_view_corners(name):
    # Catches missing inverse generators: without them a translation tiles
    # only one quadrant, leaving view corners empty.
    group = GROUPS[name]
    view = view_for(group)
    tiles = construct_tiles(group)
    n = len(group.vertices)
    corners = [
        (view.center_x + sx * view.width / 2, view.center_y + sy * view.height / 2)
        for sx in (-1, 1)
        for sy in (-1, 1)
    ]
    for corner in corners:
        assert any(_inside_polygon(corner, list(tile.vertices[:n])) for tile in tiles), corner


@pytest.mark.parametrize("name", GROUP_NAMES)
def test_mirror_copies_are_marked(name):
    tiles = construct_tiles(GROUPS[name])
    annotations = {annotation for tile in tiles for _, annotation in tile.polygons}
    # Exactly the groups with an orientation-reversing element have mirror copies.
    has_reflections = name not in {"p1", "p2", "p4", "p3", "p6"}
    assert ("motif_mirrored" in annotations) == has_reflections
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups -v`
Expected: collection error, `ModuleNotFoundError: No module named 'construction'`.

- [ ] **Step 4: Write `groups.py`**

`examples/wallpaper_groups/groups.py`:

```python
"""
The 17 wallpaper groups, each given as a fundamental domain plus the edge
identifications (in `caleidoscope.Pattern`'s format) that generate the group.

Notation used in the comments below:

- mirror:    an edge glued to itself, orientation reversed: ((a, b), (a, b), False)
- half-turn: an edge glued to itself reversed, about its midpoint: ((a, b), (b, a), True)
- rot @ P:   the two edges meeting at P glued by a rotation about P
- glide:     an edge glued to the opposite edge by an orientation-reversing map
"""

import math
from dataclasses import dataclass

type Point = tuple[float, float]
type Identification = tuple[tuple[int, int], tuple[int, int], bool]


@dataclass(frozen=True)
class WallpaperGroup:
    """A wallpaper group, given by a fundamental domain and its gluings."""

    name: str
    # Domain corners, counter-clockwise.
    vertices: list[Point]
    identifications: list[Identification]


SQRT3 = math.sqrt(3)

# Rectangle used by the groups with a rectangular (or rhombic) lattice. Its
# sides are unequal so no image looks more symmetric than its group.
W, H = 2.0, 1.2
RECTANGLE: list[Point] = [(0, 0), (W, 0), (W, H), (0, H)]

MIRROR_BOTTOM: Identification = ((0, 1), (0, 1), False)
MIRROR_RIGHT: Identification = ((1, 2), (1, 2), False)
MIRROR_TOP: Identification = ((3, 2), (3, 2), False)
MIRROR_LEFT: Identification = ((0, 3), (0, 3), False)
HALF_TURN_BOTTOM: Identification = ((0, 1), (1, 0), True)
HALF_TURN_RIGHT: Identification = ((1, 2), (2, 1), True)
HALF_TURN_TOP: Identification = ((3, 2), (2, 3), True)
HALF_TURN_LEFT: Identification = ((0, 3), (3, 0), True)
TRANSLATE_LEFT_RIGHT: Identification = ((0, 3), (1, 2), True)
TRANSLATE_BOTTOM_TOP: Identification = ((0, 1), (3, 2), True)
# (x, y) -> (x + W, H - y): glide along the horizontal line y = H/2.
GLIDE_LEFT_RIGHT: Identification = ((0, 3), (2, 1), False)

SQUARE_SIDE = 1.5
SQUARE: list[Point] = [(0, 0), (SQUARE_SIDE, 0), (SQUARE_SIDE, SQUARE_SIDE), (0, SQUARE_SIDE)]

TRIANGLE_SIDE = 1.8


def _polar(r: float, degrees: float) -> Point:
    return (r * math.cos(math.radians(degrees)), r * math.sin(math.radians(degrees)))


GROUPS: dict[str, WallpaperGroup] = {
    group.name: group
    for group in [
        WallpaperGroup(
            "p1",
            [(0, 0), (2.0, 0), (2.7, 1.8), (0.7, 1.8)],
            [TRANSLATE_LEFT_RIGHT, TRANSLATE_BOTTOM_TOP],
        ),
        # Half of an oblique cell; the 2-fold centres sit at the midpoints of
        # the bottom and top edges.
        WallpaperGroup(
            "p2",
            [(0, 0), (2.0, 0), (2.4, 1.2), (0.4, 1.2)],
            [HALF_TURN_BOTTOM, HALF_TURN_TOP, TRANSLATE_LEFT_RIGHT],
        ),
        WallpaperGroup("pm", RECTANGLE, [MIRROR_BOTTOM, MIRROR_TOP, TRANSLATE_LEFT_RIGHT]),
        WallpaperGroup("pg", RECTANGLE, [TRANSLATE_BOTTOM_TOP, GLIDE_LEFT_RIGHT]),
        WallpaperGroup("cm", RECTANGLE, [MIRROR_BOTTOM, MIRROR_TOP, GLIDE_LEFT_RIGHT]),
        WallpaperGroup("pmm", RECTANGLE, [MIRROR_BOTTOM, MIRROR_RIGHT, MIRROR_TOP, MIRROR_LEFT]),
        WallpaperGroup("pmg", RECTANGLE, [MIRROR_BOTTOM, MIRROR_TOP, HALF_TURN_LEFT, HALF_TURN_RIGHT]),
        WallpaperGroup("pgg", RECTANGLE, [HALF_TURN_BOTTOM, HALF_TURN_TOP, GLIDE_LEFT_RIGHT]),
        WallpaperGroup("cmm", RECTANGLE, [MIRROR_BOTTOM, MIRROR_LEFT, MIRROR_RIGHT, HALF_TURN_TOP]),
        # 4-fold centres at corners 0 and 2, 2-fold centres at corners 1 and 3.
        WallpaperGroup("p4", SQUARE, [((0, 1), (0, 3), True), ((2, 1), (2, 3), True)]),
        WallpaperGroup(
            "p4m",
            [(0, 0), (SQUARE_SIDE, 0), (SQUARE_SIDE, SQUARE_SIDE)],
            [((0, 1), (0, 1), False), ((1, 2), (1, 2), False), ((2, 0), (2, 0), False)],
        ),
        # 4-fold centre at corner 0, mirrors through corner 2.
        WallpaperGroup("p4g", SQUARE, [((0, 1), (0, 3), True), MIRROR_RIGHT, MIRROR_TOP]),
        # 60/120 rhombus; 3-fold rotations about the obtuse corners 1 and 3.
        WallpaperGroup(
            "p3",
            [(0, 0), (TRIANGLE_SIDE, 0), (1.5 * TRIANGLE_SIDE, SQRT3 / 2 * TRIANGLE_SIDE),
             (0.5 * TRIANGLE_SIDE, SQRT3 / 2 * TRIANGLE_SIDE)],
            [((1, 0), (1, 2), True), ((3, 0), (3, 2), True)],
        ),
        WallpaperGroup(
            "p3m1",
            [(0, 0), (TRIANGLE_SIDE, 0), _polar(TRIANGLE_SIDE, 60)],
            [((0, 1), (0, 1), False), ((1, 2), (1, 2), False), ((2, 0), (2, 0), False)],
        ),
        # Isosceles triangle with a 120-degree apex at corner 0; mirror base.
        WallpaperGroup(
            "p31m",
            [(0, 0), (TRIANGLE_SIDE, 0), _polar(TRIANGLE_SIDE, 120)],
            [((0, 1), (0, 2), True), ((1, 2), (1, 2), False)],
        ),
        # 6-fold centre at corner 0; 2-fold centre at the midpoint of the
        # opposite edge.
        WallpaperGroup(
            "p6",
            [(0, 0), (TRIANGLE_SIDE, 0), _polar(TRIANGLE_SIDE, 60)],
            [((0, 1), (0, 2), True), ((1, 2), (2, 1), True)],
        ),
        # 30-60-90 triangle: 30 degrees at corner 0, 90 at corner 1.
        WallpaperGroup(
            "p6m",
            [(0, 0), (TRIANGLE_SIDE, 0), (TRIANGLE_SIDE, TRIANGLE_SIDE / SQRT3)],
            [((0, 1), (0, 1), False), ((1, 2), (1, 2), False), ((2, 0), (2, 0), False)],
        ),
    ]
}
```

- [ ] **Step 5: Write `motif.py`**

`examples/wallpaper_groups/motif.py`:

```python
"""
The F-shaped motif and the assembly of a group's fundamental tile: domain
outline, domain polygon and motif, as `caleidoscope.Pattern` input.
"""

import math

from groups import Point, WallpaperGroup

# A chiral "F" (no symmetry of its own), centred on its bounding box.
_F_RAW: list[Point] = [
    (0, 0), (0.25, 0), (0.25, 0.45), (0.6, 0.45), (0.6, 0.65),
    (0.25, 0.65), (0.25, 0.8), (0.75, 0.8), (0.75, 1.0), (0, 1.0),
]
F_SHAPE: list[Point] = [(x - 0.375, y - 0.5) for x, y in _F_RAW]
_F_RADIUS = max(math.hypot(x, y) for x, y in F_SHAPE)

# Fraction of the largest disc around the anchor (inside the domain) that the
# motif's circumscribed circle may use.
MOTIF_FILL = 0.85


def centroid(vertices: list[Point]) -> Point:
    """Area centroid of a simple polygon."""
    area = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(vertices, vertices[1:] + vertices[:1]):
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area /= 2
    return (cx / (6 * area), cy / (6 * area))


def _distance_to_line(p: Point, a: Point, b: Point) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    return abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / math.hypot(bx - ax, by - ay)


def motif_anchor(vertices: list[Point]) -> Point:
    """Where the motif goes: the incentre of a triangle, else the centroid."""
    if len(vertices) == 3:
        a, b, c = vertices
        la, lb, lc = math.dist(b, c), math.dist(a, c), math.dist(a, b)
        total = la + lb + lc
        return (
            (la * a[0] + lb * b[0] + lc * c[0]) / total,
            (la * a[1] + lb * b[1] + lc * c[1]) / total,
        )
    return centroid(vertices)


def motif_polygon(vertices: list[Point]) -> list[Point]:
    """The F motif, scaled to fit inside the (convex) domain around its anchor."""
    anchor = motif_anchor(vertices)
    clearance = min(
        _distance_to_line(anchor, a, b) for a, b in zip(vertices, vertices[1:] + vertices[:1])
    )
    scale = MOTIF_FILL * clearance / _F_RADIUS
    return [(anchor[0] + scale * x, anchor[1] + scale * y) for x, y in F_SHAPE]


def fundamental_tile(
    group: WallpaperGroup,
) -> tuple[list[Point], list[tuple[int, int, str]], list[tuple[list[int], str]]]:
    """Vertices, edges and polygons of `group`'s fundamental tile.

    The domain's corners come first, so the group's identifications (which
    index them) stay valid; the motif's points follow.
    """
    n = len(group.vertices)
    motif = motif_polygon(group.vertices)
    vertices = list(group.vertices) + motif
    edges = [(i, (i + 1) % n, "domain_edge") for i in range(n)]
    polygons = [
        (list(range(n)), "domain"),
        (list(range(n, n + len(motif))), "motif"),
    ]
    return vertices, edges, polygons
```

- [ ] **Step 6: Write `symmetry.py` (View only)**

`examples/wallpaper_groups/symmetry.py`:

```python
"""
Derive the symmetry elements (rotation centres, mirror lines, glide axes) of
a constructed pattern from its tiles' transformations, and turn them into
synthetic tiles that any caleidoscope renderer can draw.
"""

import math
from dataclasses import dataclass

import caleidoscope

type Point = tuple[float, float]

TOLERANCE = 1e-6


@dataclass(frozen=True)
class View:
    """An axis-aligned rectangle, given by its centre and size."""

    center_x: float
    center_y: float
    width: float
    height: float

    def contains(self, p: Point) -> bool:
        return (
            abs(p[0] - self.center_x) <= self.width / 2
            and abs(p[1] - self.center_y) <= self.height / 2
        )
```

(`math` and `caleidoscope` are used by the code Task 2 appends.)

- [ ] **Step 7: Write `construction.py`**

`examples/wallpaper_groups/construction.py`:

```python
"""
Construct a wallpaper group's tiles over the region needed to render (and
derive the symmetry elements of) one view.
"""

import caleidoscope
from groups import Identification, WallpaperGroup
from motif import centroid, fundamental_tile
from symmetry import View

VIEW_SIZE = 8.0
# The symmetry derivation needs group elements whose tiles land up to about
# twice as far away as the symmetry elements they describe.
CONSTRUCTION_FACTOR = 2.5


def with_inverses(identifications: list[Identification]) -> list[Identification]:
    """`identifications` plus their inverses.

    `Pattern.construct` only composes the generators it is given, so a
    translation without its inverse tiles just one quadrant. Self-gluings
    (mirrors, half-turns) are their own inverse and are not repeated.
    """
    inverses = [
        (to, frm, keep_orientation)
        for frm, to, keep_orientation in identifications
        if to not in (frm, frm[::-1])
    ]
    return identifications + inverses


def view_for(group: WallpaperGroup) -> View:
    """The rendered region: a square centred on the fundamental domain."""
    cx, cy = centroid(group.vertices)
    return View(cx, cy, VIEW_SIZE, VIEW_SIZE)


def _is_orientation_reversing(transformation: caleidoscope.Transform2D) -> bool:
    (a, b, _), (c, d, _) = transformation.matrix[0], transformation.matrix[1]
    return a * d - b * c < 0


def _mark_mirrored(tile: caleidoscope.Tile) -> caleidoscope.Tile:
    """`tile`, with its motif re-annotated if it is a mirror-image copy."""
    if not _is_orientation_reversing(tile.transformation):
        return tile
    polygons = [
        (list(indices), "motif_mirrored" if annotation == "motif" else annotation)
        for indices, annotation in tile.polygons
    ]
    return caleidoscope.Tile(
        list(tile.vertices), list(tile.edges), polygons, tile.transformation, tile.generator_sequence
    )


def construct_tiles(group: WallpaperGroup) -> list[caleidoscope.Tile]:
    """All tiles over the enlarged region around `view_for(group)`, with the
    motif of mirror-image copies annotated `motif_mirrored`."""
    view = view_for(group)
    vertices, edges, polygons = fundamental_tile(group)
    pattern = caleidoscope.Pattern(
        vertices,
        edges,
        polygons,
        center=centroid(group.vertices),
        tolerance=0.01,
        identifications=with_inverses(group.identifications),
    )
    constructed = pattern.construct(
        center_x=view.center_x,
        center_y=view.center_y,
        width=CONSTRUCTION_FACTOR * view.width,
        height=CONSTRUCTION_FACTOR * view.height,
    )
    return [_mark_mirrored(tile) for tile in constructed.get_tiles()]
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups -v`
Expected: all tests in `test_groups.py` PASS (1 + 1 + 17 × 3 = 53).

- [ ] **Step 9: Verify the coverage test really detects missing inverses**

Temporarily change `identifications=with_inverses(group.identifications)` to `identifications=group.identifications` in `construction.py` and rerun the command from Step 8.
Expected: `test_tiles_cover_view_corners` FAILS for at least p1, pm, pg, cm. Revert the change and rerun: all PASS.

- [ ] **Step 10: Commit**

```bash
git add examples/wallpaper_groups uv.lock
git commit -m "feat(wallpaper-groups): define the 17 groups

Fundamental domains with edge identifications for all 17
wallpaper groups, an automatically placed F motif, and tile
construction with inverse generators and mirror-copy marking.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Symmetry derivation and group signature tests

**Files:**
- Modify: `examples/wallpaper_groups/symmetry.py` (append after `View`)
- Modify: `examples/wallpaper_groups/tests/test_groups.py` (append)
- Create: `examples/wallpaper_groups/tests/test_symmetry.py`

**Interfaces:**
- Consumes: `symmetry.View`, `construction.construct_tiles`, `construction.view_for`, `groups.GROUPS`; `Transform2D.classify()` returning `.type` in {`"rotation"`, `"reflection"`, `"glide_reflection"`, …} with `.parameters`: rotation `{"angle_rad", "pivot"}`, reflection/glide `{"axis_point", "axis_direction", ...}`; `Transform2D.rotate(angle, px, py)`, `Transform2D.reflect_x()`, `Transform2D.translate(dx, dy)`, `Transform2D.compose(other)` (applies `other` first).
- Produces:
  - `symmetry.Line(angle: float, offset: float)` with `Line.through(point, direction)`, `.direction`, `.distance_to(p)`, `.is_close(other)`, `.clip(view) -> tuple[Point, Point] | None`
  - `symmetry.RotationCentre(point: Point, order: int)`
  - `symmetry.SymmetryElements(rotations: list[RotationCentre], mirrors: list[Line], glides: list[Line])`
  - `symmetry.derive(transformations: list[Transform2D], view: View) -> SymmetryElements`
  - `symmetry.signature(elements) -> tuple[frozenset[int], frozenset[int], int, bool]`

- [ ] **Step 1: Write the failing unit tests**

`examples/wallpaper_groups/tests/test_symmetry.py`:

```python
import math

import caleidoscope
from symmetry import Line, View, derive


def test_line_through_is_canonical_for_either_direction():
    assert Line.through((0, 1), (1, 0)).is_close(Line.through((5, 1), (-1, 0)))


def test_line_clip_to_view():
    segment = Line.through((0, 1), (1, 0)).clip(View(0, 0, 4, 4))
    assert segment is not None
    assert sorted(segment) == [(-2.0, 1.0), (2.0, 1.0)]


def test_line_clip_misses_view():
    assert Line.through((0, 5), (1, 0)).clip(View(0, 0, 4, 4)) is None


def test_derive_classifies_elements():
    view = View(0, 0, 4, 4)
    half_turn = caleidoscope.Transform2D.rotate(math.pi, 1, 0)
    quarter_turn = caleidoscope.Transform2D.rotate(math.pi / 2, 1, 0)
    mirror = caleidoscope.Transform2D.reflect_x()
    # Mirror in the x-axis followed by a translation along it: classifies as
    # a glide, but the x-axis is already a mirror, so it is no glide axis.
    fake_glide = caleidoscope.Transform2D.translate(1, 0).compose(mirror)
    # (x, y) -> (x + 1, 1 - y): a genuine glide along y = 1/2.
    real_glide = caleidoscope.Transform2D.translate(1, 1).compose(mirror)
    elements = derive(
        [caleidoscope.Transform2D(), half_turn, quarter_turn, mirror, fake_glide, real_glide], view
    )
    assert len(elements.rotations) == 1
    assert elements.rotations[0].order == 4
    assert math.dist(elements.rotations[0].point, (1, 0)) < 1e-9
    assert len(elements.mirrors) == 1 and elements.mirrors[0].is_close(Line(0.0, 0.0))
    assert len(elements.glides) == 1 and elements.glides[0].is_close(Line(0.0, 0.5))
```

Append to `examples/wallpaper_groups/tests/test_groups.py` (and add `from symmetry import derive, signature` to its imports):

```python
# (orders of rotation centres on a mirror, orders off every mirror,
#  number of mirror directions, has glide axes)
EXPECTED_SIGNATURES = {
    "p1": (set(), set(), 0, False),
    "p2": (set(), {2}, 0, False),
    "pm": (set(), set(), 1, False),
    "pg": (set(), set(), 0, True),
    "cm": (set(), set(), 1, True),
    "pmm": ({2}, set(), 2, False),
    "pmg": (set(), {2}, 1, True),
    "pgg": (set(), {2}, 0, True),
    "cmm": ({2}, {2}, 2, True),
    "p4": (set(), {2, 4}, 0, False),
    "p4m": ({2, 4}, set(), 4, True),
    "p4g": ({2}, {4}, 2, True),
    "p3": (set(), {3}, 0, False),
    "p3m1": ({3}, set(), 3, True),
    "p31m": ({3}, {3}, 3, True),
    "p6": (set(), {2, 3, 6}, 0, False),
    "p6m": ({2, 3, 6}, set(), 6, True),
}


def test_expected_signatures_are_distinct():
    signatures = {
        (frozenset(on), frozenset(off), dirs, glide)
        for on, off, dirs, glide in EXPECTED_SIGNATURES.values()
    }
    assert len(signatures) == 17


@pytest.mark.parametrize("name", GROUP_NAMES)
def test_group_signature(name):
    group = GROUPS[name]
    tiles = construct_tiles(group)
    elements = derive([tile.transformation for tile in tiles], view_for(group))
    on, off, dirs, glide = EXPECTED_SIGNATURES[name]
    assert signature(elements) == (frozenset(on), frozenset(off), dirs, glide)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups -v`
Expected: collection errors, `ImportError: cannot import name 'Line' from 'symmetry'` (and `derive`).

- [ ] **Step 3: Implement the derivation**

Append to `examples/wallpaper_groups/symmetry.py`:

```python
@dataclass(frozen=True)
class Line:
    """A line in canonical form: angle in [0, pi) and signed offset.

    Its points p satisfy n . p = offset, with n = (-sin angle, cos angle).
    """

    angle: float
    offset: float

    @staticmethod
    def through(point: Point, direction: Point) -> "Line":
        angle = math.atan2(direction[1], direction[0]) % math.pi
        if angle > math.pi - TOLERANCE:
            angle = 0.0
        return Line(angle, -math.sin(angle) * point[0] + math.cos(angle) * point[1])

    @property
    def direction(self) -> Point:
        return (math.cos(self.angle), math.sin(self.angle))

    def distance_to(self, p: Point) -> float:
        return abs(-math.sin(self.angle) * p[0] + math.cos(self.angle) * p[1] - self.offset)

    def is_close(self, other: "Line", tolerance: float = TOLERANCE) -> bool:
        return (
            abs(self.angle - other.angle) < tolerance
            and abs(self.offset - other.offset) < tolerance
        )

    def clip(self, view: View) -> tuple[Point, Point] | None:
        """The part of this line inside `view`, or None if it misses it."""
        dx, dy = self.direction
        # Point on the line closest to the view's centre.
        nx, ny = -dy, dx
        shift = self.offset - (nx * view.center_x + ny * view.center_y)
        px, py = view.center_x + shift * nx, view.center_y + shift * ny
        t_min, t_max = -math.inf, math.inf
        for p, d, low, high in (
            (px, dx, view.center_x - view.width / 2, view.center_x + view.width / 2),
            (py, dy, view.center_y - view.height / 2, view.center_y + view.height / 2),
        ):
            if abs(d) < TOLERANCE:
                if not low <= p <= high:
                    return None
                continue
            t1, t2 = (low - p) / d, (high - p) / d
            t_min, t_max = max(t_min, min(t1, t2)), min(t_max, max(t1, t2))
        if t_min >= t_max:
            return None
        return (px + t_min * dx, py + t_min * dy), (px + t_max * dx, py + t_max * dy)


@dataclass(frozen=True)
class RotationCentre:
    point: Point
    order: int


@dataclass(frozen=True)
class SymmetryElements:
    rotations: list[RotationCentre]
    mirrors: list[Line]
    glides: list[Line]


def _add_line(lines: list[Line], line: Line) -> None:
    if not any(line.is_close(other) for other in lines):
        lines.append(line)


def derive(transformations: list[caleidoscope.Transform2D], view: View) -> SymmetryElements:
    """Collect the symmetry elements of the given group elements that meet `view`.

    A line only counts as a glide axis if it is not also a mirror line: a
    mirror composed with a translation along itself classifies as a glide.
    """
    rotations: list[tuple[Point, int]] = []
    mirrors: list[Line] = []
    glide_candidates: list[Line] = []
    for transformation in transformations:
        classification = transformation.classify()
        parameters = classification.parameters
        match classification.type:
            case "rotation":
                pivot = parameters["pivot"]
                order = round(2 * math.pi / abs(parameters["angle_rad"]))
                for i, (other, other_order) in enumerate(rotations):
                    if math.dist(pivot, other) < TOLERANCE:
                        rotations[i] = (other, max(order, other_order))
                        break
                else:
                    rotations.append((pivot, order))
            case "reflection":
                _add_line(mirrors, Line.through(parameters["axis_point"], parameters["axis_direction"]))
            case "glide_reflection":
                _add_line(glide_candidates, Line.through(parameters["axis_point"], parameters["axis_direction"]))
    glides = [g for g in glide_candidates if not any(g.is_close(m) for m in mirrors)]
    return SymmetryElements(
        rotations=[RotationCentre(p, order) for p, order in rotations if view.contains(p)],
        mirrors=[m for m in mirrors if m.clip(view) is not None],
        glides=[g for g in glides if g.clip(view) is not None],
    )


type Signature = tuple[frozenset[int], frozenset[int], int, bool]


def signature(elements: SymmetryElements) -> Signature:
    """(orders of centres on a mirror, orders of centres off every mirror,
    number of mirror directions, has glide axes)."""
    on_mirror: set[int] = set()
    off_mirror: set[int] = set()
    for centre in elements.rotations:
        if any(m.distance_to(centre.point) < TOLERANCE for m in elements.mirrors):
            on_mirror.add(centre.order)
        else:
            off_mirror.add(centre.order)
    directions: list[float] = []
    for m in elements.mirrors:
        if not any(abs(m.angle - d) < TOLERANCE for d in directions):
            directions.append(m.angle)
    return frozenset(on_mirror), frozenset(off_mirror), len(directions), bool(elements.glides)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups -v`
Expected: all PASS (Task 1's 53 + 1 + 17 signatures + 4 unit tests = 75).

If a `test_group_signature[...]` case fails, the fault is most likely in that group's identifications in `groups.py`, not in `derive`: print `signature(...)` for the group, compare with the table, and re-derive the gluings by hand (compose the generators). Do not edit `EXPECTED_SIGNATURES`: it is the standard classification.

- [ ] **Step 5: Commit**

```bash
git add examples/wallpaper_groups
git commit -m "feat(wallpaper-groups): derive symmetry elements

Classify the constructed tiles' transformations into rotation
centres, mirror lines and glide axes, and test every group's
gluings against its standard signature.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Symmetry-element tiles, PNG rendering, CLI and README

**Files:**
- Modify: `examples/wallpaper_groups/symmetry.py` (append)
- Modify: `examples/wallpaper_groups/tests/test_symmetry.py` (append)
- Create: `examples/wallpaper_groups/main.py`
- Modify: `examples/wallpaper_groups/README.md`

**Interfaces:**
- Consumes: everything from Tasks 1–2; `caleidoscope.ConstructedPattern(tiles, center_x, center_y, width, height).render(renderer, edge_filter=None, polygon_filter=None, margin=1)`; `caleidoscope.PngRenderer(annotation_styles, scale)` (styles are CSS-like: `stroke`, `stroke-width` in world units, `fill`, `fill-opacity`; unmapped annotations draw nothing; `finalize()` returns an RGBA `PIL.Image.Image` with a transparent background).
- Produces:
  - `symmetry.to_tiles(elements: SymmetryElements, view: View, marker_size: float) -> list[caleidoscope.Tile]` — `[lines_tile, markers_tile]`; edge annotations `glide`, `mirror`; polygon annotations `rot2`, `rot3`, `rot4`, `rot6`
  - `main.PNG_STYLES: dict[str, str]`, `main.render_png(group) -> PIL.Image.Image`, CLI `--group {p1,…,p6m,all}`

- [ ] **Step 1: Write the failing test**

Append to `examples/wallpaper_groups/tests/test_symmetry.py` (extend the import to `from symmetry import Line, RotationCentre, SymmetryElements, View, derive, to_tiles`):

```python
def test_to_tiles_draws_lines_then_markers():
    elements = SymmetryElements(
        rotations=[RotationCentre((0, 0), 4), RotationCentre((1, 1), 2)],
        mirrors=[Line.through((0, 0), (1, 0))],
        glides=[Line.through((0, 0.5), (1, 0))],
    )
    lines_tile, markers_tile = to_tiles(elements, View(0, 0, 4, 4), 0.1)
    assert [edge[2] for edge in lines_tile.edges] == ["glide", "mirror"]
    assert [polygon[1] for polygon in markers_tile.polygons] == ["rot4", "rot2"]
    square = markers_tile.polygons[0][0]
    assert all(math.isclose(math.dist(markers_tile.vertices[i], (0, 0)), 0.1) for i in square)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups/tests/test_symmetry.py -v`
Expected: collection error, `ImportError: cannot import name 'to_tiles' from 'symmetry'`.

- [ ] **Step 3: Implement `to_tiles`**

Append to `examples/wallpaper_groups/symmetry.py`:

```python
def _marker(centre: RotationCentre, angle: float, size: float) -> list[Point]:
    """Outline of a rotation-centre marker, with a symmetry axis along `angle`."""
    x, y = centre.point
    if centre.order == 2:
        # Lens: two circular arcs between (-size, 0) and (size, 0), bulging
        # by half the size.
        bulge = size / 2
        k = (size * size - bulge * bulge) / (2 * bulge)
        radius = k + bulge
        half = math.atan2(size, k)
        arc = [(radius * math.sin(t), radius * math.cos(t) - k)
               for t in (half - 2 * half * i / 8 for i in range(9))]
        local = arc + [(-px, -py) for px, py in arc[1:-1]]
    else:
        # Regular polygon with a vertex on the axis, except squares, which
        # get an edge parallel to it.
        offset = math.pi / 4 if centre.order == 4 else 0.0
        local = [
            (size * math.cos(offset + 2 * math.pi * i / centre.order),
             size * math.sin(offset + 2 * math.pi * i / centre.order))
            for i in range(centre.order)
        ]
    c, s = math.cos(angle), math.sin(angle)
    return [(x + c * px - s * py, y + s * px + c * py) for px, py in local]


def to_tiles(elements: SymmetryElements, view: View, marker_size: float) -> list[caleidoscope.Tile]:
    """Two tiles in world coordinates: the clipped mirror/glide lines, then
    the rotation-centre markers (so markers are drawn on top of lines).

    A marker is aligned with a mirror through its centre, if there is one.
    """
    line_vertices: list[Point] = []
    line_edges: list[tuple[int, int, str]] = []
    for annotation, lines in (("glide", elements.glides), ("mirror", elements.mirrors)):
        for line in lines:
            segment = line.clip(view)
            if segment is None:
                continue
            line_vertices.extend(segment)
            line_edges.append((len(line_vertices) - 2, len(line_vertices) - 1, annotation))

    marker_vertices: list[Point] = []
    marker_polygons: list[tuple[list[int], str]] = []
    for centre in elements.rotations:
        angle = next(
            (m.angle for m in elements.mirrors if m.distance_to(centre.point) < TOLERANCE), 0.0
        )
        outline = _marker(centre, angle, marker_size)
        start = len(marker_vertices)
        marker_vertices.extend(outline)
        marker_polygons.append((list(range(start, start + len(outline))), f"rot{centre.order}"))

    identity = caleidoscope.Transform2D()
    return [
        caleidoscope.Tile(line_vertices, line_edges, [], identity, ()),
        caleidoscope.Tile(marker_vertices, [], marker_polygons, identity, ()),
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups -v`
Expected: all 76 PASS.

- [ ] **Step 5: Write `main.py`**

`examples/wallpaper_groups/main.py`:

```python
"""
Render one annotated PNG per wallpaper group: an F motif in every
fundamental domain (mirror-image copies in a second colour), one domain
highlighted, and the group's mirrors, glide axes and rotation centres.
"""

import argparse
from pathlib import Path

from PIL import Image

import caleidoscope
from construction import construct_tiles, view_for
from groups import GROUPS, WallpaperGroup
from symmetry import derive, to_tiles

OUTPUT_DIR = Path(__file__).parent / "output"

SCALE = 100
MARKER_SIZE = 0.12

PNG_STYLES = {
    "domain": "fill:#ffd54f;stroke:none",
    "domain_edge": "stroke:#e0e0e0;stroke-width:0.01",
    "motif": "fill:#1e88e5;stroke:none",
    "motif_mirrored": "fill:#e53935;stroke:none",
    "glide": "stroke:#616161;stroke-width:0.015",
    "mirror": "stroke:#000000;stroke-width:0.04",
    "rot2": "fill:#000000;stroke:none",
    "rot3": "fill:#000000;stroke:none",
    "rot4": "fill:#000000;stroke:none",
    "rot6": "fill:#000000;stroke:none",
}


def render_png(group: WallpaperGroup) -> Image.Image:
    """The annotated tiling of `group`, on a white background."""
    view = view_for(group)
    tiles = construct_tiles(group)
    elements = derive([tile.transformation for tile in tiles], view)
    scene = caleidoscope.ConstructedPattern(
        tiles + to_tiles(elements, view, MARKER_SIZE),
        view.center_x,
        view.center_y,
        view.width,
        view.height,
    )
    image = scene.render(
        caleidoscope.PngRenderer(PNG_STYLES, scale=SCALE),
        # Only the fundamental tile itself shows its domain highlighted.
        polygon_filter=lambda polygon, tile: polygon[1] != "domain" or not tile.generator_sequence,
        margin=0,
    )
    background = Image.new("RGBA", image.size, "white")
    return Image.alpha_composite(background, image)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=[*GROUPS, "all"], default="all")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    names = list(GROUPS) if args.group == "all" else [args.group]
    for name in names:
        path = OUTPUT_DIR / f"{name}.png"
        render_png(GROUPS[name]).save(path)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Generate the images and inspect them**

Run: `uv run --package wallpaper-groups python examples/wallpaper_groups/main.py`
Expected: 17 lines `Wrote .../output/<group>.png`; each image is 800×800.

Open every PNG and check:
- the view is fully tiled (no empty corners);
- one domain (centre) is filled yellow;
- blue F's for direct copies, red F's for mirror images; p1, p2, p4, p3, p6 have no red F's;
- mirrors are thick black lines, glide axes thin dark-grey lines, distinguishable from the light-grey domain edges;
- rotation markers: lens/triangle/square/hexagon for orders 2/3/4/6, at the places the signature table implies (e.g. p4g: squares off the mirrors, lenses at mirror crossings).

If glide axes and domain edges are hard to tell apart, adjust only `PNG_STYLES` colours/widths.

- [ ] **Step 7: Write the README**

`examples/wallpaper_groups/README.md`:

````markdown
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
````

- [ ] **Step 8: Run all tests (example and library)**

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups && uv run --locked --package caleidoscope pytest`
Expected: example 76 passed; library suite passes unchanged; `--locked` succeeds (lockfile up to date).

- [ ] **Step 9: Commit**

```bash
git add examples/wallpaper_groups
git commit -m "feat(wallpaper-groups): render annotated PNGs

Draw mirrors, glide axes and rotation-centre markers as extra
tiles, render one PNG per group with mirror-image motifs in a
second colour, and document the example.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
