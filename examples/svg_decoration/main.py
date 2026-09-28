"""
Render the p31m tiling's "domain 2" fundamental quadrangle at a fixed shape
(x=0.5), with its finished "rectification" decoration applied, as a single
static picture using SvgRenderer.

The geometry (fundamental_domain, IDENTIFICATIONS) and the "rectification"
decoration's edges/polygons are ported from examples/decoration/main.py's
BASE_STEPS_ALT; unlike that example, there's no step sequence, no video
pipeline, and no CLI flags — this exists purely to demonstrate SvgRenderer
on a real (non-toy) tiling.
"""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import caleidoscope

OUTPUT_DIR = Path(__file__).parent / "output"

X = 0.5

# Scale factors (in SVG units per unit of `fundamental_domain()` output), as
# in decoration: the isolated tile uses a larger scale than the full tiling.
TILE_SCALE = 10
TILING_SCALE = 2

ANNOTATION_STYLES = {
    "s0": "stroke:teal;stroke-width:0.5",
    "s1": "stroke:red;stroke-width:0.5",
    "s2": "stroke:black;stroke-width:2",
    "face1": "fill:#0000ff;fill-opacity:0.2;stroke:none",
    "face2": "fill:#a000a0;fill-opacity:0.2;stroke:none",
    "face3": "fill:#ffa500;fill-opacity:0.2;stroke:none",
    "face4": "fill:#00a000;fill-opacity:0.2;stroke:none",
    "face5": "fill:#c0c000;fill-opacity:0.2;stroke:none",
}

IDENTIFICATIONS = [
    ((0, 3), (0, 3), False),
    ((0, 5), (0, 5), False),
    ((4, 3), (4, 5), True),
]

TILE_VIEW = {"center_x": 5, "center_y": 4, "width": 20, "height": 14}

# One triangle per entry, each a triple of point indices from
# `fundamental_domain`'s step1 (9 points) + step2 (13 points).
# fundamental_domain's step3 (triangle barycenters + boundary projections)
# is derived from this, and the rectification decoration below indexes into
# vertices that step3 in turn depends on — so this is needed even though
# rectification doesn't reference any triangle directly.
TRIANGLE_INDICES = [
    (0, 7, 9),
    (0, 9, 15),
    (1, 9, 15),
    (1, 9, 19),
    (1, 10, 16),
    (1, 10, 19),
    (3, 12, 21),
    (4, 11, 17),
    (4, 11, 20),
    (4, 12, 17),
    (4, 13, 20),
    (5, 6, 13),
    (6, 7, 9),
    (6, 9, 19),
    (6, 10, 18),
    (6, 10, 19),
    (6, 11, 18),
    (6, 11, 20),
    (6, 13, 20),
    (10, 16, 21),
    (10, 18, 21),
    (11, 17, 21),
    (11, 18, 21),
    (12, 17, 21),
]

# The finished "rectification" decoration (examples/decoration/main.py's
# BASE_STEPS_ALT[1]): edges/polygons over `VERTICES` below.
EDGES: list[tuple[int, int, str]] = [
    # s2
    (7, 58, "s2"),
    (7, 59, "s2"),
    (5, 58, "s2"),
    (3, 58, "s2"),
    (58, 60, "s2"),
    # s0
    (0, 59, "s0"),
    (1, 59, "s0"),
    (1, 60, "s0"),
    (1, 64, "s0"),
    (61, 60, "s0"),
    (61, 62, "s0"),
    (4, 62, "s0"),
    (4, 63, "s0"),
    (6, 63, "s0"),
    (6, 64, "s0"),
    # s1
    (6, 7, "s1"),
    (6, 58, "s1"),
    (6, 5, "s1"),
    (61, 3, "s1"),
    (61, 58, "s1"),
    (4, 3, "s1"),
    (4, 58, "s1"),
    (4, 5, "s1"),
    (1, 7, "s1"),
    (1, 18, "s1"),
    (0, 7, "s1"),
]

