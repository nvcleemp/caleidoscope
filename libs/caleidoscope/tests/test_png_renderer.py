"""Tests for PngRenderer output content.

Mirrors test_tikz_renderer.py/test_svg_renderer.py's structure, adapted for
raster output: behaviors are asserted via pixel sampling (image.getpixel)
instead of string/Element inspection.
"""

from caleidoscope import PngRenderer, Transform2D
from caleidoscope.constructed_pattern import Tile


def _make_tile(
    edges: list[tuple[int, int, str]],
    polygons: list[tuple[list[int], str]] | None = None,
) -> Tile:
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    return Tile(vertices, edges, polygons or [], Transform2D(), ())


def test_initialize_produces_expected_image_size() -> None:
    renderer = PngRenderer(scale=10)
    renderer.initialize(center_x=0, center_y=0, width=10, height=10)
    image = renderer.finalize()
    # Padded box (min=(-5,-5), max=(5,5), padded by the default margin of 1)
    # is (-4,-4)-(4,4): an 8x8 world-unit box, times scale=10 -> 80x80 px.
    assert image.size == (80, 80)


def test_initialize_image_size_respects_center_and_scale() -> None:
    renderer = PngRenderer(scale=10)
    renderer.initialize(center_x=2, center_y=-1, width=4, height=6)
    image = renderer.finalize()
    # Same padded box as the TikZ/SVG asymmetric case: (1,-3)-(3,1), a
    # 2x4 world-unit box, times scale=10 -> 20x40 px.
    assert image.size == (20, 40)


def test_render_tile_draws_edge_with_style() -> None:
    renderer = PngRenderer({"a": "stroke:#ff0000;stroke-width:1"}, scale=10)
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "a")]))
    image = renderer.finalize()
    # Edge (0,0)-(1,0) maps to the pixel row y=40 (world y=0 -> py=(4-0)*10),
    # spanning px 40..50 (world x in [0,1] -> px=(x+4)*10).
    assert image.getpixel((45, 40)) == (255, 0, 0, 255)


def test_render_tile_edge_draws_nothing_with_empty_style_by_default() -> None:
    renderer = PngRenderer(scale=10)
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "")]))
    image = renderer.finalize()
    assert image.getpixel((45, 40)) == (0, 0, 0, 0)


def test_render_tile_scales_stroke_width_by_scale() -> None:
    # stroke-width is in world units, like coordinates - scale=100 makes a
    # 0.1-world-unit stroke 10px wide. Sampling the pure midpoint of the
    # edge (away from either endpoint) avoids any ambiguity from how
    # Pillow caps a thick line's ends.
    renderer = PngRenderer({"a": "stroke:#ff0000;stroke-width:0.1"}, scale=100)
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "a")]))
    image = renderer.finalize()
    assert image.getpixel((450, 400)) == (255, 0, 0, 255)


def test_render_tile_with_edge_filter_renders_only_matching_edges() -> None:
    renderer = PngRenderer(
        {"a": "stroke:#ff0000;stroke-width:1", "b": "stroke:#00ff00;stroke-width:1"},
        scale=10,
    )
    renderer.initialize()
    tile = _make_tile([(0, 1, "a"), (1, 2, "b")])
    renderer.render_tile(tile, edge_filter=lambda edge, _: edge[2] == "a")
    image = renderer.finalize()
    # (0,1,"a") is the bottom edge (world y=0, px row 40); (1,2,"b") is the
    # right edge (world x=1, px column 50). Only "a" should be drawn.
    assert image.getpixel((45, 40)) == (255, 0, 0, 255)
    assert image.getpixel((50, 35)) == (0, 0, 0, 0)


def test_render_tile_draws_polygon_with_fill() -> None:
    renderer = PngRenderer({"face": "fill:#0000ff;fill-opacity:0.5;stroke:none"}, scale=10)
    renderer.initialize()
    renderer.render_tile(_make_tile([], polygons=[([0, 1, 2, 3], "face")]))
    image = renderer.finalize()
    # Interior of the unit square, well away from any edge pixel.
    assert image.getpixel((45, 35)) == (0, 0, 255, 128)


def test_render_tile_polygon_draws_nothing_with_empty_style_by_default() -> None:
    renderer = PngRenderer(scale=10)
    renderer.initialize()
    renderer.render_tile(_make_tile([], polygons=[([0, 1, 2, 3], "")]))
    image = renderer.finalize()
    assert image.getpixel((45, 35)) == (0, 0, 0, 0)


def test_render_tile_with_polygon_filter_renders_only_matching_polygons() -> None:
    renderer = PngRenderer(
        {"a": "fill:#0000ff;fill-opacity:1;stroke:none", "b": "fill:#00ff00;fill-opacity:1;stroke:none"},
        scale=10,
    )
    renderer.initialize()
    tile = _make_tile([], polygons=[([0, 1, 2, 3], "a")])
    renderer.render_tile(tile, polygon_filter=lambda polygon, _: polygon[1] == "z")
    image = renderer.finalize()
    assert image.getpixel((45, 35)) == (0, 0, 0, 0)


def test_render_tile_draws_polygon_before_edge() -> None:
    renderer = PngRenderer(
        {
            "face": "fill:#0000ff;fill-opacity:0.5;stroke:none",
            "a": "stroke:#ff0000;stroke-width:1",
        },
        scale=10,
    )
    renderer.initialize()
    tile = _make_tile([(0, 1, "a")], polygons=[([0, 1, 2, 3], "face")])
    renderer.render_tile(tile)
    image = renderer.finalize()
    # The bottom edge sits on the polygon's boundary; if the polygon fill
    # were drawn after the edge, its translucent blue would blend on top
    # and this pixel would no longer be pure opaque red.
    assert image.getpixel((45, 40)) == (255, 0, 0, 255)


def test_initialize_resets_state_between_uses() -> None:
    renderer = PngRenderer({"a": "stroke:#ff0000;stroke-width:1"}, scale=10)
    renderer.initialize()
    renderer.render_tile(_make_tile([(0, 1, "a")]))
    renderer.initialize()  # re-initializing should discard the previous tile's output
    image = renderer.finalize()
    assert image.getpixel((45, 40)) == (0, 0, 0, 0)
