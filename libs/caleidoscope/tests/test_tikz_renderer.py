"""Tests for TikzRenderer output content.

test_constructed_pattern.py only checks draw *counts*; these tests check the
actual generated TikZ strings.
"""

from caleidoscope import TikzRenderer, Transform2D
from caleidoscope.constructed_pattern import Tile


def _make_tile(
    edges: list[tuple[int, int, str]],
    polygons: list[tuple[list[int], str]] | None = None,
) -> Tile:
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    return Tile(vertices, edges, polygons or [], Transform2D(), ())


def test_initialize_produces_expected_bounding_box() -> None:
    renderer = TikzRenderer()
    renderer.initialize(center_x=0, center_y=0, width=10, height=10)
    assert renderer.finalize() == "  \\useasboundingbox (-4.0,-4.0) rectangle (4.0,4.0);\n"


def test_initialize_bounding_box_respects_center_and_size() -> None:
    renderer = TikzRenderer()
    renderer.initialize(center_x=2, center_y=-1, width=4, height=6)
    # half_width=2, half_height=3 -> min=(0,-4), max=(4,2), padded by 1 on each side.
    assert renderer.finalize() == "  \\useasboundingbox (1.0,-3.0) rectangle (3.0,1.0);\n"


def test_render_tile_uses_empty_style_by_default() -> None:
    renderer = TikzRenderer()
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "")]))
    output = renderer.finalize()
    assert "\\draw[] (0.000, 0.000) -- (1.000, 0.000);\n" in output


def test_render_tile_applies_annotation_style() -> None:
    renderer = TikzRenderer({"a": "red, thick"})
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "a")]))
    output = renderer.finalize()
    assert "\\draw[red, thick] (0.000, 0.000) -- (1.000, 0.000);\n" in output


def test_render_tile_falls_back_to_empty_style_for_unmapped_annotation() -> None:
    renderer = TikzRenderer({"a": "red"})
    renderer.initialize()
    renderer.render_tile(_make_tile([(1, 2, "b")]))
    output = renderer.finalize()
    assert "\\draw[] (1.000, 0.000) -- (1.000, 1.000);\n" in output


def test_render_tile_with_edge_filter_renders_only_matching_edges() -> None:
    renderer = TikzRenderer()
    renderer.initialize()
    tile = _make_tile([(0, 1, "a"), (1, 2, "b")])
    renderer.render_tile(tile, edge_filter=lambda edge, _: edge[2] == "a")
    output = renderer.finalize()
    assert "(0.000, 0.000) -- (1.000, 0.000)" in output
    assert "(1.000, 0.000) -- (1.000, 1.000)" not in output


def test_finalize_concatenates_multiple_tiles_in_order() -> None:
    renderer = TikzRenderer()
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "")]))
    renderer.render_tile(_make_tile([(1, 2, "")]))
    output = renderer.finalize()
    first = output.index("(0.000, 0.000) -- (1.000, 0.000)")
    second = output.index("(1.000, 0.000) -- (1.000, 1.000)")
    assert first < second


def test_initialize_resets_buffer_between_uses() -> None:
    renderer = TikzRenderer()
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "")]))
    renderer.initialize()  # re-initializing should discard the previous tile's output
    output = renderer.finalize()
    assert "draw" not in output


def test_render_tile_renders_polygon_with_style() -> None:
    renderer = TikzRenderer({"face": "blue, fill=blue!20"})
    renderer.initialize()
    renderer.render_tile(_make_tile([], polygons=[([0, 1, 2, 3], "face")]))
    output = renderer.finalize()
    assert (
        "\\draw[blue, fill=blue!20] (0.000, 0.000) -- (1.000, 0.000) -- "
        "(1.000, 1.000) -- (0.000, 1.000) -- cycle;\n"
    ) in output


def test_render_tile_polygon_uses_empty_style_by_default() -> None:
    renderer = TikzRenderer()
    renderer.initialize()
    renderer.render_tile(_make_tile([], polygons=[([0, 1, 2], "")]))
    output = renderer.finalize()
    assert "\\draw[] (0.000, 0.000) -- (1.000, 0.000) -- (1.000, 1.000) -- cycle;\n" in output


def test_render_tile_polygon_falls_back_to_empty_style_for_unmapped_annotation() -> None:
    renderer = TikzRenderer({"a": "red"})
    renderer.initialize()
    renderer.render_tile(_make_tile([], polygons=[([0, 1, 2], "b")]))
    output = renderer.finalize()
    assert "\\draw[] (0.000, 0.000) -- (1.000, 0.000) -- (1.000, 1.000) -- cycle;\n" in output


def test_render_tile_with_polygon_filter_renders_only_matching_polygons() -> None:
    renderer = TikzRenderer()
    renderer.initialize()
    tile = _make_tile([], polygons=[([0, 1, 2], "a"), ([0, 2, 3], "b")])
    renderer.render_tile(tile, polygon_filter=lambda polygon, _: polygon[1] == "a")
    output = renderer.finalize()
    assert "(0.000, 0.000) -- (1.000, 0.000) -- (1.000, 1.000) -- cycle" in output
    assert "(0.000, 0.000) -- (1.000, 1.000) -- (0.000, 1.000) -- cycle" not in output


def test_render_tile_draws_polygons_before_edges() -> None:
    renderer = TikzRenderer()
    renderer.initialize()
    tile = _make_tile([(0, 1, "")], polygons=[([0, 1, 2], "")])
    renderer.render_tile(tile)
    output = renderer.finalize()
    polygon_index = output.index("cycle")
    edge_index = output.index("\\draw[] (0.000, 0.000) -- (1.000, 0.000);\n")
    assert polygon_index < edge_index
