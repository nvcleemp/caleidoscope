"""Tests for Pattern.construct() / ConstructedPattern."""

import pytest

from caleidoscope import ConstructedPattern, Pattern, TikzRenderer


@pytest.fixture
def simple_pattern() -> Pattern:
    """A square pattern with two edge annotations, tiling by translation."""
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    edges = [
        (0, 1, "s0"),  # bottom edge
        (1, 2, "s1"),  # right edge
        (2, 3, "s0"),  # top edge
        (3, 0, "s1"),  # left edge
    ]
    center = (0.5, 0.5)
    tolerance = 0.1
    identifications = [
        ((3, 0), (1, 2), True),   # left edge to right edge
        ((0, 1), (2, 3), True),   # bottom edge to top edge
    ]
    return Pattern(vertices, edges, [], center, tolerance, identifications)


@pytest.fixture
def constructed_pattern(simple_pattern: Pattern) -> ConstructedPattern:
    return simple_pattern.construct(width=4, height=4)


def test_render_is_backwards_compatible(simple_pattern: Pattern) -> None:
    output = simple_pattern.render(TikzRenderer(), width=4, height=4)
    assert output.count("draw") > 0


def test_construct_creates_constructed_pattern(constructed_pattern: ConstructedPattern) -> None:
    assert isinstance(constructed_pattern, ConstructedPattern)
    assert constructed_pattern.tile_count == len(constructed_pattern.get_tiles())


def test_multiple_renders_are_consistent(constructed_pattern: ConstructedPattern) -> None:
    output1 = constructed_pattern.render(TikzRenderer({"s0": "red, thick", "s1": "blue, thick"}))
    output2 = constructed_pattern.render(TikzRenderer({"s0": "green, thin", "s1": "purple, thin"}))
    assert output1.count("draw") == output2.count("draw")


def test_edge_filtering_partitions_all_edges(constructed_pattern: ConstructedPattern) -> None:
    draw_count_all = constructed_pattern.render(TikzRenderer()).count("draw")

    filter_s0 = lambda edge, _: len(edge) == 3 and edge[2] == "s0"
    draw_count_s0 = constructed_pattern.render(TikzRenderer(), edge_filter=filter_s0).count("draw")

    filter_s1 = lambda edge, _: len(edge) == 3 and edge[2] == "s1"
    draw_count_s1 = constructed_pattern.render(TikzRenderer(), edge_filter=filter_s1).count("draw")

    assert draw_count_s0 > 0
    assert draw_count_s1 > 0
    assert draw_count_s0 + draw_count_s1 == draw_count_all


def test_construct_and_render_matches_direct_render(
    simple_pattern: Pattern, constructed_pattern: ConstructedPattern
) -> None:
    old_output = simple_pattern.render(TikzRenderer(), width=4, height=4)
    new_output = constructed_pattern.render(TikzRenderer())
    assert old_output.count("draw") == new_output.count("draw")


def test_get_tiles_returns_a_copy(constructed_pattern: ConstructedPattern) -> None:
    tiles = constructed_pattern.get_tiles()
    original_count = constructed_pattern.tile_count
    tiles.clear()
    assert constructed_pattern.tile_count == original_count
    assert len(constructed_pattern.get_tiles()) == original_count
