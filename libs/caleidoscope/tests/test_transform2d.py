"""Tests for Transform2D construction, application, composition, and factories
that aren't already covered by test_classify.py."""

import math

import pytest

from caleidoscope import Transform2D


def _assert_points_close(
    actual: tuple[float, float], expected: tuple[float, float], abs_tol: float = 1e-6
) -> None:
    assert actual[0] == pytest.approx(expected[0], abs=abs_tol)
    assert actual[1] == pytest.approx(expected[1], abs=abs_tol)


def test_default_constructor_is_identity() -> None:
    t = Transform2D()
    assert t.matrix == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def test_constructor_deep_copies_input_matrix() -> None:
    matrix = [[1.0, 0.0, 5.0], [0.0, 1.0, 3.0], [0.0, 0.0, 1.0]]
    t = Transform2D(matrix)
    matrix[0][2] = 999.0
    assert t.matrix[0][2] == 5.0


def test_apply_translation() -> None:
    t = Transform2D.translate(2.0, -3.0)
    _assert_points_close(t.apply((1.0, 1.0)), (3.0, -2.0))


def test_compose_applies_right_operand_first() -> None:
    # translate(rotate(p)) should differ from rotate(translate(p)) in general.
    translate = Transform2D.translate(1.0, 0.0)
    rotate = Transform2D.rotate(math.pi / 2)

    translate_then_rotate = rotate.compose(translate)
    rotate_then_translate = translate.compose(rotate)

    # rotate(translate((0,0))) = rotate((1,0)) = (0,1)
    _assert_points_close(translate_then_rotate.apply((0.0, 0.0)), (0.0, 1.0))
    # translate(rotate((0,0))) = translate((0,0)) = (1,0)
    _assert_points_close(rotate_then_translate.apply((0.0, 0.0)), (1.0, 0.0))


def test_rotate_around_origin() -> None:
    t = Transform2D.rotate(math.pi / 2)
    _assert_points_close(t.apply((1.0, 0.0)), (0.0, 1.0))


def test_rotate_around_pivot() -> None:
    t = Transform2D.rotate(math.pi, pivot_x=2.0, pivot_y=2.0)
    # 180 degree rotation around (2, 2) maps (0, 0) to (4, 4).
    _assert_points_close(t.apply((0.0, 0.0)), (4.0, 4.0))
    # The pivot itself is a fixed point.
    _assert_points_close(t.apply((2.0, 2.0)), (2.0, 2.0))


def test_reflect_x() -> None:
    t = Transform2D.reflect_x()
    _assert_points_close(t.apply((3.0, 4.0)), (3.0, -4.0))


class TestFromOrthogonalScaling:
    def test_scales_along_axis_aligned_vectors(self) -> None:
        t = Transform2D.from_orthogonal_scaling((1.0, 0.0), 2.0, (0.0, 1.0), 3.0)
        _assert_points_close(t.apply((1.0, 1.0)), (2.0, 3.0))

    def test_scales_along_rotated_orthogonal_vectors(self) -> None:
        # Scale by 2 along the 45-degree diagonal and by 1 along its perpendicular.
        v1 = (1.0, 1.0)
        v2 = (-1.0, 1.0)
        t = Transform2D.from_orthogonal_scaling(v1, 2.0, v2, 1.0)
        # A point along v1 should scale by 2; a point along v2 should scale by 1.
        _assert_points_close(t.apply(v1), (2.0, 2.0))
        _assert_points_close(t.apply(v2), (-1.0, 1.0))

    def test_raises_on_zero_first_vector(self) -> None:
        with pytest.raises(ValueError, match="first vector"):
            Transform2D.from_orthogonal_scaling((0.0, 0.0), 2.0, (0.0, 1.0), 3.0)

    def test_raises_on_zero_second_vector(self) -> None:
        with pytest.raises(ValueError, match="second vector"):
            Transform2D.from_orthogonal_scaling((1.0, 0.0), 2.0, (0.0, 0.0), 3.0)

    def test_raises_on_non_orthogonal_vectors(self) -> None:
        with pytest.raises(ValueError, match="not orthogonal"):
            Transform2D.from_orthogonal_scaling((1.0, 0.0), 2.0, (1.0, 1.0), 3.0)


class TestFromTwoSegments:
    def test_keep_orientation_true_is_rigid_rotation(self) -> None:
        t = Transform2D.from_two_segments((0, 0), (1, 0), (0, 0), (0, 1), keep_orientation=True)
        _assert_points_close(t.apply((0, 0)), (0, 0))
        _assert_points_close(t.apply((1, 0)), (0, 1))

    def test_keep_orientation_false_maps_endpoints_and_flips(self) -> None:
        # Mapping a segment onto itself with keep_orientation=False must still
        # send a1->a2 and b1->b2, but flip a point off the segment's line.
        t = Transform2D.from_two_segments((0, 0), (1, 0), (0, 0), (1, 0), keep_orientation=False)
        _assert_points_close(t.apply((0, 0)), (0, 0))
        _assert_points_close(t.apply((1, 0)), (1, 0))
        _assert_points_close(t.apply((0, 1)), (0, -1))

    def test_keep_orientation_false_onto_different_segment(self) -> None:
        t = Transform2D.from_two_segments((0, 0), (1, 0), (5, 5), (6, 5), keep_orientation=False)
        _assert_points_close(t.apply((0, 0)), (5, 5))
        _assert_points_close(t.apply((1, 0)), (6, 5))


