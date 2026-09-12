"""
Build up a wallpaper pattern from a square fundamental domain step by step:
starting from the bare square, each step adds edges that split it into more
polygons, and may restyle edges/polygons already present.

The square's four corners (vertices 1,2,3,4 in cyclic order, 0-indexed here
as 0,1,2,3) are glued by two orientation-preserving generators:
  - side 1,2 -> side 1,4
  - side 3,2 -> side 3,4
These identifications are fixed for every step; only the interior edges,
polygons, and styles change between steps.

Generates two LaTeX documents: a sequence of standalone TikZ pictures (one
per step, for `make videos`), and the same sequence as a single beamer frame
using `\\only<n>` overlays.
"""

import argparse
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

import caleidoscope

OUTPUT_DIR = Path(__file__).parent / "output"

VIEW = {
    "tile_center_x": 0.5,
    "tile_center_y": 0.5,
    "center_x": 2,
    "center_y": 2,
    "width": 6,
    "height": 6,
    "margin": -.1,
}

# Square corners: vertex 1,2,3,4 in cyclic order, 0-indexed. Add interior
# vertices here as steps need them; unused vertices in a given step are
# harmless since only edges and polygons are drawn.
VERTICES = [
    (0.0, 0.0),  # 1 (square)
    (1.0, 0.0),  # 2 (square)
    (1.0, 1.0),  # 3 (square)
    (0.0, 1.0),  # 4 (square)
    (0.9, 0.7),  # 5 (mark)
    (0.9, 0.9),  # 6 (mark)
    (0.8, 0.8),  # 7 (mark)
    (0.0, 0.5),  # 8 (split 1 endpoint)
    (0.5, 1.0),  # 9 (split 2 endpoint)
    (0.5, 0.25), # 10 (split 2 endpoint)
    (0.5, 0.0),  # 11 (midpoint edge 1)
]

# Generators: side 1,2 -> side 1,4 and side 3,2 -> side 3,4, both
# orientation-preserving. Fixed regardless of how VERTICES/edges/polygons
# grow across steps.
IDENTIFICATIONS_LIST = [
    [(e, e, False) for e in ((1, 2), (2, 3))] + [((0, 1), (0,3), True)],
    [(e, e, False) for e in ((0, 1), (1, 2), (2, 3), (3, 0))],
    [((0, 1), (0, 3), True), ((2, 1), (2, 3), True)]
]
IDENTIFICATIONS = IDENTIFICATIONS_LIST[0]

ANNOTATION_STYLES = {
    "side": "gray, thick",
    "square": "draw=none, fill=blue!20",
    "mark": "draw=blue, ultra thin",
    "tile1": "draw=none, fill=blue!20",
    "tile2": "draw=none, fill=yellow!20",
    "tile3": "draw=none, fill=teal!20",
    "cut": "draw=red, thick, densely dotted",
    "glue": "draw=red, thick, densely dotted",
}


@dataclass
class Step:
    """One frame of the construction: the edges/polygons visible at this
    point, plus any style overrides layered on top of ANNOTATION_STYLES.

    edge_filter/polygon_filter, if given, are passed straight through to
    Pattern.render (signature: (edge_or_polygon, tile) -> bool) so a step
    can e.g. hide edges/polygons of a given annotation without removing
    them from `edges`/`polygons`.

    extra_tikz, if given, is raw TikZ source appended after the rendered
    pattern, inside the same tikzpicture (e.g. for one-off annotations
    that don't fit the edges/polygons/identifications model)."""

    label: str
    edges: list[tuple[int, int, str]]
    polygons: list[tuple[list[int], str]]
    style_overrides: dict[str, str] = field(default_factory=dict)
    edge_filter: Callable[[tuple[int, int, str], caleidoscope.Tile], bool] | None = None
    polygon_filter: (
        Callable[[tuple[tuple[int, ...], str], caleidoscope.Tile], bool] | None
    ) = None
    extra_tikz: str = ""


