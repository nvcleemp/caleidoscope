import math

import caleidoscope
from symmetry import Line, RotationCentre, SymmetryElements, View, derive, to_tiles


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


def test_derive_combines_rotation_orders_at_one_centre():
    third_turn = caleidoscope.Transform2D.rotate(2 * math.pi / 3, 0, 0)
    half_turn = caleidoscope.Transform2D.rotate(math.pi, 0, 0)
    elements = derive([third_turn, half_turn], View(0, 0, 4, 4))
    assert [centre.order for centre in elements.rotations] == [6]
