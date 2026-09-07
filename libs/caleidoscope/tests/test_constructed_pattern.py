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


@pytest.fixture
def pattern_with_polygons() -> Pattern:
    """A square pattern with a face polygon covering half the square, tiling by translation."""
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    edges = [
        (0, 1, "s0"),
        (1, 2, "s1"),
        (2, 3, "s0"),
        (3, 0, "s1"),
    ]
    polygons = [([0, 1, 2], "tri1"), ([0, 2, 3], "tri2")]
    center = (0.5, 0.5)
    tolerance = 0.1
    identifications = [
        ((3, 0), (1, 2), True),
        ((0, 1), (2, 3), True),
    ]
    return Pattern(vertices, edges, polygons, center, tolerance, identifications)


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


def test_polygon_filtering_partitions_all_polygons(pattern_with_polygons: Pattern) -> None:
    constructed = pattern_with_polygons.construct(width=4, height=4)
    cycle_count_all = constructed.render(TikzRenderer()).count("cycle")

    filter_tri1 = lambda polygon, _: polygon[1] == "tri1"
    cycle_count_tri1 = constructed.render(TikzRenderer(), polygon_filter=filter_tri1).count("cycle")

    filter_tri2 = lambda polygon, _: polygon[1] == "tri2"
    cycle_count_tri2 = constructed.render(TikzRenderer(), polygon_filter=filter_tri2).count("cycle")

    assert cycle_count_tri1 > 0
    assert cycle_count_tri2 > 0
    assert cycle_count_tri1 + cycle_count_tri2 == cycle_count_all


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


class _RecordingRenderer:
    def __init__(self) -> None:
        self.margin: float | None = None

    def initialize(self, center_x=0, center_y=0, width=10, height=10, margin=1) -> None:
        self.margin = margin

    def render_tile(self, tile, edge_filter=None, polygon_filter=None) -> None:
        pass

    def finalize(self):
        return self.margin


def test_render_defaults_margin_to_one(constructed_pattern: ConstructedPattern) -> None:
    assert constructed_pattern.render(_RecordingRenderer()) == 1


def test_render_forwards_custom_margin(constructed_pattern: ConstructedPattern) -> None:
    assert constructed_pattern.render(_RecordingRenderer(), margin=2.5) == 2.5
