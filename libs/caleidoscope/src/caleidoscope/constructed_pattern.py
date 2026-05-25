"""
Constructed pattern module for the Caleidoscope project.

This module provides the ConstructedPattern class that stores pre-generated
tiles for a specific boundary, enabling multiple rendering passes with
different filters or styles.
"""
from dataclasses import dataclass
from typing import Callable, Any
from .renderers import Renderer


# ============================================================================
# Tile Data Structure
# ============================================================================


@dataclass(frozen=True)
class Tile:
    """
    Represents a single tile in a constructed pattern.

    A tile consists of vertices (transformed to their final position)
    and edges connecting those vertices.

    Attributes:
        vertices: List of vertex coordinates as tuples (x, y).
        edges: List of edge tuples (v1_index, v2_index) or (v1_index, v2_index, annotation)
              connecting vertices. The optional third element is a string annotation for the edge.
    """
    vertices: tuple[tuple[float, float], ...]
    edges: tuple[tuple[int, int] | tuple[int, int, str], ...]

    def __init__(
        self,
        vertices: list[tuple[float, float]],
        edges: list[tuple[int, int] | tuple[int, int, str]]
    ):
        """
        Initialize a Tile.

        Args:
            vertices: List of vertex coordinates as tuples (x, y).
            edges: List of edge tuples (v1_index, v2_index) or (v1_index, v2_index, annotation).
        """
        # Convert to tuples for immutability
        object.__setattr__(self, 'vertices', tuple(vertices))
        object.__setattr__(self, 'edges', tuple(edges))


# ============================================================================
# ConstructedPattern Class
# ============================================================================


class ConstructedPattern:
    """
    A pre-generated pattern with all tiles constructed for a specific boundary.

    This class stores all the tiles that would be rendered within a given
    boundary, allowing for multiple rendering passes with different filters
    or styles without reconstructing the pattern each time.

    The pattern can be rendered multiple times using different renderers
    or edge filters to produce different outputs from the same tile data.
    """

    def __init__(
        self,
        tiles: list[Tile],
        center_x: float,
        center_y: float,
        width: float,
        height: float
    ):
        """
        Initialize a ConstructedPattern.

        Args:
            tiles: List of Tile objects representing the pattern.
            center_x: X-coordinate of the center of the rendering region.
            center_y: Y-coordinate of the center of the rendering region.
            width: Width of the rendering region.
            height: Height of the rendering region.
        """
        self._tiles = tiles
        self._center_x = center_x
        self._center_y = center_y
        self._width = width
        self._height = height

    @property
    def tile_count(self) -> int:
        """
        Get the number of tiles in this constructed pattern.

        Returns:
            The number of tiles.
        """
        return len(self._tiles)

    def get_tiles(self) -> list[Tile]:
        """
        Get all tiles in this constructed pattern.

        Returns:
            A list of Tile objects. This is a copy to prevent external modification.
        """
        return self._tiles.copy()

    def render(
        self,
        renderer: Renderer,
        edge_filter: Callable[[tuple[int, int] | tuple[int, int, str]], bool] | None = None
    ) -> Any:
        """
        Render the constructed pattern using the given renderer.

        This method allows rendering the same pattern multiple times with
        different renderers or edge filters without reconstructing the tiles.

        Args:
            renderer: A renderer object implementing the Renderer protocol.
                     The renderer handles format-specific rendering logic.
            edge_filter: Optional predicate function to filter edges.
                        If provided, only edges for which edge_filter(edge) returns True
                        will be rendered. If None, all edges are rendered.
                        Example: lambda edge: len(edge) == 3 and edge[2] == "s0"

        Returns:
            The rendered output, as determined by renderer.finalize().
            Typically a string for text formats (TikZ, SVG) or an image
            object for raster formats (PNG).
        """
        # Initialize renderer with the boundary
        renderer.initialize(
            center_x=self._center_x,
            center_y=self._center_y,
            width=self._width,
            height=self._height
        )

        # Render each tile
        for tile in self._tiles:
            # Apply edge filter if provided
            if edge_filter is not None:
                filtered_edges = [edge for edge in tile.edges if edge_filter(edge)]
            else:
                filtered_edges = list(tile.edges)

            # Only render the tile if it has edges (after filtering)
            if filtered_edges:
                renderer.render_tile(list(tile.vertices), filtered_edges)

        return renderer.finalize()
