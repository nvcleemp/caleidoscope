"""
Animate a p31m wallpaper-group tiling as its fundamental tile is deformed by
a shape parameter x, ranging over x_values.

Generates several LaTeX documents, each a sequence of standalone TikZ
pictures (one per frame): the isolated fundamental tile, and the resulting
periodic tiling, both animated over the shape parameter x; plus a
fixed-shape tiling built up one tile at a time in construction order.
"""

import argparse
import math
from pathlib import Path

import caleidoscope

OUTPUT_DIR = Path(__file__).parent / "output"

# Scale factors (in TikZ units per unit of `quadrangle()` output) used so the
# isolated-tile and isolated-quadrangle frames line up at the same physical
# size; the full periodic tiling uses a smaller scale to fit multiple tiles.
TILE_SCALE = 10
TILING_SCALE = 2

ANNOTATION_STYLES = {
    "s0": "teal, ultra thin",
    "s1": "red, ultra thin",
    "s2": "black, thick",
    "triangle": "draw=none, fill=blue!20",
    "quadrangle": "draw=none, fill=purple!20",
    "triangle2": "draw=none, fill=orange!20",
    "side": "gray, ultra thick",
    "gen1": "blue, ultra thick",
    "gen2": "purple, ultra thick",
    "gen3": "orange, ultra thick",
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


def wrap_beamer(content):
    """Wrap the TikZ content in a single-frame beamer document."""
    return f"""\\documentclass{{beamer}}
\\usepackage{{tikz}}
\\begin{{document}}
\\begin{{frame}}
{content}\\end{{frame}}
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


def render_quadrangle_frames(x_values) -> str:
    """Render each frame as the isolated base quadrangle, with the angle and
    side-length annotations used to construct it."""
    content = "\\usetikzlibrary{calc}\n\n"
    for x in x_values:
        p1, p2, p3, p4 = [
            (TILE_SCALE * vx, TILE_SCALE * vy) for vx, vy in quadrangle(x)[:4]
        ]

        # Angle (in degrees) of the ray P4->P2, used to place the 120° arc
        # and label at P4.
        angle_p4_p2 = math.degrees(math.atan2(p2[1] - p4[1], p2[0] - p4[0]))

        lines = [
            "  \\useasboundingbox (-4,-2) rectangle (14,8);",
            "  \\draw "
            + " -- ".join(f"({vx},{vy})" for vx, vy in (p1, p2, p4, p3))
            + " -- cycle;",
            "  \\draw (1,0) arc[start angle=0,end angle=60,radius=1];",
            "  \\node at (1.1,.7) {60°};",
            (
                f"  \\draw ($({p4[0]},{p4[1]}) + ({angle_p4_p2}:1) $) "
                f"arc[start angle={angle_p4_p2},end angle={angle_p4_p2 - 120},radius=1];"
            ),
            f"  \\node at ($({p4[0]},{p4[1]}) + ({angle_p4_p2 - 60}:1.3) $) {{120°}};",
            f"  \\node at ($({(p1[0] + p3[0]) / 2},{(p1[1] + p3[1]) / 2}) + (120:.2) $) {{$x$}};",
        ]
        content += wrap_tikz_picture("\n".join(lines) + "\n")
    return content


def render_quadrangle_with_chambers_frames(x_values, edges, polygons) -> str:
    """Render each frame as the isolated tile with polygon fills suppressed
    and each chamber labeled with its number at its barycenter."""
    chambers = [
        (0, 2, 4),
        (2, 4, 6),
        (2, 6, 9),
        (3, 6, 9),
        (3, 5, 6),
        (1, 7, 8),
        (3, 7, 8),
        (3, 5, 7),
    ]

    content = ""
    for x in x_values:
        vertices = [(TILE_SCALE * vx, TILE_SCALE * vy) for vx, vy in quadrangle(x)]
        chamber_labels = [
            (p + 1, barycenter([vertices[i] for i in chamber]))
            for p, chamber in enumerate(chambers)
        ]
        renderer = caleidoscope.TikzRenderer(ANNOTATION_STYLES)
        renderer.initialize(center_x=5, center_y=3, width=20, height=12)
        tile = caleidoscope.Tile(
            vertices,
            edges,
            polygons,
            caleidoscope.Transform2D(),
            (),
        )
        renderer.render_tile(tile, polygon_filter=lambda polygon, tile: False)
        tikz_commands = renderer.finalize()
        tikz_commands += "\n".join(
            f"\\node[draw=none] at ({x},{y}) {{${i}$}};" for i, (x, y) in chamber_labels
        )
        content += wrap_tikz_picture(tikz_commands + "\n")
    return content


def render_tile_frames(x_values, edges, polygons) -> str:
    """Render each frame as the isolated fundamental tile, unfolded."""
    content = ""
    for x in x_values:
        vertices = quadrangle(x)
        renderer = caleidoscope.TikzRenderer(ANNOTATION_STYLES)
        renderer.initialize(center_x=5, center_y=3, width=20, height=12)
        tile = caleidoscope.Tile(
            [(TILE_SCALE * vx, TILE_SCALE * vy) for vx, vy in vertices],
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
        vertices = [(TILING_SCALE * vx, TILING_SCALE * vy) for vx, vy in quadrangle(x)]
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


MAX_CONSTRUCTION_FRAMES = 20

# Each entry is (n, owner): show the first n tiles (in construction/BFS
# order), with `owner`'s generator edges highlighted to indicate it's the
# tile currently spawning children (or no highlight, if `owner` is None).
CONSTRUCTION_STEPS = [
    (1, None),
    (1, 1),
    (2, 1),
    (3, 1),
    (4, 1),
    # Children of 2
    (4, 2),
    (5, 2),
    (6, 2),
    # Children of 3
    (6, 3),
    (7, 3),
    (8, 3),
    # Children of 4
    (8, 4),
    (9, 4),
    (10, 4),
    # Children of 5
    (10, 5),
    (11, 5),
    (12, 5),
    # Children of 6
    (12, 6),
    (13, 6),
    (14, 6),
    # Children of 7
    (14, 7),
    (15, 7),
    # Children of 8
    (15, 8),
    (16, 8),
    (17, 8),
    # Children of 9
    (17, 9),
    (18, 9),
    # Children of 10
    (18, 10),
    (19, 10),
]


def render_tiling_construction_frames(edges, polygons, identifications) -> str:
    """Render each frame as the fixed-shape tiling with one more tile added,
    in construction (BFS) order, building up from the fundamental tile.

    Stops after MAX_CONSTRUCTION_FRAMES tiles, since the idea is already
    clear well before the tiling fills the full boundary."""
    x = 0.5
    vertices = [(TILING_SCALE * vx, TILING_SCALE * vy) for vx, vy in quadrangle(x)]
    bc = barycenter(vertices)
    tiling = caleidoscope.Pattern(
        vertices=vertices,
        edges=edges,
        polygons=polygons,
        center=bc,
        tolerance=0.1,
        identifications=identifications,
    )
    constructed = tiling.construct(center_x=bc[0], center_y=bc[1], width=12, height=12)
    tiles = constructed.get_tiles()[:MAX_CONSTRUCTION_FRAMES]

    content = ""
    for n, owner in CONSTRUCTION_STEPS:
        frame = caleidoscope.ConstructedPattern(tiles[:n], bc[0], bc[1], 12, 12)
        renderer = caleidoscope.TikzRenderer(ANNOTATION_STYLES)
        tikz_commands = (
            frame.render(
                renderer,
                edge_filter=lambda edge, tile: (
                    edge[2] != "s2" and not edge[2].startswith("side")
                ),
                polygon_filter=None,
            )
            + "\n"
            + frame.render(
                renderer,
                edge_filter=lambda edge, tile: edge[2] == "s2",
                polygon_filter=lambda polygon, tile: False,
            )
            + "\n"
            + frame.render(
                renderer,
                edge_filter=lambda edge, tile: edge[2] == "side",
                polygon_filter=lambda polygon, tile: False,
            )
            + "\n"
            + frame.render(
                renderer,
                edge_filter=lambda edge, tile: (
                    edge[2].startswith("gen") and owner is not None and tile == tiles[owner - 1]
                ),
                polygon_filter=lambda polygon, tile: False,
            )
        )
        labels = "\n".join(
            f"\\node[circle, draw=none, fill=white, minimum size=10pt, inner sep=1pt] "
            f"at ({barycenter([tile.vertices[p] for p in (2, 3, 4, 5)])[0]},{barycenter([tile.vertices[p] for p in (2, 3, 4, 5)])[1]}) "
            f"{{\\scriptsize {i}}};"
            for i, tile in enumerate(tiles[:n], start=1)
        )
        content += wrap_tikz_picture(tikz_commands + "\n" + labels + "\n")
    return content


def render_tiling_construction_beamer_frames(edges, polygons, identifications) -> str:
    """Render the same construction sequence as render_tiling_construction_frames,
    but as a single tikzpicture using beamer \\only<start-end> overlays instead
    of one standalone picture per step.

    Each tile's own geometry (fill, main edges, s2 edges, side boundary) is
    rendered once and wrapped in \\only<n-N> (N = total overlay count), so it
    appears at the overlay where CONSTRUCTION_STEPS first reaches that tile's
    count and then stays visible. Each generator highlight is rendered once
    per contiguous run of steps sharing the same owner and wrapped in
    \\only<start-end> for just that run. Draw order follows
    render_tiling_construction_frames: all tile geometry, then all
    highlights, then all labels, so the on-top/underneath relationships at
    every overlay match the per-step version exactly."""
    x = 0.5
    vertices = [(TILING_SCALE * vx, TILING_SCALE * vy) for vx, vy in quadrangle(x)]
    bc = barycenter(vertices)
    tiling = caleidoscope.Pattern(
        vertices=vertices,
        edges=edges,
        polygons=polygons,
        center=bc,
        tolerance=0.1,
        identifications=identifications,
    )
    constructed = tiling.construct(center_x=bc[0], center_y=bc[1], width=12, height=12)
    tiles = constructed.get_tiles()[:MAX_CONSTRUCTION_FRAMES]

    total_overlays = len(CONSTRUCTION_STEPS)
    max_tiles = max(n for n, _ in CONSTRUCTION_STEPS)

    # First overlay (1-indexed) at which each tile count is reached.
    introduced_at = {}
    for overlay, (n, _owner) in enumerate(CONSTRUCTION_STEPS, start=1):
        introduced_at.setdefault(n, overlay)

    # Contiguous (owner, start_overlay, end_overlay) runs, skipping the
    # owner-less step(s) that show a tile before it starts generating.
    owner_runs = []
    prev_overlay = None
    for overlay, (_n, owner) in enumerate(CONSTRUCTION_STEPS, start=1):
        if owner is None:
            continue
        if owner_runs and owner_runs[-1][0] == owner and prev_overlay == overlay - 1:
            owner_runs[-1] = (owner, owner_runs[-1][1], overlay)
        else:
            owner_runs.append((owner, overlay, overlay))
        prev_overlay = overlay

    frame = caleidoscope.ConstructedPattern(tiles[:max_tiles], bc[0], bc[1], 12, 12)
    renderer = caleidoscope.TikzRenderer(ANNOTATION_STYLES)

    def only(start, end, body):
        return f"\\only<{start}-{end}>{{\n{body}\n}}\n"

    geometry_blocks = []
    label_blocks = []
    for t in range(1, max_tiles + 1):
        tile = tiles[t - 1]
        body = (
            frame.render(
                renderer,
                edge_filter=lambda edge, rtile, tile=tile: (
                    edge[2] != "s2"
                    and not edge[2].startswith("side")
                    and rtile == tile
                ),
                polygon_filter=lambda polygon, rtile, tile=tile: rtile == tile,
            )
            + "\n"
            + frame.render(
                renderer,
                edge_filter=lambda edge, rtile, tile=tile: (
                    edge[2] == "s2" and rtile == tile
                ),
                polygon_filter=lambda polygon, rtile: False,
            )
            + "\n"
            + frame.render(
                renderer,
                edge_filter=lambda edge, rtile, tile=tile: (
                    edge[2] == "side" and rtile == tile
                ),
                polygon_filter=lambda polygon, rtile: False,
            )
        )
        geometry_blocks.append(only(introduced_at[t], total_overlays, body))

        label_x, label_y = barycenter([tile.vertices[p] for p in (2, 3, 4, 5)])
        label = (
            f"\\node[circle, draw=none, fill=white, minimum size=10pt, inner sep=1pt] "
            f"at ({label_x},{label_y}) {{\\scriptsize {t}}};"
        )
        label_blocks.append(only(introduced_at[t], total_overlays, label))

    highlight_blocks = []
    for owner, start, end in owner_runs:
        tile = tiles[owner - 1]
        body = frame.render(
            renderer,
            edge_filter=lambda edge, rtile, tile=tile: (
                edge[2].startswith("gen") and rtile == tile
            ),
            polygon_filter=lambda polygon, rtile: False,
        )
        highlight_blocks.append(only(start, end, body))

    content = "".join(geometry_blocks) + "".join(highlight_blocks) + "".join(label_blocks)
    return wrap_tikz_picture(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=[
            "tile",
            "tiling",
            "all",
            "quadrangle",
            "chambers",
            "construction",
            "construction_beamer",
        ],
        default="all",
        help="which output(s) to generate (default: all)",
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

    tile_boundary_edges = [
        (0, 1, "side"),
        (0, 2, "side"),
        (2, 3, "side"),
        (1, 3, "side"),
        (0, 1, "gen1"),
        (0, 2, "gen2"),
        (2, 3, "gen3"),
    ]

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.mode in ("tile", "all"):
        content = render_tile_frames(x_values, edges, polygons)
        path = OUTPUT_DIR / "p31m_tile.tex"
        path.write_text(wrap_standalone(content))
        print(f"Wrote {path}")

    if args.mode in ("tiling", "all"):
        content = render_tiling_frames(x_values, edges, polygons, identifications)
        path = OUTPUT_DIR / "p31m_tiling.tex"
        path.write_text(wrap_standalone(content))
        print(f"Wrote {path}")

    if args.mode in ("quadrangle", "all"):
        content = render_quadrangle_frames(x_values)
        path = OUTPUT_DIR / "p31m_quadrangle.tex"
        path.write_text(wrap_standalone(content))
        print(f"Wrote {path}")

    if args.mode in ("chambers", "all"):
        content = render_quadrangle_with_chambers_frames(x_values, edges, polygons)
        path = OUTPUT_DIR / "p31m_chambers.tex"
        path.write_text(wrap_standalone(content))
        print(f"Wrote {path}")

    if args.mode in ("construction", "all"):
        content = render_tiling_construction_frames(
            edges + tile_boundary_edges, polygons, identifications
        )
        path = OUTPUT_DIR / "p31m_tiling_construction.tex"
        path.write_text(wrap_standalone(content))
        print(f"Wrote {path}")

    if args.mode in ("construction_beamer", "all"):
        content = render_tiling_construction_beamer_frames(
            edges + tile_boundary_edges, polygons, identifications
        )
        path = OUTPUT_DIR / "p31m_tiling_construction_beamer.tex"
        path.write_text(wrap_beamer(content))
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
