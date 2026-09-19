"""
Render the p31m tiling's "domain 2" fundamental quadrangle at a fixed shape
(x=0.5), both as an isolated tile and as the resulting periodic tiling.

The geometry (fundamental_domain, identifications) is copied from
examples/p31m_tiling/main.py's domain 2; unlike that example, here x is
fixed rather than animated, and there's no construction-order output.

Two decorations are available, selected with --decoration: "truncation"
(BASE_STEPS: base, truncation, omnitruncation) and "rectification"
(BASE_STEPS_ALT: base, rectification). build_steps() expands either
into a full step list, interleaving a transition_N step between each
consecutive pair of stages.

Each Step shares the same vertices and identifications as every other
step, but has its own edges and polygons, plus optionally its own raw
TikZ appended after the rendered pattern, inside the same tikzpicture
(extra_tikz_tile / extra_tikz_tiling), for one-off annotations that
don't fit the edges/polygons/identifications model (same mechanism as
examples/glue_and_split/main.py's Step.extra_tikz). decoration_tile.tex
/ decoration_tiling.tex each render every step of the selected
decoration(s) as its own tikzpicture, in order; output filenames are
suffixed with the decoration's name.
"""

import argparse
import math
from dataclasses import dataclass, replace
from pathlib import Path

import caleidoscope

OUTPUT_DIR = Path(__file__).parent / "output"

X = 0.5

# Scale factors (in TikZ units per unit of `fundamental_domain()` output), as in
# p31m_tiling: the isolated tile uses a larger scale than the full tiling.
TILE_SCALE = 10
TILING_SCALE = 2

# Custom colors for face6-face17 (defined below, in FACE_COLORS); face1-face5
# keep their original named xcolor colors. These are saturated rather than
# tinted like face1-face5's "blue!20" etc.: tinting 12 more hues down to
# "!20" (mostly white) would wash out the hue differences too far to tell
# them apart, both from each other and from face1-face5.
FACE_COLORS = {
    "face6color": "EB6A6A",
    "face7color": "EBC56A",
    "face8color": "B5EB6A",
    "face9color": "88EB6A",
    "face10color": "6AEBA6",
    "face11color": "6AEBD4",
    "face12color": "6AD4EB",
    "face13color": "6AA6EB",
    "face14color": "886AEB",
    "face15color": "B56AEB",
    "face16color": "EB6AC5",
    "face17color": "EB6A97",
}

ANNOTATION_STYLES = {
    "s0": "teal, ultra thin",
    "s1": "red, ultra thin",
    "s2": "black, thick",
    "s2old": "gray, thick",
    "face1": "draw=none, fill=blue!20",
    "face2": "draw=none, fill=purple!20",
    "face3": "draw=none, fill=orange!20",
    "face4": "draw=none, fill=green!20",
    "face5": "draw=none, fill=yellow!20",
    "face6": "draw=none, fill=face6color",
    "face7": "draw=none, fill=face7color",
    "face8": "draw=none, fill=face8color",
    "face9": "draw=none, fill=face9color",
    "face10": "draw=none, fill=face10color",
    "face11": "draw=none, fill=face11color",
    "face12": "draw=none, fill=face12color",
    "face13": "draw=none, fill=face13color",
    "face14": "draw=none, fill=face14color",
    "face15": "draw=none, fill=face15color",
    "face16": "draw=none, fill=face16color",
    "face17": "draw=none, fill=face17color",
}

IDENTIFICATIONS = [
    ((0, 3), (0, 3), False),
    ((0, 5), (0, 5), False),
    ((4, 3), (4, 5), True),
]

TILE_VIEW = {"center_x": 5, "center_y": 4, "width": 20, "height": 14}

# Third decoration: one triangle per entry, each a triple of point indices
# from `fundamental_domain`'s step1 (9 points) + step2 (13 points). Also used
# below to derive the "dual" edges connecting each triangle's barycenter to
# that of every triangle it shares an edge (two points) with.
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

# Index of the first triangle-barycenter point in `VERTICES`: step1 (9
# points) + step2 (13 points) come before them.
TRIANGLE_BARYCENTER_OFFSET = 22

TRIANGLE_BARYCENTER_EDGES = [
    (TRIANGLE_BARYCENTER_OFFSET + i, TRIANGLE_BARYCENTER_OFFSET + j, "s2")
    for i, tri_a in enumerate(TRIANGLE_INDICES)
    for j, tri_b in enumerate(TRIANGLE_INDICES)
    if i < j and len(set(tri_a) & set(tri_b)) == 2
]


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

