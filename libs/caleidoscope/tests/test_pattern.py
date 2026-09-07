"""Tests for Pattern-level behavior not already covered by
test_constructed_pattern.py and test_transformation_tracking.py:
generator caching, boundary handling, and the no-generators edge case."""

from caleidoscope import Pattern, Transform2D


def _square_pattern(identifications: list[tuple[tuple[int, int], tuple[int, int], bool]]) -> Pattern:
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    edges = [(0, 1, ""), (1, 2, ""), (2, 3, ""), (3, 0, "")]
    return Pattern(vertices, edges, [], (0.5, 0.5), 0.1, identifications)


def test_generators_are_lazily_computed() -> None:
    pattern = _square_pattern([((0, 3), (1, 2), True)])
    assert pattern._generators is None
    generators = pattern.generators
    assert pattern._generators is not None
    assert len(generators) == 1
    assert isinstance(generators[0], Transform2D)


def test_generators_are_cached_across_accesses() -> None:
    pattern = _square_pattern([((0, 3), (1, 2), True)])
    first = pattern.generators
    second = pattern.generators
    assert first is second


def test_no_identifications_yields_only_the_fundamental_tile() -> None:
    pattern = _square_pattern([])
    constructed = pattern.construct(width=10, height=10)
    assert constructed.tile_count == 1
    tile = constructed.get_tiles()[0]
    assert tile.generator_sequence == ()


def test_construct_excludes_tiles_outside_the_boundary() -> None:
    # A translation-only pattern with a large step: within a small region only
    # the fundamental tile fits, since the next tile's center falls outside it.
    pattern = _square_pattern([((0, 3), (1, 2), True)])  # translate by (1, 0)
    small = pattern.construct(center_x=0.5, center_y=0.5, width=1.5, height=1.5)
    large = pattern.construct(center_x=0.5, center_y=0.5, width=10, height=10)
    assert small.tile_count == 1
    assert large.tile_count > small.tile_count


class RecordingRenderer:
    def __init__(self) -> None:
        self.init_args: dict[str, float] | None = None

    def initialize(self, center_x=0, center_y=0, width=10, height=10, margin=1) -> None:
        self.init_args = {
            "center_x": center_x,
            "center_y": center_y,
            "width": width,
            "height": height,
            "margin": margin,
        }

    def render_tile(self, tile, edge_filter=None, polygon_filter=None) -> None:
        pass

    def finalize(self):
        return self.init_args


def test_construct_region_is_forwarded_to_render_boundary() -> None:
    pattern = _square_pattern([])
    renderer = RecordingRenderer()
    result = pattern.render(renderer, center_x=1.0, center_y=2.0, width=3.0, height=4.0)
    assert result == {"center_x": 1.0, "center_y": 2.0, "width": 3.0, "height": 4.0, "margin": 1}


def test_render_forwards_custom_margin_to_renderer() -> None:
    pattern = _square_pattern([])
    renderer = RecordingRenderer()
    result = pattern.render(renderer, width=3.0, height=4.0, margin=2.5)
    assert result["margin"] == 2.5
