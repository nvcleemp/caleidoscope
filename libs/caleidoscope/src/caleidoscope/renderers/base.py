"""
Base renderer protocol for the Caleidoscope project.

This module defines the interface that all renderers must implement
to work with the Pattern class.
"""
from typing import Callable, Protocol, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..constructed_pattern import Tile


class Renderer(Protocol):
    """
    Protocol defining the interface for pattern renderers.

    Renderers are responsible for converting geometric patterns into
    specific output formats (TikZ, PNG, SVG, etc.). The Pattern class
    uses this interface to delegate rendering concerns.

    Usage:
        1. Call initialize() once at the start with the boundary
        2. Call render_tile() for each tile in the pattern
        3. Call finalize() once at the end to get the result
    """

    def initialize(self,
        center_x: float = 0,
        center_y: float = 0,
        width: float = 10,
        height: float = 10) -> None:
        """
        Initialize the renderer with the rendering boundary.

        This method is called once before any tiles are rendered.
        Use it to set up the rendering context, bounding box, or
        any initial state.

        Args:
            center_x: The x-coordinate of the center of the rendering region.
            center_y: The y-coordinate of the center of the rendering region.
            width: The width of the rendering region.
            height: The height of the rendering region.
        """
        ...

    def render_tile(
        self,
        tile: "Tile",
        edge_filter: Callable[[tuple[int, int, str], "Tile"], bool] | None = None
    ) -> None:
        """
        Render a single tile.
    
        This method is called once for each tile in the pattern.
        The vertices are already transformed to their final position.

        Args:
            tile: A Tile object representing the tile to be rendered.
            edge_filter: Optional predicate function to filter edges.
                        If provided, only edges for which edge_filter(edge, tile) returns True
                        will be rendered. If None, all edges are rendered.
                        Example: lambda edge, tile: len(edge) == 3 and edge[2] == "s0"
        """
        ...

    def finalize(self) -> Any:
        """
        Finalize rendering and return the result.

        This method is called once after all tiles have been rendered.
        Use it for cleanup and to return the final output.

        Returns:
            The rendered output. Type depends on the renderer implementation:
            - str for text-based formats (TikZ, SVG)
            - Image object for raster formats (PNG)
            - File path for file-based outputs
        """
        ...
