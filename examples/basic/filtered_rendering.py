#!/usr/bin/env python3
"""
Example demonstrating the separation of pattern construction from rendering.

This example shows how to:
1. Construct a pattern once
2. Render it multiple times with different filters
3. Generate separate outputs for different edge annotations
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from caleidoscope import Pattern, SvgRenderer, TikzRenderer

OUTPUT_DIR = Path(__file__).parent / "output"


def create_checkerboard_pattern() -> Pattern:
    """
    Create a simple checkerboard pattern with two types of edges.

    The fundamental tile is a square with horizontal edges marked as "horizontal"
    and vertical edges marked as "vertical".
    """
    # Square vertices
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

    # Edges with annotations
    edges = [
        (0, 1, "horizontal"),  # bottom edge
        (1, 2, "vertical"),    # right edge
        (2, 3, "horizontal"),  # top edge
        (3, 0, "vertical"),    # left edge
    ]

    center = (0.5, 0.5)
    tolerance = 0.1

    # Edge identifications for tiling
    identifications = [
        ((3, 0), (1, 2), True),   # left to right
        ((0, 1), (2, 3), True),   # bottom to top
    ]

    return Pattern(vertices, edges, [], center, tolerance, identifications)


def wrap_tikz_picture(tikz_code: str, title: str = "") -> str:
    """Wrap TikZ code in a complete LaTeX document."""
    return f"""\\documentclass{{standalone}}
\\usepackage{{tikz}}
\\begin{{document}}
\\begin{{tikzpicture}}
{tikz_code}
\\end{{tikzpicture}}
\\end{{document}}
"""


def write_svg(element: ET.Element, path: Path) -> None:
    """Serialize an SVG element tree and write it to disk."""
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(element, encoding="unicode")
    )


def main():
    """Demonstrate the new functionality."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Constructing pattern...")
    pattern = create_checkerboard_pattern()

    # Construct the pattern once (this does the expensive computation)
    constructed = pattern.construct(width=6, height=6)
    print(f"Pattern constructed: {constructed.tile_count} tiles\n")

    # Now we can render it multiple times without reconstructing

    # 1. Render all edges with default styles
    print("1. Rendering all edges...")
    output_all = constructed.render(TikzRenderer())
    (OUTPUT_DIR / "all_edges.tex").write_text(wrap_tikz_picture(output_all, "All Edges"))
    print(f"   Saved to output/all_edges.tex ({output_all.count('draw')} edges)\n")
    svg_renderer_all = SvgRenderer({
        "horizontal": "stroke:black;stroke-width:0.1",
        "vertical": "stroke:black;stroke-width:0.1",
    })
    write_svg(constructed.render(svg_renderer_all), OUTPUT_DIR / "all_edges.svg")
    print("   Saved to output/all_edges.svg\n")

    # 2. Render only horizontal edges with red color
    print("2. Rendering horizontal edges only...")
    filter_horizontal = lambda edge, _: len(edge) == 3 and edge[2] == "horizontal"
    renderer_horizontal = TikzRenderer({"horizontal": "red, thick"})
    output_horizontal = constructed.render(renderer_horizontal, edge_filter=filter_horizontal)
    (OUTPUT_DIR / "horizontal.tex").write_text(wrap_tikz_picture(output_horizontal, "Horizontal Edges"))
    print(f"   Saved to output/horizontal.tex ({output_horizontal.count('draw')} edges)\n")
    svg_renderer_horizontal = SvgRenderer({"horizontal": "stroke:red;stroke-width:0.1"})
    write_svg(
        constructed.render(svg_renderer_horizontal, edge_filter=filter_horizontal),
        OUTPUT_DIR / "horizontal.svg",
    )
    print("   Saved to output/horizontal.svg\n")

    # 3. Render only vertical edges with blue color
    print("3. Rendering vertical edges only...")
    filter_vertical = lambda edge, _: len(edge) == 3 and edge[2] == "vertical"
    renderer_vertical = TikzRenderer({"vertical": "blue, thick"})
    output_vertical = constructed.render(renderer_vertical, edge_filter=filter_vertical)
    (OUTPUT_DIR / "vertical.tex").write_text(wrap_tikz_picture(output_vertical, "Vertical Edges"))
    print(f"   Saved to output/vertical.tex ({output_vertical.count('draw')} edges)\n")
    svg_renderer_vertical = SvgRenderer({"vertical": "stroke:blue;stroke-width:0.1"})
    write_svg(
        constructed.render(svg_renderer_vertical, edge_filter=filter_vertical),
        OUTPUT_DIR / "vertical.svg",
    )
    print("   Saved to output/vertical.svg\n")

    # 4. Render both with different colors in the same output
    print("4. Rendering with colored edges...")
    renderer_colored = TikzRenderer({
        "horizontal": "red, thick",
        "vertical": "blue, thick"
    })
    output_colored = constructed.render(renderer_colored)
    (OUTPUT_DIR / "colored.tex").write_text(wrap_tikz_picture(output_colored, "Colored Edges"))
    print(f"   Saved to output/colored.tex ({output_colored.count('draw')} edges)\n")
    svg_renderer_colored = SvgRenderer({
        "horizontal": "stroke:red;stroke-width:0.1",
        "vertical": "stroke:blue;stroke-width:0.1",
    })
    write_svg(constructed.render(svg_renderer_colored), OUTPUT_DIR / "colored.svg")
    print("   Saved to output/colored.svg\n")

    print("=" * 60)
    print("Benefits of the new approach:")
    print("  • Pattern constructed only ONCE (expensive)")
    print("  • Rendered MULTIPLE times (cheap)")
    print("  • Different filters for different outputs")
    print("  • No redundant computation")
    print("=" * 60)


if __name__ == "__main__":
    main()
