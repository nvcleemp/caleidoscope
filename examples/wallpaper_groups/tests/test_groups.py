import pytest

from construction import construct_tiles, view_for, with_inverses
from groups import GROUPS
from motif import motif_polygon
from symmetry import derive, signature

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
