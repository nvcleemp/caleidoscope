from groups import GROUPS
from main import render_png


def test_render_png_produces_full_size_image():
    image = render_png(GROUPS["p4g"])
    assert image.size == (800, 800)
    assert image.mode == "RGBA"