POLYGONS: list[tuple[list[int], str]] = [
    ([0, 59, 7], "face1"),
    ([58, 5, 7], "face2"),
    ([4, 3, 58, 5], "face4"),
    ([3, 58, 60], "face3"),
    ([59, 2, 58, 7], "face5"),
]


def barycenter(points):
    """Calculate the barycenter (centroid) of a list of points."""
    n = len(points)
    if n == 0:
        return (0, 0)
    x_sum = sum(p[0] for p in points)
    y_sum = sum(p[1] for p in points)
    return (x_sum / n, y_sum / n)


def between(p1, p2, percentage):
    """Calculate the point between p1 and p2 at the given percentage."""
    x = p1[0] + (p2[0] - p1[0]) * percentage
    y = p1[1] + (p2[1] - p1[1]) * percentage
    return (x, y)


def line_intersection(a1, a2, b1, b2):
    """Intersection of line a1-a2 with line b1-b2."""
    x1, y1 = a1
    x2, y2 = a2
    x3, y3 = b1
    x4, y4 = b2
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def perpendicular_projection(point, line_start, line_end):
    """Project a point onto a line defined by line_start and line_end."""
    x, y = point
    x1, y1 = line_start
    x2, y2 = line_end
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:
        return line_start
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    return (x1 + t * dx, y1 + t * dy)


def fundamental_domain(x: float):
    rad_60 = math.radians(60)

    # Fixed base vertices
    p0 = (0.0, 0.0)
    p5 = (1.0, 0.0)
    p3 = (math.cos(rad_60), math.sin(rad_60))

    p1 = (x * math.cos(rad_60), x * math.sin(rad_60))
    p7 = (x * math.cos(rad_60), 0)

    p2 = barycenter([p1, p3])
    p6 = barycenter([p7, p5])

    # p4 is placed such that the triangle P3-P5-P4 has angles 30° at P3 and P5, and 120° at P4.
    mid = barycenter([p3, p5])
    d = math.hypot(p5[0] - p3[0], p5[1] - p3[1])
    half_base = d / 2
    height = half_base * math.tan(math.radians(30))  # base_angle -> height
    # unit vector perpendicular to A->B
    ux, uy = -(p5[1] - p3[1]) / d, (p5[0] - p3[0]) / d  # pick sign for correct side
    p4 = (mid[0] + height * ux, mid[1] + height * uy)

    # p8 is placed at the intersection of p2p6 and p1p4
    p8 = line_intersection(p2, p6, p1, p4)

    step1 = [p0, p1, p2, p3, p4, p5, p6, p7, p8]

    # First decoration:

    p9 = between(p1, p7, 0.5)
    p10 = between(p1, p4, 0.25)
    p11 = between(p1, p4, 0.6)
    p12 = between(p3, p4, 0.5)
    p13 = between(p4, p5, 0.5)

    p14 = line_intersection(p9, p10, p1, p6)
    p15 = perpendicular_projection(p9, p0, p3)
    p16 = perpendicular_projection(p10, p0, p3)

    # Second decoration: midpoints of existing truncation edges.
    p17 = between(p11, p12, 0.5)
    p18 = between(p10, p11, 0.5)
    p19 = between(p10, p9, 0.5)
    p20 = between(p11, p13, 0.5)
    p21 = between(p16, p3, 0.5)

    step2 = [p9, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20, p21]

    # Third decoration: one point per entry in TRIANGLE_INDICES, at that
    # triangle's barycenter.
    step1_and_2 = step1 + step2
    step3 = [
        barycenter([step1_and_2[i] for i in triangle]) for triangle in TRIANGLE_INDICES
    ]
    p46 = perpendicular_projection(step3[22 - 22], p0, p5)
    p47 = perpendicular_projection(step3[34 - 22], p0, p5)
    p48 = perpendicular_projection(step3[33 - 22], p0, p5)
    p49 = perpendicular_projection(step3[23 - 22], p0, p3)
    p50 = perpendicular_projection(step3[24 - 22], p0, p3)
    p51 = perpendicular_projection(step3[26 - 22], p0, p3)
    p52 = perpendicular_projection(step3[41 - 22], p0, p3)
    p53 = perpendicular_projection(step3[28 - 22], p0, p3)
    p54 = perpendicular_projection(step3[28 - 22], p4, p3)
    p55 = between(p12, p4, 0.4)
    p56 = between(p13, p4, 0.4)
    p57 = perpendicular_projection(step3[33 - 22], p4, p5)
    step3 += [p46, p47, p48, p49, p50, p51, p52, p53, p54, p55, p56, p57]

    # Alternative second decoration: rectification
    p58 = between(p1, p4, 0.5)
    p59 = perpendicular_projection(p7, p0, p3)
    p60 = perpendicular_projection(p58, p0, p3)
    p61 = between(p60, p3, 0.5)
    p62 = between(p3, p58, 0.5)
    p63 = between(p5, p58, 0.5)
    p64 = between(p7, p58, 0.5)

    step2_alt = [p58, p59, p60, p61, p62, p63, p64]

    return step1_and_2 + step3 + step2_alt


