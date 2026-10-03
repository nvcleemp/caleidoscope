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
