"""
PNG renderer implementation for the Caleidoscope project.

This module provides a renderer that draws geometric patterns onto a
raster canvas using Pillow.
"""

from typing import Callable, TYPE_CHECKING

from PIL import Image, ImageColor, ImageDraw

if TYPE_CHECKING:
    from ..constructed_pattern import Tile


def _parse_style(style: str) -> dict[str, str]:
    """Parse a CSS-like style string into a property -> value dict."""
    properties = {}
    for part in style.split(";"):
        part = part.strip()
        if not part:
            continue
        key, _, value = part.partition(":")
        properties[key.strip()] = value.strip()
    return properties


def _resolve_stroke(properties: dict[str, str]) -> tuple[tuple[int, int, int, int] | None, float]:
    """Resolve a style's stroke color (or None if unset/"none") and width."""
    color = properties.get("stroke")
    width = float(properties.get("stroke-width", 1))
    if not color or color == "none":
        return None, width
    r, g, b = ImageColor.getrgb(color)[:3]
    return (r, g, b, 255), width


def _resolve_fill(properties: dict[str, str]) -> tuple[int, int, int, int] | None:
    """Resolve a style's fill color (or None if unset/"none")."""
    color = properties.get("fill")
    if not color or color == "none":
        return None
    opacity = float(properties.get("fill-opacity", 1))
    r, g, b = ImageColor.getrgb(color)[:3]
    return (r, g, b, round(255 * opacity))


class PngRenderer:
    """
    Renderer that draws geometric patterns onto a raster canvas using Pillow.

    Unlike TikzRenderer/SvgRenderer, annotation_styles' CSS-like style
    strings are parsed internally (colors are handed to
    PIL.ImageColor.getrgb()), since Pillow's drawing calls need actual
    color/width values rather than a style string it can pass through
    verbatim. finalize() returns a PIL.Image.Image directly; callers save
    it (e.g. image.save(path)) themselves.
    """

    def __init__(self, annotation_styles: dict[str, str] | None = None, scale: float = 100):
        """
        Initialize the PNG renderer.

        Args:
            annotation_styles: Maps an edge/polygon annotation to a
                                CSS-like style string (e.g.
                                "stroke:red;stroke-width:2" or
                                "fill:#0000ff;fill-opacity:0.2;stroke:none").
                                Recognized properties: stroke, stroke-width,
                                fill, fill-opacity. An unmapped or absent
                                annotation draws nothing (no default stroke,
                                unlike TikZ).
            scale: Pixels per world-unit of `fundamental_domain()`-style
                   output.
        """
        self._annotation_styles = annotation_styles or {}
        self._scale = scale
        self._image: Image.Image | None = None
        self._draw: ImageDraw.ImageDraw | None = None
        self._x_min = 0.0
        self._y_max = 0.0

    def initialize(self,
        center_x: float = 0,
        center_y: float = 0,
        width: float = 10,
        height: float = 10,
        margin: float = 1) -> None:
        """
        Initialize the renderer with a bounding box, creating the canvas.

        Args:
            center_x: The x-coordinate of the center of the rendering region.
            center_y: The y-coordinate of the center of the rendering region.
            width: The width of the rendering region.
            height: The height of the rendering region.
            margin: The distance by which the drawn area is inset from the
                    edges of the rendering region on each side.
        """
        half_width = width / 2
        half_height = height / 2
        min_x = center_x - half_width
        max_x = center_x + half_width
        min_y = center_y - half_height
        max_y = center_y + half_height

        x_min = min_x + margin
        x_max = max_x - margin
        y_min = min_y + margin
        y_max = max_y - margin

        self._x_min = x_min
        self._y_max = y_max

        pixel_width = round((x_max - x_min) * self._scale)
        pixel_height = round((y_max - y_min) * self._scale)

        self._image = Image.new("RGBA", (pixel_width, pixel_height), (0, 0, 0, 0))
        self._draw = ImageDraw.Draw(self._image)

    def _to_pixel(self, point: tuple[float, float]) -> tuple[float, float]:
        x, y = point
        return ((x - self._x_min) * self._scale, (self._y_max - y) * self._scale)

    def render_tile(
            self,
            tile: "Tile",
            edge_filter: Callable[[tuple[int, int, str], "Tile"], bool] | None = None,
            polygon_filter: Callable[[tuple[tuple[int, ...], str], "Tile"], bool] | None = None
        ) -> None:
        """
        Render a single tile onto the canvas.

        Args:
            tile: A Tile object representing the tile to be rendered.
            edge_filter: An optional callable to filter edges. Only edges for which
                         the callable returns True will be rendered. If None, all edges are rendered.
            polygon_filter: An optional callable to filter polygons. Only polygons for which
                            the callable returns True will be rendered. If None, all polygons are rendered.
        """
        assert self._draw is not None, "initialize() must be called first"

        # Polygons are drawn before edges, so edge lines are not hidden by
        # polygon fills (same rule as TikzRenderer/SvgRenderer).
        polygons = tile.polygons
        if polygon_filter is not None:
            polygons = tuple(polygon for polygon in polygons if polygon_filter(polygon, tile))
        for vertex_indices, annotation in polygons:
            style = _parse_style(self._annotation_styles.get(annotation, ""))
            fill = _resolve_fill(style)
            stroke, _ = _resolve_stroke(style)
            if fill is None and stroke is None:
                continue
            points = [self._to_pixel(tile.vertices[i]) for i in vertex_indices]
            # Note: Pillow's polygon() outline is always 1px wide - it
            # doesn't support a configurable outline width the way its
            # line() does. Irrelevant today since every current face style
            # uses stroke:none, but worth knowing if that changes.
            self._draw.polygon(points, fill=fill, outline=stroke)

        edges = tile.edges
        if edge_filter is not None:
            edges = tuple(edge for edge in edges if edge_filter(edge, tile))
        for v1, v2, annotation in edges:
            style = _parse_style(self._annotation_styles.get(annotation, ""))
            stroke, stroke_width = _resolve_stroke(style)
            if stroke is None:
                continue
            self._draw.line(
                [self._to_pixel(tile.vertices[v1]), self._to_pixel(tile.vertices[v2])],
                fill=stroke,
                width=round(stroke_width),
            )

    def finalize(self) -> Image.Image:
        """
        Finalize rendering and return the rendered image.

        Returns:
            The PIL.Image.Image containing every rendered polygon and edge.
        """
        assert self._image is not None, "initialize() must be called first"
        return self._image
