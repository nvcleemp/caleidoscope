"""
Animate a p31m wallpaper-group tiling as its fundamental tile is deformed by
a shape parameter x, ranging over x_values.

Generates two LaTeX documents, each a sequence of standalone TikZ pictures
(one per frame): the isolated fundamental tile, and the resulting periodic
tiling.
"""

import argparse
import math
from pathlib import Path

import caleidoscope

OUTPUT_DIR = Path(__file__).parent / "output"

ANNOTATION_STYLES = {
    "s0": "green, ultra thin",
    "s1": "red, ultra thin",
    "s2": "black, thick",
    "triangle": "draw=none, fill=blue!20",
    "quadrangle": "draw=none, fill=purple!20",
    "triangle2": "draw=none, fill=orange!20",
}


def barycenter(points):
    """Calculate the barycenter (centroid) of a list of points."""
    n = len(points)
    if n == 0:
        return (0, 0)
    x_sum = sum(p[0] for p in points)
    y_sum = sum(p[1] for p in points)
    return (x_sum / n, y_sum / n)


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


def quadrangle(x: float):
    # Fixed base vertices
    p1 = (0.0, 0.0)
    p2 = (1.0, 0.0)

    # Vertex P3 (Top-left, at distance x and angle 60° from P1)
    rad_60 = math.radians(60)
    p3 = (x * math.cos(rad_60), x * math.sin(rad_60))

    # Vector from P2 to P3
    v_x = p3[0] - p2[0]
    v_y = p3[1] - p2[1]
    dist_p2_p3 = math.hypot(v_x, v_y)

    # Angle of segment P3->P2 relative to horizontal
    angle_p3_p2 = math.atan2(-v_y, -v_x)

    # Triangle P3-P2-P4 has a 30° angle at P3 (between P3->P2 and P3->P4) and
    # a 30° angle at P2 (between P2->P3 and P2->P4), so it's isosceles with
    # angle 120° at P4. By the law of sines, |P3-P4| / sin(30°) = |P3-P2| / sin(120°).
    dist_p3_p4 = dist_p2_p3 * math.sin(math.radians(30)) / math.sin(math.radians(120))

    angle_p3_p4 = angle_p3_p2 + math.radians(30)

    # Vertex P4 (Top-right)
    p4 = (
        p3[0] + dist_p3_p4 * math.cos(angle_p3_p4),
        p3[1] + dist_p3_p4 * math.sin(angle_p3_p4),
    )

    p5 = (x * math.cos(rad_60), 0)
    p6 = (p3[0] + dist_p3_p4 * math.cos(angle_p3_p4), 0)

    p7 = barycenter([p5, p6])
    p8 = barycenter([p6, p2])

    p9 = barycenter([p2, p4])
    p10 = barycenter([p3, p4])

    return [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]


def render_tile_frames(x_values, edges, polygons) -> str:
    """Render each frame as the isolated fundamental tile, unfolded."""
    content = ""
    for x in x_values:
        vertices = quadrangle(x)
        renderer = caleidoscope.TikzRenderer(ANNOTATION_STYLES)
        renderer.initialize(center_x=5, center_y=0, width=20, height=18)
        tile = caleidoscope.Tile(
            [(10 * vx, 10 * vy) for vx, vy in vertices],
            edges,
            polygons,
            caleidoscope.Transform2D(),
            (),
        )
        renderer.render_tile(tile)
        content += wrap_tikz_picture(renderer.finalize())
    return content


def render_tiling_frames(x_values, edges, polygons, identifications) -> str:
    """Render each frame as the full periodic tiling."""
    content = ""
    for x in x_values:
        vertices = [(2 * vx, 2 * vy) for vx, vy in quadrangle(x)]
        bc = barycenter(vertices)
        renderer = caleidoscope.TikzRenderer(ANNOTATION_STYLES)
        tiling = caleidoscope.Pattern(
            vertices=vertices,
            edges=edges,
            polygons=polygons,
            center=bc,
            tolerance=0.1,
            identifications=identifications,
        )
        content += wrap_tikz_picture(
            tiling.render(
                renderer,
                center_x=bc[0],
                center_y=bc[1],
                width=16,
                height=16,
                edge_filter=lambda edge, tile: edge[2] != "s2",
                polygon_filter=None,
            )
            + "\n"
            + tiling.render(
                renderer,
                center_x=bc[0],
                center_y=bc[1],
                width=16,
                height=16,
                edge_filter=lambda edge, tile: edge[2] == "s2",
                polygon_filter=lambda polygon, tile: False,
            )
        )
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["tile", "tiling", "both"],
        default="both",
        help="which output(s) to generate (default: both)",
    )
    args = parser.parse_args()

    x_range = [0.2, 0.8]
    x_count = 50
    x_values = [
        x_range[0] + i * (x_range[1] - x_range[0]) / (x_count - 1)
        for i in range(x_count)
    ]

    edges = [
        (0, 4, "s0"),
        (4, 6, "s0"),
        (6, 5, "s0"),
        (5, 7, "s0"),
        (7, 1, "s1"),
        (0, 2, "s1"),
        (1, 8, "s2"),
        (8, 3, "s2"),
        (2, 9, "s2"),
        (9, 3, "s2"),
        (4, 2, "s2"),
        (5, 3, "s2"),
        (2, 6, "s1"),
        (6, 9, "s0"),
        (3, 6, "s1"),
        (3, 7, "s1"),
        (7, 8, "s0"),
    ]

    polygons = [
        ([0, 4, 2], "triangle"),
        ([4, 2, 3, 5], "quadrangle"),
        ([5, 3, 1], "triangle2"),
    ]

    identifications = [
        ((0, 1), (0, 1), False),
        ((0, 2), (0, 2), False),
        ((3, 1), (3, 2), True),
    ]

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.mode in ("tile", "both"):
        content = render_tile_frames(x_values, edges, polygons)
        path = OUTPUT_DIR / "p31m_tile.tex"
        path.write_text(wrap_standalone(content))
        print(f"Wrote {path}")

    if args.mode in ("tiling", "both"):
        content = render_tiling_frames(x_values, edges, polygons, identifications)
        path = OUTPUT_DIR / "p31m_tiling.tex"
        path.write_text(wrap_standalone(content))
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