class TestFromTwoTriplets:
    def test_maps_translated_standard_basis(self) -> None:
        triplet_from = ((0, 0), (1, 0), (0, 1))
        triplet_to = ((5, 3), (6, 3), (5, 4))
        t = Transform2D.from_two_triplets(triplet_from, triplet_to)
        _assert_points_close(t.apply((0, 0)), (5, 3))
        _assert_points_close(t.apply((1, 0)), (6, 3))
        _assert_points_close(t.apply((0, 1)), (5, 4))

    def test_maps_arbitrary_point_by_linearity(self) -> None:
        triplet_from = ((0, 0), (2, 0), (0, 2))
        triplet_to = ((0, 0), (0, 2), (-2, 0))  # 90-degree rotation, scaled by 1
        t = Transform2D.from_two_triplets(triplet_from, triplet_to)
        # (1, 1) is the midpoint of the two basis endpoints in `from`, so its
        # image is the midpoint of the corresponding endpoints in `to`.
        _assert_points_close(t.apply((1, 1)), (-1, 1))

    def test_raises_on_collinear_basis(self) -> None:
        triplet_from = ((0, 0), (1, 0), (2, 0))  # collinear -> degenerate basis
        triplet_to = ((0, 0), (1, 0), (0, 1))
        with pytest.raises(ValueError, match="collinear|degenerate"):
            Transform2D.from_two_triplets(triplet_from, triplet_to)


class TestIdentify:
    def test_identity(self) -> None:
        assert Transform2D().identify() == "Identity"

    def test_translation(self) -> None:
        text = Transform2D.translate(5.0, 3.0).identify()
        assert "Translation" in text
        assert "5.0000" in text and "3.0000" in text

    def test_rotation(self) -> None:
        text = Transform2D.rotate(math.pi / 2, 1.0, 1.0).identify()
        assert "Rotation" in text
        assert "90.00" in text

    def test_rotation_with_negative_angle_is_normalized_to_positive_degrees(self) -> None:
        # classify() reports the raw angle from atan2, which is negative here;
        # identify() must normalize it into [0, 360) before formatting.
        text = Transform2D.rotate(-math.pi / 4).identify()
        assert "315.00" in text

    def test_reflection(self) -> None:
        text = Transform2D.reflect_x().identify()
        assert "Reflection" in text

    def test_glide_reflection(self) -> None:
        t = Transform2D.translate(2.0, 0.0).compose(Transform2D.reflect_x())
        text = t.identify()
        assert "Glide Reflection" in text

    def test_uniform_scaling(self) -> None:
        t = Transform2D([[2.5, 0.0, 0.0], [0.0, 2.5, 0.0], [0.0, 0.0, 1.0]])
        assert "Uniform Scaling" in t.identify()

    def test_non_uniform_scaling(self) -> None:
        t = Transform2D([[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 1.0]])
        assert "Non-uniform Scaling" in t.identify()

    def test_complex_affine(self) -> None:
        t = Transform2D([[1.0, 0.5, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
        assert "Complex Affine" in t.identify()


def test_repr_shows_matrix_rows() -> None:
    t = Transform2D.translate(1.0, 2.0)
    text = repr(t)
    assert text.startswith("Transform2D([")
    assert "1.000000" in text and "2.000000" in text
    assert text.count("[") == 4  # outer + three rows


@pytest.mark.parametrize(
    "transform",
    [
        Transform2D.rotate(1.0, 2.0, 3.0),
        Transform2D.translate(1.0, -2.0),
        # (x, y) -> (x + 1, 1 - y): a glide reflection.
        Transform2D.translate(1.0, 1.0).compose(Transform2D.reflect_x()),
    ],
)
def test_inverse_composes_to_identity(transform: Transform2D) -> None:
    assert transform.compose(transform.inverse()).is_close(Transform2D())
    assert transform.inverse().compose(transform).is_close(Transform2D())


def test_inverse_of_singular_matrix_raises() -> None:
    singular = Transform2D([[1.0, 2.0, 0.0], [2.0, 4.0, 0.0], [0.0, 0.0, 1.0]])
    with pytest.raises(ValueError):
        singular.inverse()


def test_is_close_within_tolerance() -> None:
    a = Transform2D.translate(1.0, 2.0)
    assert a.is_close(Transform2D.translate(1.0 + 1e-12, 2.0))
    assert not a.is_close(Transform2D.translate(1.0 + 1e-6, 2.0))
    assert a.is_close(Transform2D.translate(1.0 + 1e-6, 2.0), tolerance=1e-5)