VERTICES = fundamental_domain(X)


def write_svg(element: ET.Element, path: Path) -> None:
    """Serialize an SVG element tree and write it to disk."""
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(element, encoding="unicode")
    )


def render_tile() -> ET.Element:
    """Render the isolated fundamental tile, unfolded."""
    renderer = caleidoscope.SvgRenderer(ANNOTATION_STYLES)
    renderer.initialize(**TILE_VIEW)
    tile = caleidoscope.Tile(
        [(TILE_SCALE * vx, TILE_SCALE * vy) for vx, vy in VERTICES],
        EDGES,
        POLYGONS,
        caleidoscope.Transform2D(),
        (),
    )
    renderer.render_tile(tile)
    return renderer.finalize()


def render_tiling() -> ET.Element:
    """Render the full periodic tiling.

    Two passes, not one: this draws every tile's polygon before any tile's
    s2 edge, so s2 edges stay on top even where they sit on a shared
    boundary with a neighboring tile's fill. A single combined pass would
    interleave per tile (polygon, edges) and let a later tile's fill cover
    an earlier tile's edge (same reasoning as
    examples/decoration/main.py's render_tiling_steps).

    Unlike that TikZ version, which concatenates two rendered strings, this
    appends the second pass's elements directly onto the first pass's root
    Element — SvgRenderer.finalize() returns a live tree specifically so
    this kind of extension doesn't need string manipulation.
    """
    vertices = [(TILING_SCALE * vx, TILING_SCALE * vy) for vx, vy in VERTICES]
    bc = barycenter(vertices)
    pattern = caleidoscope.Pattern(
        vertices=vertices,
        edges=EDGES,
        polygons=POLYGONS,
        center=bc,
        tolerance=0.1,
        identifications=IDENTIFICATIONS,
    )
    constructed = pattern.construct(center_x=bc[0], center_y=bc[1], width=16, height=16)

    fills_root = constructed.render(
        caleidoscope.SvgRenderer(ANNOTATION_STYLES),
        edge_filter=lambda edge, tile: False,
        polygon_filter=None,
    )
    edges_root = constructed.render(
        caleidoscope.SvgRenderer(ANNOTATION_STYLES),
        edge_filter=lambda edge, tile: edge[2].startswith("s2"),
        polygon_filter=lambda polygon, tile: False,
    )
    for child in list(edges_root):
        fills_root.append(child)
    return fills_root


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    tile_path = OUTPUT_DIR / "svg_decoration_tile.svg"
    write_svg(render_tile(), tile_path)
    print(f"Wrote {tile_path}")

    tiling_path = OUTPUT_DIR / "svg_decoration_tiling.svg"
    write_svg(render_tiling(), tiling_path)
    print(f"Wrote {tiling_path}")


if __name__ == "__main__":
    main()
