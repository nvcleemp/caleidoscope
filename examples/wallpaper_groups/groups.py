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
