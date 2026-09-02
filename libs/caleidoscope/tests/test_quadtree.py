"""Tests for the QuadTree spatial data structure."""

import math

import pytest

from caleidoscope.quadtree import Boundary, QuadTree, QuadTreeNode, euclidean_distance


def test_euclidean_distance() -> None:
    assert euclidean_distance((0.0, 0.0), (3.0, 4.0)) == pytest.approx(5.0)


class TestBoundary:
    def test_contains_point_inside(self) -> None:
        b = Boundary(0, 0, 5, 5)
        assert b.contains((2, 2))

    def test_contains_point_on_edge(self) -> None:
        b = Boundary(0, 0, 5, 5)
        assert b.contains((5, 0))
        assert b.contains((0, 5))

    def test_does_not_contain_point_outside(self) -> None:
        b = Boundary(0, 0, 5, 5)
        assert not b.contains((6, 0))
        assert not b.contains((0, -6))

    def test_bounds_returns_corners(self) -> None:
        b = Boundary(1, 2, 3, 4)
        assert b.bounds() == (-2, -2, 4, 6)

    def test_raises_on_non_positive_half_width(self) -> None:
        with pytest.raises(ValueError, match="half_width"):
            Boundary(0, 0, 0, 5)

    def test_raises_on_non_positive_half_height(self) -> None:
        with pytest.raises(ValueError, match="half_height"):
            Boundary(0, 0, 5, -1)

    def test_intersects_overlapping(self) -> None:
        a = Boundary(0, 0, 5, 5)
        b = Boundary(3, 3, 5, 5)
        assert a.intersects(b)
        assert b.intersects(a)

    def test_intersects_touching_at_edge(self) -> None:
        a = Boundary(0, 0, 5, 5)
        b = Boundary(10, 0, 5, 5)  # a's right edge (x=5) touches b's left edge (x=5)
        assert a.intersects(b)

    def test_does_not_intersect_separated_in_x(self) -> None:
        a = Boundary(0, 0, 5, 5)
        b = Boundary(20, 0, 5, 5)
        assert not a.intersects(b)
        assert not b.intersects(a)

    def test_does_not_intersect_separated_in_y(self) -> None:
        a = Boundary(0, 0, 5, 5)
        b = Boundary(0, 20, 5, 5)
        assert not a.intersects(b)

    def test_intersects_when_one_contains_the_other(self) -> None:
        outer = Boundary(0, 0, 10, 10)
        inner = Boundary(0, 0, 1, 1)
        assert outer.intersects(inner)
        assert inner.intersects(outer)


class TestQuadTree:
    def test_insert_new_point_succeeds(self) -> None:
        tree = QuadTree(Boundary(0, 0, 10, 10))
        assert tree.insert((1.0, 2.0), tolerance=0.01) is True
        assert tree.size() == 1

    def test_insert_exact_duplicate_fails(self) -> None:
        tree = QuadTree(Boundary(0, 0, 10, 10))
        tree.insert((1.0, 2.0), tolerance=0.01)
        assert tree.insert((1.0, 2.0), tolerance=0.01) is False
        assert tree.size() == 1

    def test_insert_within_tolerance_fails(self) -> None:
        tree = QuadTree(Boundary(0, 0, 10, 10))
        tree.insert((1.0, 2.0), tolerance=0.01)
        assert tree.insert((1.0001, 2.0001), tolerance=0.01) is False

    def test_insert_outside_tolerance_succeeds(self) -> None:
        tree = QuadTree(Boundary(0, 0, 10, 10))
        tree.insert((1.0, 2.0), tolerance=0.01)
        assert tree.insert((1.1, 2.1), tolerance=0.01) is True
        assert tree.size() == 2

    def test_insert_outside_boundary_fails(self) -> None:
        tree = QuadTree(Boundary(0, 0, 5, 5))
        assert tree.insert((100.0, 100.0), tolerance=0.01) is False
        assert tree.size() == 0

    def test_default_boundary_accepts_points_near_origin(self) -> None:
        tree = QuadTree()
        assert tree.insert((10.0, -10.0), tolerance=0.01) is True

    def test_clear_resets_size_and_forgets_points(self) -> None:
        tree = QuadTree(Boundary(0, 0, 10, 10))
        tree.insert((1.0, 2.0), tolerance=0.01)
        tree.clear()
        assert tree.size() == 0
        # A point identical to one inserted before clear() must be accepted again.
        assert tree.insert((1.0, 2.0), tolerance=0.01) is True

    def test_subdivision_preserves_all_distinct_points(self) -> None:
        # Default node capacity is 4; insert enough distinct points to force
        # at least one subdivision and verify none are lost or double-counted.
        tree = QuadTree(Boundary(0, 0, 100, 100))
        points = [(float(i), float(i)) for i in range(10)]
        for p in points:
            assert tree.insert(p, tolerance=0.01) is True
        assert tree.size() == 10

    def test_subdivision_still_detects_duplicates_across_children(self) -> None:
        tree = QuadTree(Boundary(0, 0, 100, 100))
        for i in range(10):
            tree.insert((float(i), float(i)), tolerance=0.01)
        # A near-duplicate of a point that ended up in a subdivided child
        # must still be rejected.
        assert tree.insert((0.0001, 0.0001), tolerance=0.01) is False
        assert tree.size() == 10


class TestQuadTreeNode:
    def test_is_leaf_before_and_after_subdivide(self) -> None:
        node = QuadTreeNode(Boundary(0, 0, 10, 10))
        assert node.is_leaf()
        node.subdivide()
        assert not node.is_leaf()
        assert len(node.children) == 4

    def test_insert_into_children_with_no_children_returns_false(self) -> None:
        node = QuadTreeNode(Boundary(0, 0, 10, 10))
        assert node._insert_into_children((0.0, 0.0)) is False

    def test_insert_into_children_returns_false_when_no_child_contains_point(self) -> None:
        node = QuadTreeNode(Boundary(0, 0, 10, 10))
        node.subdivide()
        assert node._insert_into_children((1000.0, 1000.0)) is False
