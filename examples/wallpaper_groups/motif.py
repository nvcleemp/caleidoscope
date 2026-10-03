"""
The F-shaped motif and the assembly of a group's fundamental tile: domain
outline, domain polygon and motif, as `caleidoscope.Pattern` input.
"""

import math

from groups import Point, WallpaperGroup

# A chiral "F" (no symmetry of its own), centred on its bounding box.
_F_RAW: list[Point] = [
    (0, 0), (0.25, 0), (0.25, 0.45), (0.6, 0.45), (0.6, 0.65),
    (0.25, 0.65), (0.25, 0.8), (0.75, 0.8), (0.75, 1.0), (0, 1.0),
]
F_SHAPE: list[Point] = [(x - 0.375, y - 0.5) for x, y in _F_RAW]
_F_RADIUS = max(math.hypot(x, y) for x, y in F_SHAPE)

# Fraction of the largest disc around the anchor (inside the domain) that the
# motif's circumscribed circle may use.
MOTIF_FILL = 0.85


def centroid(vertices: list[Point]) -> Point:
    """Area centroid of a simple polygon."""
    area = cx = cy = 0.0
    for (x1, y1), (x2, y2) in zip(vertices, vertices[1:] + vertices[:1]):
        cross = x1 * y2 - x2 * y1
        area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    area /= 2
    return (cx / (6 * area), cy / (6 * area))


def _distance_to_line(p: Point, a: Point, b: Point) -> float:
    (px, py), (ax, ay), (bx, by) = p, a, b
    return abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / math.hypot(bx - ax, by - ay)


def motif_anchor(vertices: list[Point]) -> Point:
    """Where the motif goes: the incentre of a triangle, else the centroid."""
    if len(vertices) == 3:
        a, b, c = vertices
        la, lb, lc = math.dist(b, c), math.dist(a, c), math.dist(a, b)
        total = la + lb + lc
        return (
            (la * a[0] + lb * b[0] + lc * c[0]) / total,
            (la * a[1] + lb * b[1] + lc * c[1]) / total,
        )
    return centroid(vertices)


def motif_polygon(vertices: list[Point]) -> list[Point]:
    """The F motif, scaled to fit inside the (convex) domain around its anchor."""
    anchor = motif_anchor(vertices)
    clearance = min(
        _distance_to_line(anchor, a, b) for a, b in zip(vertices, vertices[1:] + vertices[:1])
    )
    scale = MOTIF_FILL * clearance / _F_RADIUS
    return [(anchor[0] + scale * x, anchor[1] + scale * y) for x, y in F_SHAPE]


def fundamental_tile(
    group: WallpaperGroup,
) -> tuple[list[Point], list[tuple[int, int, str]], list[tuple[list[int], str]]]:
    """Vertices, edges and polygons of `group`'s fundamental tile.

    The domain's corners come first, so the group's identifications (which
    index them) stay valid; the motif's points follow.
    """
    n = len(group.vertices)
    motif = motif_polygon(group.vertices)
    vertices = list(group.vertices) + motif
    edges = [(i, (i + 1) % n, "domain_edge") for i in range(n)]
    polygons = [
        (list(range(n)), "domain"),
        (list(range(n, n + len(motif))), "motif"),
    ]
    return vertices, edges, polygons
