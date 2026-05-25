"""
TikZ renderer implementation for the Caleidoscope project.

This module provides a renderer that generates TikZ/LaTeX code
for geometric patterns.
"""


from collections.abc import Callable

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..constructed_pattern import Tile


def _get_tikz_edges(
        points: tuple[tuple[float, float], ...],
        lines: tuple[tuple[int, int] | tuple[int, int, str], ...],
        annotation_styles: dict[str, str]) -> str:
    """
    Create a TikZ representation of lines connecting the given points.

    Args:
        points: Tuple of vertex coordinates as tuples (x, y).
        lines: Tuple of edge tuples (v1_index, v2_index) or (v1_index, v2_index, annotation)
              connecting vertices. Annotations are currently ignored.
        annotation_styles: A dictionary mapping annotation strings to TikZ styles.

    Returns:
        A string containing the TikZ code for the edges.
    """
    result = []
    for edge in lines:
        if len(edge) == 3:
            p1, p2, annotation = edge
            style = annotation_styles.get(annotation, "")
            result.append(f"  \\draw[{style}] ({points[p1][0]:.3f}, {points[p1][1]:.3f}) -- ({points[p2][0]:.3f}, {points[p2][1]:.3f});\n")
        else:
            p1, p2 = edge[0], edge[1]
            result.append(f"  \\draw ({points[p1][0]:.3f}, {points[p1][1]:.3f}) -- ({points[p2][0]:.3f}, {points[p2][1]:.3f});\n")
    return "".join(result)


class TikzRenderer:
    """
    Renderer that generates TikZ/LaTeX code for geometric patterns.

    The output is a string containing TikZ drawing commands that can be
    wrapped in a tikzpicture environment or standalone document.
    """

    def __init__(self, annotation_styles: dict[str, str] | None = None):
        """Initialize the TikZ renderer."""
        self._buffer: list[str] = []
        self._annotation_styles = annotation_styles or {}

    def initialize(self,
        center_x: float = 0,
        center_y: float = 0,
        width: float = 10,
        height: float = 10) -> None:
        """
        Initialize the renderer with a bounding box.

        Args:
            center_x: The x-coordinate of the center of the rendering region.
            center_y: The y-coordinate of the center of the rendering region.
            width: The width of the rendering region.
            height: The height of the rendering region.
        """
        self._buffer = []
        # Calculate bounds based on center and size
        half_width = width / 2
        half_height = height / 2
        min_x = center_x - half_width
        max_x = center_x + half_width
        min_y = center_y - half_height
        max_y = center_y + half_height
        # Add bounding box with 1-unit padding
        self._buffer.append(
            f"  \\useasboundingbox ({min_x + 1},{min_y + 1}) "
            f"rectangle ({max_x - 1},{max_y - 1});\n"
        )

    def render_tile(
            self,
            tile: "Tile",
            edge_filter: Callable[[tuple[int, int] | tuple[int, int, str]], bool] | None = None
        ) -> None:
        """
        Render a single tile as TikZ draw commands.

        Args:
            tile: A Tile object representing the tile to be rendered.
            edge_filter: An optional callable to filter edges. Only edges for which
                         the callable returns True will be rendered. If None, all edges are rendered.
        """
        if edge_filter is not None:
            filtered_edges = tuple(edge for edge in tile.edges if edge_filter(edge))
            self._buffer.append(_get_tikz_edges(tile.vertices, filtered_edges, self._annotation_styles))
        else:
            self._buffer.append(_get_tikz_edges(tile.vertices, tile.edges, self._annotation_styles))

    def finalize(self) -> str:
        """
        Finalize rendering and return the TikZ code.

        Returns:
            A string containing all TikZ drawing commands.
        """
        return "".join(self._buffer)
