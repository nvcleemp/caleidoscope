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
