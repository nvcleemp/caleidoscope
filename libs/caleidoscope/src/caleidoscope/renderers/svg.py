"""
SVG renderer implementation for the Caleidoscope project.

This module provides a renderer that generates SVG elements for
geometric patterns.
"""

import xml.etree.ElementTree as ET
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..constructed_pattern import Tile

SVG_NAMESPACE = "http://www.w3.org/2000/svg"


class SvgRenderer:
    """
    Renderer that generates SVG elements for geometric patterns.

    Unlike TikzRenderer, finalize() returns a complete
    xml.etree.ElementTree.Element (the <svg> root) rather than a string:
    callers who want to extend the output append further elements onto
    that root directly, and serialize (e.g. via ET.tostring) once done.
    """

    def __init__(self, annotation_styles: dict[str, str] | None = None):
        """Initialize the SVG renderer."""
        self._annotation_styles = annotation_styles or {}
        self._root: ET.Element | None = None

    def initialize(self,
        center_x: float = 0,
        center_y: float = 0,
        width: float = 10,
        height: float = 10,
        margin: float = 1) -> None:
        """
        Initialize the renderer with a bounding box, creating the <svg> root.

        Args:
            center_x: The x-coordinate of the center of the rendering region.
            center_y: The y-coordinate of the center of the rendering region.
            width: The width of the rendering region.
            height: The height of the rendering region.
            margin: The distance by which the viewBox is inset from the
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

        view_box = f"{x_min} {-y_max} {x_max - x_min} {y_max - y_min}"

        self._root = ET.Element("svg", {
            "xmlns": SVG_NAMESPACE,
            "viewBox": view_box,
        })

    def render_tile(
            self,
            tile: "Tile",
            edge_filter: Callable[[tuple[int, int, str], "Tile"], bool] | None = None,
            polygon_filter: Callable[[tuple[tuple[int, ...], str], "Tile"], bool] | None = None
        ) -> None:
        """
        Render a single tile as <line>/<polygon> elements on the root.

        Args:
            tile: A Tile object representing the tile to be rendered.
            edge_filter: An optional callable to filter edges. Only edges for which
                         the callable returns True will be rendered. If None, all edges are rendered.
            polygon_filter: An optional callable to filter polygons. Only polygons for which
                            the callable returns True will be rendered. If None, all polygons are rendered.
        """
        assert self._root is not None, "initialize() must be called first"

        # Polygons are drawn before edges, so edge lines are not hidden by
        # polygon fills (same rule as TikzRenderer).
        polygons = tile.polygons
        if polygon_filter is not None:
            polygons = tuple(polygon for polygon in polygons if polygon_filter(polygon, tile))
        for vertex_indices, annotation in polygons:
            points = " ".join(
                f"{tile.vertices[i][0]:.3f},{-tile.vertices[i][1]:.3f}" for i in vertex_indices
            )
            ET.SubElement(self._root, "polygon", {
                "points": points,
                "style": self._annotation_styles.get(annotation, ""),
            })

        edges = tile.edges
        if edge_filter is not None:
            edges = tuple(edge for edge in edges if edge_filter(edge, tile))
        for v1, v2, annotation in edges:
            x1, y1 = tile.vertices[v1]
            x2, y2 = tile.vertices[v2]
            ET.SubElement(self._root, "line", {
                "x1": f"{x1:.3f}",
                "y1": f"{-y1:.3f}",
                "x2": f"{x2:.3f}",
                "y2": f"{-y2:.3f}",
                "style": self._annotation_styles.get(annotation, ""),
            })

    def finalize(self) -> ET.Element:
        """
        Finalize rendering and return the SVG root element.

        Returns:
            The <svg> root xml.etree.ElementTree.Element containing every
            rendered polygon and edge.
        """
        assert self._root is not None, "initialize() must be called first"
        return self._root