BASE_STEP: Step = Step(
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
    )

BASE_STEPS: list[Step] = [
    BASE_STEP,
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
            # s0
            (6, 7, "s0"),
            (6, 18, "s0"),
            (6, 19, "s0"),
            (6, 20, "s0"),
            (5, 6, "s0"),
            (0, 15, "s0"),
            (0, 7, "s0"),
            (1, 15, "s0"),
            (1, 16, "s0"),
            (1, 19, "s0"),
            (21, 16, "s0"),
            (21, 18, "s0"),
            (21, 17, "s0"),
            (21, 3, "s0"),
            (4, 17, "s0"),
            (4, 20, "s0"),
            # s1
            (6, 9, "s1"),
            (6, 10, "s1"),
            (6, 11, "s1"),
            (6, 13, "s1"),
            (0, 9, "s1"),
            (1, 9, "s1"),
            (1, 10, "s1"),
            (21, 10, "s1"),
            (21, 11, "s1"),
            (21, 12, "s1"),
            (4, 12, "s1"),
            (4, 11, "s1"),
            (4, 13, "s1"),
        ],
        polygons=[
            ([0, 15, 9, 7], "face1"),
            ([9, 10, 11, 13, 5, 7], "face2"),
            ([13, 11, 12, 4], "face4"),
            ([3, 12, 11, 10, 16], "face3"),
            ([15, 9, 10, 16], "face5"),
        ],
    ),
    Step(
        label="omnitruncation",
        edges=TRIANGLE_BARYCENTER_EDGES
        + [
            (22, 46, "s2"),
            (34, 47, "s2"),
            (33, 48, "s2"),
            (23, 49, "s2"),
            (24, 50, "s2"),
            (26, 51, "s2"),
            (41, 52, "s2"),
            (28, 53, "s2"),
            (28, 54, "s2"),
            (31, 55, "s2"),
            (32, 56, "s2"),
            (33, 57, "s2"),
        ],
        # One polygon per original vertex used in TRIANGLE_INDICES: the
        # barycenters of its incident triangles (from TRIANGLE_BARYCENTER_EDGES
        # above), plus, for a vertex on the tile's outer boundary, the two
        # boundary/projection points that close its fan (and, at a domain
        # corner, the corner point itself).
        polygons=[
            ([0, 46, 22, 23, 49], "face1"),
            ([50, 24, 25, 27, 26, 51], "face5"),
            ([53, 28, 54, 3], "face15"),
            ([29, 30, 32, 56, 4, 55, 31], "face4"),
            ([5, 57, 33, 48], "face15"),
            ([48, 33, 40, 39, 38, 36, 37, 35, 34, 47], "face2"),
            ([47, 34, 22, 46], "face12"),
            ([23, 22, 34, 35, 25, 24], "face16"),
            ([27, 37, 36, 42, 41, 26], "face8"),
            ([38, 39, 30, 29, 43, 44], "face6"),
            ([45, 31, 55, 54, 28], "face17"),
            ([40, 33, 57, 56, 32], "face17"),
            ([49, 23, 24, 50], "face13"),
            ([51, 26, 41, 52], "face14"),
            ([43, 29, 31, 45], "face11"),
            ([36, 38, 44, 42], "face9"),
            ([25, 35, 37, 27], "face10"),
            ([39, 40, 32, 30], "face7"),
            ([52, 41, 42, 44, 43, 45, 28, 53], "face3"),
        ],
    ),
]

BASE_STEPS_ALT: list[Step] = [
    BASE_STEP,
    Step(
        label="rectification",
        edges=[
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
        ],
        polygons=[
            ([0,59, 7], "face1"),
            ([58, 5, 7], "face2"),
            ([4, 3, 58, 5], "face4"),
            ([3, 58, 60], "face3"),
            ([59, 2, 58, 7], "face5"),
        ],
    ),
]

DECORATIONS: dict[str, list[Step]] = {
    "truncation": BASE_STEPS,
    "rectification": BASE_STEPS_ALT,
}