BASE_STEPS: list[Step] = [
    Step(
        label="square",
        edges=[
            (0, 1, "side"),
            (1, 2, "side"),
            (2, 3, "side"),
            (3, 0, "side"),
            (4, 5, "mark"),
            (5, 6, "mark"),
            (1, 7, "cut"),
        ],
        polygons=[
            ([0, 1, 2, 3], "square"),
        ],
        edge_filter=lambda e, t: e[2] != "cut",
    ),
    Step(
        label="square",
        edges=[
            (0, 1, "side"),
            (1, 2, "side"),
            (2, 3, "side"),
            (3, 0, "side"),
            (4, 5, "mark"),
            (5, 6, "mark"),
            (1, 7, "side"),
            (8, 9, "cut"),
        ],
        polygons=[
            ([1, 2, 3, 7], "tile1"),
            ([0, 1, 7], "tile2"),
        ],
        edge_filter=lambda e, t: e[2] != "cut",
    ),
    Step(
        label="square",
        edges=[
            (0, 1, "side"),
            (1, 2, "side"),
            (2, 3, "side"),
            (3, 0, "side"),
            (4, 5, "mark"),
            (5, 6, "mark"),
            (1, 7, "side"),
            (8, 9, "side"),
            (10, 1, "side"),
        ],
        polygons=[
            ([1, 2, 8, 9], "tile1"),
            ([0, 1, 7], "tile2"),
            ([3, 7, 9, 8], "tile3"),
        ],
        edge_filter=lambda e, t: e[2] != "cut",
    ),
    Step(
        label="square",
        edges=[
            (1, 2, "side"),
            (2, 3, "side"),
            (3, 7, "side"),
            (4, 5, "mark"),
            (5, 6, "mark"),
            (1, 7, "side"),
            (8, 9, "side"),
            (10, 1, "side"),
        ],
        polygons=[
            ([1, 2, 8, 9], "tile1"),
            ([0, 1, 7], "tile2"),
            ([3, 7, 9, 8], "tile3"),
        ],
    ),
    Step(
        label="square",
        edges=[
            (1, 2, "side"),
            (2, 8, "side"),
            (3, 7, "side"),
            (4, 5, "mark"),
            (5, 6, "mark"),
            (1, 7, "side"),
            (8, 9, "side"),
            (10, 1, "side"),
        ],
        polygons=[
            ([1, 2, 8, 9], "tile1"),
            ([0, 1, 7], "tile2"),
            ([3, 7, 9, 8], "tile3"),
        ],
    ),
    Step(
        label="square",
        edges=[
            (3, 7, "side"),
            (4, 5, "mark"),
            (5, 6, "mark"),
            (1, 7, "side"),
            (8, 9, "side"),
            (10, 1, "side"),
        ],
        polygons=[
            ([1, 2, 8, 9], "tile1"),
            ([0, 1, 7], "tile2"),
            ([3, 7, 9, 8], "tile3"),
        ],
    ),
]

def is_tile_one(tile: caleidoscope.Tile) -> bool:
    xmax, xmin, ymax, ymin = (
        max(v[0] for v in tile.vertices),
        min(v[0] for v in tile.vertices),
        max(v[1] for v in tile.vertices),
        min(v[1] for v in tile.vertices),
    )
    return xmax == 1 and xmin == 0 and ymax == 1 and ymin == 0

STEPS = [
    BASE_STEPS[0],
    replace(BASE_STEPS[0], edge_filter=lambda e, t: e[2] != "cut" or is_tile_one(t)),
    BASE_STEPS[1],
    replace(BASE_STEPS[1], edge_filter=lambda e, t: e[2] != "cut" or is_tile_one(t)),
    BASE_STEPS[2],
    replace(BASE_STEPS[2], extra_tikz=f"  \\draw[{ANNOTATION_STYLES['glue']}] (0,0) circle [radius=0.2];\n"),
    BASE_STEPS[3],
    replace(BASE_STEPS[3], extra_tikz=f"  \\draw[{ANNOTATION_STYLES['glue']}] (.25,1) circle [radius=0.2];\n"),
    BASE_STEPS[4],
    replace(BASE_STEPS[4], extra_tikz=f"  \\draw[{ANNOTATION_STYLES['glue']}] (1,1) circle [radius=0.2];\n"),
    BASE_STEPS[5],
]


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


def render_step(step: Step) -> str:
    """Render a single step as one tikzpicture's worth of TikZ commands."""
    styles = {**ANNOTATION_STYLES, **step.style_overrides}
    renderer = caleidoscope.TikzRenderer(styles)
    tiling = caleidoscope.Pattern(
        vertices=VERTICES,
        edges=step.edges,
        polygons=step.polygons,
        center=(VIEW["tile_center_x"], VIEW["tile_center_y"]),
        tolerance=0.1,
        identifications=IDENTIFICATIONS,
    )
    rendered = tiling.render(
        renderer,
        center_x=VIEW["center_x"],
        center_y=VIEW["center_y"],
        width=VIEW["width"],
        height=VIEW["height"],
        margin=VIEW["margin"],
        edge_filter=step.edge_filter,
        polygon_filter=step.polygon_filter,
    )
    return rendered + step.extra_tikz


def render_steps(steps: list[Step]) -> str:
    """Render each step as its own tikzpicture, one after another."""
    content = ""
    for step in steps:
        content += wrap_tikz_picture(render_step(step))
    return content


def render_steps_beamer(steps: list[Step]) -> str:
    """Render each step as one overlay of a single tikzpicture: step n is
    visible only on overlay n (not cumulative, since a step may restyle or
    remove content from the previous one rather than only add to it)."""
    total_overlays = len(steps)
    blocks = []
    for n, step in enumerate(steps, start=1):
        body = render_step(step)
        blocks.append(f"\\only<{n}>{{\n{body}}}\n")
    return wrap_tikz_picture("".join(blocks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["steps", "steps_beamer", "all"],
        default="all",
        help="which output(s) to generate (default: all)",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    if args.mode in ("steps", "all"):
        content = render_steps(STEPS)
        path = OUTPUT_DIR / "glue_and_split.tex"
        path.write_text(wrap_standalone(content))
        print(f"Wrote {path}")

    if args.mode in ("steps_beamer", "all"):
        content = render_steps_beamer(STEPS)
        path = OUTPUT_DIR / "glue_and_split_beamer.tex"
        path.write_text(wrap_beamer(content))
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
