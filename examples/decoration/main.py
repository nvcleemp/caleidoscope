"""
Render the p31m tiling's "domain 2" fundamental quadrangle at a fixed shape
(x=0.5), both as an isolated tile and as the resulting periodic tiling.

The geometry (fundamental_domain, identifications) is copied from
examples/p31m_tiling/main.py's domain 2; unlike that example, here x is
fixed rather than animated, and there's no construction-order output.

Each Step in STEPS is a decoration: it shares the same vertices and
identifications as every other step, but has its own edges and polygons,
plus optionally its own raw TikZ appended after the rendered pattern,
inside the same tikzpicture (extra_tikz_tile / extra_tikz_tiling), for
one-off annotations that don't fit the edges/polygons/identifications
model (same mechanism as examples/glue_and_split/main.py's
Step.extra_tikz). decoration_tile.tex / decoration_tiling.tex each render
every step as its own tikzpicture, in order.
"""

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import caleidoscope

OUTPUT_DIR = Path(__file__).parent / "output"

X = 0.5

# Scale factors (in TikZ units per unit of `fundamental_domain()` output), as in
# p31m_tiling: the isolated tile uses a larger scale than the full tiling.
TILE_SCALE = 10
TILING_SCALE = 2

ANNOTATION_STYLES = {
    "s0": "teal, ultra thin",
    "s1": "red, ultra thin",
    "s2": "black, thick",
    "face1": "draw=none, fill=blue!20",
    "face2": "draw=none, fill=purple!20",
    "face3": "draw=none, fill=orange!20",
    "face4": "draw=none, fill=green!20",
    "face5": "draw=none, fill=yellow!20",
}

IDENTIFICATIONS = [
    ((0, 3), (0, 3), False),
    ((0, 5), (0, 5), False),
    ((4, 3), (4, 5), True),
]

TILE_VIEW = {"center_x": 5, "center_y": 4, "width": 20, "height": 14}


@dataclass
class Step:
    """One decoration: shares VERTICES and IDENTIFICATIONS with every other
    step, but has its own edges/polygons, plus optional raw TikZ appended
    after the rendered pattern (inside the same tikzpicture) for
    annotations that don't fit the edges/polygons model."""

    label: str
    edges: list[tuple[int, int, str]]
    polygons: list[tuple[list[int], str]]
    extra_tikz_tile: str = ""
    extra_tikz_tiling: str = ""


