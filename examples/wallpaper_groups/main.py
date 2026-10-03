"""
Render one annotated PNG per wallpaper group: an F motif in every
fundamental domain (mirror-image copies in a second colour), one domain
highlighted, and the group's mirrors, glide axes and rotation centres.
"""

import argparse
from pathlib import Path

from PIL import Image

import caleidoscope
from construction import construct_tiles, view_for
from groups import GROUPS, WallpaperGroup
from symmetry import derive, to_tiles

OUTPUT_DIR = Path(__file__).parent / "output"

SCALE = 100
MARKER_SIZE = 0.12

PNG_STYLES = {
    "domain": "fill:#ffd54f;stroke:none",
    "domain_edge": "stroke:#e0e0e0;stroke-width:0.01",
    "motif": "fill:#1e88e5;stroke:none",
    "motif_mirrored": "fill:#e53935;stroke:none",
    "glide": "stroke:#616161;stroke-width:0.015",
    "mirror": "stroke:#000000;stroke-width:0.04",
    "rot2": "fill:#000000;stroke:none",
    "rot3": "fill:#000000;stroke:none",
    "rot4": "fill:#000000;stroke:none",
    "rot6": "fill:#000000;stroke:none",
}


def render_png(group: WallpaperGroup) -> Image.Image:
    """The annotated tiling of `group`, on a white background."""
    view = view_for(group)
    tiles = construct_tiles(group)
    elements = derive([tile.transformation for tile in tiles], view)
    scene = caleidoscope.ConstructedPattern(
        tiles + to_tiles(elements, view, MARKER_SIZE),
        view.center_x,
        view.center_y,
        view.width,
        view.height,
    )
    image = scene.render(
        caleidoscope.PngRenderer(PNG_STYLES, scale=SCALE),
        # Only the fundamental tile itself shows its domain highlighted.
        polygon_filter=lambda polygon, tile: polygon[1] != "domain" or not tile.generator_sequence,
        margin=0,
    )
    background = Image.new("RGBA", image.size, "white")
    return Image.alpha_composite(background, image)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=[*GROUPS, "all"], default="all")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    names = list(GROUPS) if args.group == "all" else [args.group]
    for name in names:
        path = OUTPUT_DIR / f"{name}.png"
        render_png(GROUPS[name]).save(path)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
