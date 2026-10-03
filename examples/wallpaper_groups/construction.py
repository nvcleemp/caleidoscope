"""
Construct a wallpaper group's tiles over the region needed to render (and
derive the symmetry elements of) one view.
"""

import caleidoscope
from groups import Identification, WallpaperGroup
from motif import centroid, fundamental_tile
from symmetry import View

VIEW_SIZE = 8.0
# The symmetry derivation needs group elements whose tiles land up to about
# twice as far away as the symmetry elements they describe.
CONSTRUCTION_FACTOR = 2.5


def with_inverses(identifications: list[Identification]) -> list[Identification]:
    """`identifications` plus their inverses.

    `Pattern.construct` only composes the generators it is given, so a
    translation without its inverse tiles just one quadrant. Self-gluings
    (mirrors, half-turns) are their own inverse and are not repeated.
    """
    inverses = [
        (to, frm, keep_orientation)
        for frm, to, keep_orientation in identifications
        if to not in (frm, frm[::-1])
    ]
    return identifications + inverses


def view_for(group: WallpaperGroup) -> View:
    """The rendered region: a square centred on the fundamental domain."""
    cx, cy = centroid(group.vertices)
    return View(cx, cy, VIEW_SIZE, VIEW_SIZE)


def _is_orientation_reversing(transformation: caleidoscope.Transform2D) -> bool:
    (a, b, _), (c, d, _) = transformation.matrix[0], transformation.matrix[1]
    return a * d - b * c < 0


def _mark_mirrored(tile: caleidoscope.Tile) -> caleidoscope.Tile:
    """`tile`, with its motif re-annotated if it is a mirror-image copy."""
    if not _is_orientation_reversing(tile.transformation):
        return tile
    polygons = [
        (list(indices), "motif_mirrored" if annotation == "motif" else annotation)
        for indices, annotation in tile.polygons
    ]
    return caleidoscope.Tile(
        list(tile.vertices), list(tile.edges), polygons, tile.transformation, tile.generator_sequence
    )


def construct_tiles(group: WallpaperGroup) -> list[caleidoscope.Tile]:
    """All tiles over the enlarged region around `view_for(group)`, with the
    motif of mirror-image copies annotated `motif_mirrored`."""
    view = view_for(group)
    vertices, edges, polygons = fundamental_tile(group)
    pattern = caleidoscope.Pattern(
        vertices,
        edges,
        polygons,
        center=centroid(group.vertices),
        tolerance=0.01,
        identifications=with_inverses(group.identifications),
    )
    constructed = pattern.construct(
        center_x=view.center_x,
        center_y=view.center_y,
        width=CONSTRUCTION_FACTOR * view.width,
        height=CONSTRUCTION_FACTOR * view.height,
    )
    return [_mark_mirrored(tile) for tile in constructed.get_tiles()]