def build_steps(base_steps: list[Step]) -> list[Step]:
    """Expand a decoration's base stages into a full step list, with a
    transition_N step interleaved between each consecutive pair: it
    shows the previous stage's s2 edges (as s2old) alongside the next
    stage's own edges."""
    steps = [base_steps[0]]
    for i in range(1, len(base_steps)):
        prev, curr = base_steps[i - 1], base_steps[i]
        steps.append(
            replace(
                curr,
                label=f"transition_{i}",
                edges=[(v1, v2, "s2old") for v1, v2, l in prev.edges if l == "s2"]
                + curr.edges,
            )
        )
        steps.append(curr)
    return steps


def bary_steps(steps: list[Step]) -> list[Step]:
    """Reduce a built step list's base and final-decoration steps to
    only their s2 edges, keeping the transition step in between, for
    the barycentric tiling export (decoration_tiling_bary)."""
    return (
        [replace(steps[0], edges=[e for e in steps[0].edges if e[2] == "s2"])]
        + steps[1:2]
        + [replace(steps[2], edges=[e for e in steps[2].edges if e[2] == "s2"])]
    )


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

# Just for debugging reasons during development
# EXTRA = "\n".join(
#    [
#        "\\node[circle,fill=white,font=\\tiny] at ({:.3f},{:.3f}) {{{}}};".format(
#            TILE_SCALE * vx, TILE_SCALE * vy, i
#        )
#        for i, (vx, vy) in enumerate(VERTICES)
#        if i > 21
#    ]
# )


def wrap_tikz_picture(tikz_content):
    """Wrap the TikZ content in a tikz picture environment."""
    return f"""\\begin{{tikzpicture}}
{tikz_content}\\end{{tikzpicture}}
"""


def wrap_standalone(content):
    """Wrap the TikZ content in a standalone document."""
    color_defs = "\n".join(
        f"\\definecolor{{{name}}}{{HTML}}{{{hex_code}}}"
        for name, hex_code in FACE_COLORS.items()
    )
    return f"""\\documentclass[tikz]{{standalone}}
{color_defs}
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
        rendered = (
            tiling.render(
                renderer,
                center_x=bc[0],
                center_y=bc[1],
                width=16,
                height=16,
                edge_filter=lambda edge, tile: False,
                polygon_filter=None,
            )
            + "\n"
            + tiling.render(
                renderer,
                center_x=bc[0],
                center_y=bc[1],
                width=16,
                height=16,
                edge_filter=lambda edge, tile: edge[2].startswith("s2"),
                polygon_filter=lambda polygon, tile: False,
            )
        )
        content += wrap_tikz_picture(rendered + step.extra_tikz_tiling)
    return content


def render_tiling_steps_bary(steps: list[Step]) -> str:
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
        rendered = (
            tiling.render(
                renderer,
                center_x=bc[0],
                center_y=bc[1],
                width=8,
                height=8,
                edge_filter=lambda edge, tile: True,
                polygon_filter=None,
            )
            + "\n"
            + tiling.render(
                renderer,
                center_x=bc[0],
                center_y=bc[1],
                width=8,
                height=8,
                edge_filter=lambda edge, tile: edge[2].startswith("s2"),
                polygon_filter=lambda polygon, tile: False,
            )
        )
        content += wrap_tikz_picture(rendered + step.extra_tikz_tiling)
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["tile", "tiling", "tiling_bary", "all"],
        default="all",
        help="which output(s) to generate (default: all)",
    )
    parser.add_argument(
        "--decoration",
        choices=["truncation", "rectification", "both"],
        default="truncation",
        help="which decoration(s) to render (default: truncation)",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    names = (
        ["truncation", "rectification"]
        if args.decoration == "both"
        else [args.decoration]
    )

    for name in names:
        steps = build_steps(DECORATIONS[name])
        suffix = f"_{name}"

        if args.mode in ("tile", "all"):
            path = OUTPUT_DIR / f"decoration_tile{suffix}.tex"
            path.write_text(wrap_standalone(render_tile_steps(steps)))
            print(f"Wrote {path}")

        if args.mode in ("tiling", "all"):
            path = OUTPUT_DIR / f"decoration_tiling{suffix}.tex"
            path.write_text(wrap_standalone(render_tiling_steps(steps)))
            print(f"Wrote {path}")

        if args.mode in ("tiling_bary", "all"):
            path = OUTPUT_DIR / f"decoration_tiling_bary{suffix}.tex"
            path.write_text(
                wrap_standalone(render_tiling_steps_bary(bary_steps(steps)))
            )
            print(f"Wrote {path}")


if __name__ == "__main__":
    main()
