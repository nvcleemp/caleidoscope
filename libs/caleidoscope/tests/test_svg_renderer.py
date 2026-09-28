"""Tests for SvgRenderer output content.

Mirrors test_tikz_renderer.py's structure, adapted for SVG's element shapes
and the y-flip (SVG's y-axis grows downward; this codebase's geometry, like
TikZ's, treats y as growing upward).
"""

import xml.etree.ElementTree as ET

from caleidoscope import SvgRenderer, Transform2D
from caleidoscope.constructed_pattern import Tile


def _make_tile(
    edges: list[tuple[int, int, str]],
    polygons: list[tuple[list[int], str]] | None = None,
) -> Tile:
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    return Tile(vertices, edges, polygons or [], Transform2D(), ())


def test_initialize_produces_expected_viewbox() -> None:
    renderer = SvgRenderer()
    renderer.initialize(center_x=0, center_y=0, width=10, height=10)
    root = renderer.finalize()
    assert root.get("viewBox") == "-4.0 -4.0 8.0 8.0"


def test_initialize_viewbox_flips_y_relative_to_tikz_bounding_box() -> None:
    # TikzRenderer with the same args produces bounding box (1,-3)-(3,1)
    # (min=(0,-4), max=(4,2), padded by the default margin of 1).
    # Flipping y negates the y-range to [-1, 3]: viewBox min-y is the
    # smaller value (-1), height is the unflipped span (4).
    renderer = SvgRenderer()
    renderer.initialize(center_x=2, center_y=-1, width=4, height=6)
    root = renderer.finalize()
    assert root.get("viewBox") == "1.0 -1.0 2.0 4.0"


def test_render_tile_draws_edge_with_flipped_y_and_empty_style_by_default() -> None:
    renderer = SvgRenderer()
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 2, "")]))
    root = renderer.finalize()
    lines = root.findall("line")
    assert len(lines) == 1
    assert lines[0].attrib == {
        "x1": "0.000", "y1": "-0.000", "x2": "1.000", "y2": "-1.000", "style": "",
    }


def test_render_tile_applies_annotation_style_to_edge() -> None:
    renderer = SvgRenderer({"a": "stroke:red;stroke-width:2"})
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "a")]))
    root = renderer.finalize()
    assert root.find("line").get("style") == "stroke:red;stroke-width:2"


def test_render_tile_edge_falls_back_to_empty_style_for_unmapped_annotation() -> None:
    renderer = SvgRenderer({"a": "stroke:red"})
    renderer.initialize()
    renderer.render_tile(_make_tile([(1, 2, "b")]))
    root = renderer.finalize()
    assert root.find("line").get("style") == ""


def test_render_tile_with_edge_filter_renders_only_matching_edges() -> None:
    renderer = SvgRenderer()
    renderer.initialize()
    tile = _make_tile([(0, 1, "a"), (1, 2, "b")])
    renderer.render_tile(tile, edge_filter=lambda edge, _: edge[2] == "a")
    root = renderer.finalize()
    lines = root.findall("line")
    assert len(lines) == 1
    assert lines[0].get("x2") == "1.000"


def test_render_tile_draws_polygon_with_flipped_y_and_empty_style_by_default() -> None:
    renderer = SvgRenderer()
    renderer.initialize()
    renderer.render_tile(_make_tile([], polygons=[([0, 1, 2, 3], "")]))
    root = renderer.finalize()
    polygons = root.findall("polygon")
    assert len(polygons) == 1
    assert polygons[0].attrib == {
        "points": "0.000,-0.000 1.000,-0.000 1.000,-1.000 0.000,-1.000",
        "style": "",
    }


def test_render_tile_applies_annotation_style_to_polygon() -> None:
    renderer = SvgRenderer({"face": "stroke:blue;fill:#3388ff33"})
    renderer.initialize()
    renderer.render_tile(_make_tile([], polygons=[([0, 1, 2, 3], "face")]))
    root = renderer.finalize()
    assert root.find("polygon").get("style") == "stroke:blue;fill:#3388ff33"


def test_render_tile_polygon_falls_back_to_empty_style_for_unmapped_annotation() -> None:
    renderer = SvgRenderer({"a": "stroke:red"})
    renderer.initialize()
    renderer.render_tile(_make_tile([], polygons=[([0, 1, 2], "b")]))
    root = renderer.finalize()
    assert root.find("polygon").get("style") == ""


def test_render_tile_with_polygon_filter_renders_only_matching_polygons() -> None:
    renderer = SvgRenderer()
    renderer.initialize()
    tile = _make_tile([], polygons=[([0, 1, 2], "a"), ([0, 2, 3], "b")])
    renderer.render_tile(tile, polygon_filter=lambda polygon, _: polygon[1] == "a")
    root = renderer.finalize()
    polygons = root.findall("polygon")
    assert len(polygons) == 1
    assert polygons[0].get("points") == "0.000,-0.000 1.000,-0.000 1.000,-1.000"


def test_render_tile_draws_polygons_before_edges() -> None:
    renderer = SvgRenderer()
    renderer.initialize()
    tile = _make_tile([(0, 1, "")], polygons=[([0, 1, 2], "")])
    renderer.render_tile(tile)
    root = renderer.finalize()
    children = list(root)
    assert [child.tag for child in children] == ["polygon", "line"]


def test_finalize_keeps_multiple_tiles_in_render_order() -> None:
    renderer = SvgRenderer()
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "")]))
    renderer.render_tile(_make_tile([(1, 2, "")]))
    root = renderer.finalize()
    lines = root.findall("line")
    assert [line.get("x2") for line in lines] == ["1.000", "1.000"]
    assert [line.get("y2") for line in lines] == ["-0.000", "-1.000"]


def test_initialize_resets_state_between_uses() -> None:
    renderer = SvgRenderer()
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "")]))
    renderer.initialize()  # re-initializing should discard the previous tile's output
    root = renderer.finalize()
    assert root.findall("line") == []