STEPS: list[Step] = [
    Step(
        label="base",
        edges=[
            # s0
            (0, 7, "s0"),  # A
            (6, 7, "s0"),  # B
            (5, 6, "s0"),  # E
            (2, 3, "s0"),  # H
            (2, 8, "s0"),  # FG
            (6, 8, "s0"),  # CD
            # s1
            (0, 1, "s1"),  # A
            (1, 2, "s1"),  # F
            (2, 4, "s1"),  # GH
            (1, 6, "s1"),  # BC
            (4, 6, "s1"),  # DE
            # s2
            (3, 4, "s2"),  # H
            (4, 5, "s2"),  # E
            (1, 7, "s2"),  # AB
            (1, 8, "s2"),  # FC
            (4, 8, "s2"),  # GD
        ],
        polygons=[
            ([0, 1, 7], "face1"),
            ([1, 4, 5, 7], "face2"),
            ([1, 3, 4], "face3"),
        ],
    ),
    Step(
        label="truncation",
        edges=[
            # s2
            (15, 9, "s2"), 
            (7, 9, "s2"),  
            (9, 10, "s2"), 
            (10, 16, "s2"), 
            (10, 11, "s2"), 
            (5, 13, "s2"),
            (13, 11, "s2"),
            (11, 12, "s2"),
            (12, 3, "s2"),
        ],
        polygons=[
            ([0, 15, 9, 7], "face1"),
            ([9, 10, 11, 13, 5, 7], "face2"),
            ([13, 11, 12, 4], "face3"),
            ([3, 12, 11, 10, 16], "face4"),
            ([15, 9, 10, 16], "face5"),
        ],
    ),
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
    """Calculate the point between p1 and p2 at the given percentage.

    Args:
        p1: The first point (x, y).
        p2: The second point (x, y).
        percentage: A float between 0 and 1 indicating the relative position.

    Returns:
        The interpolated point (x, y).
    """
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

    # First decoration:

    p9 = between(p1, p7, 0.5)
    p10 = between(p1, p4, 0.25)
    p11 = between(p1, p4, 0.6)
    p12 = between(p3, p4, 0.5)
    p13 = between(p4, p5, 0.5)

    p14 = line_intersection(p9, p10, p1, p6)
    p15 = perpendicular_projection(p9, p0, p3)
    p16 = perpendicular_projection(p10, p0, p3)
    p17 = line_intersection(p14, p13, p4, p6)
    p18 = line_intersection(p4, p16, p12, p14)

    return [
        p0, p1, p2, p3, p4, p5, p6, p7, p8,
        p9, p10, p11, p12, p13, p14, p15, p16, p17, p18
    ]


VERTICES = fundamental_domain(X)


def wrap_tikz_picture(tikz_content):
    """Wrap the TikZ content in a tikz picture environment."""
    return f"""\\begin{{tikzpicture}}
{tikz_content}\\end{{tikzpicture}}
"""


def wrap_standalone(content):
    """Wrap the TikZ content in a standalone document."""
    return f"""\\documentclass[tikz]{{standalone}}
\\begin{{document}}
{content}
\\end{{document}}
"""


def render_tile_steps(steps: list[Step]) -> str:
    """Render each step as its own tikzpicture: the isolated fundamental
    tile, unfolded, using that step's edges/polygons."""
    content = ""
    for step in steps:
        renderer = caleidoscope.TikzRenderer(ANNOTATION_STYLES)
        renderer.initialize(**TILE_VIEW)
        tile = caleidoscope.Tile(
            [(TILE_SCALE * vx, TILE_SCALE * vy) for vx, vy in VERTICES],
            step.edges,
            step.polygons,
            caleidoscope.Transform2D(),
            (),
        )
        renderer.render_tile(tile)
        content += wrap_tikz_picture(renderer.finalize() + step.extra_tikz_tile)
    return content


def render_tiling_steps(steps: list[Step]) -> str:
    """Render each step as its own tikzpicture: the full periodic tiling
    using that step's edges/polygons."""
    content = ""
    for step in steps:
        vertices = [(TILING_SCALE * vx, TILING_SCALE * vy) for vx, vy in VERTICES]
        bc = barycenter(vertices)
        renderer = caleidoscope.TikzRenderer(ANNOTATION_STYLES)
        tiling = caleidoscope.Pattern(
            vertices=vertices,
            edges=step.edges,
            polygons=step.polygons,
            center=bc,
            tolerance=0.1,
            identifications=IDENTIFICATIONS,
        )
        # Two passes, not one: this draws every tile's polygon before any
        # tile's s2 edge, so s2 edges stay on top even where they sit on a
        # shared boundary with a neighboring tile's fill. A single combined
        # pass would interleave per tile (polygon, edges) and let a later
        # tile's fill cover an earlier tile's edge.
        rendered = tiling.render(
            renderer,
            center_x=bc[0],
            center_y=bc[1],
            width=16,
            height=16,
            edge_filter=lambda edge, tile: False,
            polygon_filter=None,
        ) + "\n" + tiling.render(
            renderer,
            center_x=bc[0],
            center_y=bc[1],
            width=16,
            height=16,
            edge_filter=lambda edge, tile: edge[2] == "s2",
            polygon_filter=lambda polygon, tile: False,
        )
        content += wrap_tikz_picture(rendered + step.extra_tikz_tiling)
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["tile", "tiling", "all"],
        default="all",
        help="which output(s) to generate (default: all)",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.mode in ("tile", "all"):
        path = OUTPUT_DIR / "decoration_tile.tex"
        path.write_text(wrap_standalone(render_tile_steps(STEPS)))
        print(f"Wrote {path}")

    if args.mode in ("tiling", "all"):
        path = OUTPUT_DIR / "decoration_tiling.tex"
        path.write_text(wrap_standalone(render_tiling_steps(STEPS)))
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
