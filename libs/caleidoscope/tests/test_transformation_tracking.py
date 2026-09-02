"""Tests that tiles correctly track their transformation and generator sequence."""

import math

import pytest

from caleidoscope import ConstructedPattern, Pattern, Transform2D
from caleidoscope.constructed_pattern import Tile


@pytest.fixture
def triangle_vertices() -> list[tuple[float, float]]:
    h = math.sqrt(3) / 2  # height of equilateral triangle with side 1
    return [
        (0.0, 0.0),  # bottom-left
        (1.0, 0.0),  # bottom-right
        (0.5, h),    # top
    ]


@pytest.fixture
def constructed(triangle_vertices: list[tuple[float, float]]) -> ConstructedPattern:
    """A triangle pattern tiled by reflecting across each of its edges."""
    vertices = triangle_vertices
    edges = [
        (0, 1, "bottom"),
        (1, 2, "right"),
        (2, 0, "left"),
    ]
    h = vertices[2][1]
    center = (0.5, h / 3)  # centroid of triangle
    tolerance = 0.01
    identifications = [
        ((0, 1), (1, 0), True),  # bottom edge reflection -> 180 rotation
        ((1, 2), (2, 1), True),  # right edge reflection -> 180 rotation
        ((2, 0), (0, 2), True),  # left edge reflection -> 180 rotation
    ]
    pattern = Pattern(vertices, edges, [], center, tolerance, identifications)
    return pattern.construct(center_x=center[0], center_y=center[1], width=4.0, height=4.0)


@pytest.fixture
def tiles(constructed: ConstructedPattern) -> list[Tile]:
    return constructed.get_tiles()


def _assert_transformation_matches_vertices(tile: Tile, original_vertices: list[tuple[float, float]]) -> None:
    for original, expected in zip(original_vertices, tile.vertices):
        transformed = tile.transformation.apply(original)
        assert transformed[0] == pytest.approx(expected[0], abs=1e-3)
        assert transformed[1] == pytest.approx(expected[1], abs=1e-3)


def test_fundamental_tile_has_empty_generator_sequence(tiles: list[Tile]) -> None:
    assert tiles[0].generator_sequence == ()


def test_fundamental_tile_has_identity_transformation(
    tiles: list[Tile], triangle_vertices: list[tuple[float, float]]
) -> None:
    _assert_transformation_matches_vertices(tiles[0], triangle_vertices)


def test_first_level_tiles_have_single_generator(
    tiles: list[Tile], triangle_vertices: list[tuple[float, float]]
) -> None:
    first_level = [t for t in tiles if len(t.generator_sequence) == 1]
    assert first_level
    for tile in first_level:
        _assert_transformation_matches_vertices(tile, triangle_vertices)


def test_second_level_tiles_have_two_generators(
    tiles: list[Tile], triangle_vertices: list[tuple[float, float]]
) -> None:
    # Whether any second-level tiles exist depends on the constructed region size;
    # when present, their transformation must still be consistent.
    second_level = [t for t in tiles if len(t.generator_sequence) == 2]
    for tile in second_level:
        _assert_transformation_matches_vertices(tile, triangle_vertices)


def test_all_tiles_have_well_formed_transformation_and_sequence(tiles: list[Tile]) -> None:
    for tile in tiles:
        assert isinstance(tile.transformation, Transform2D)
        assert isinstance(tile.generator_sequence, tuple)
        assert all(isinstance(g, int) for g in tile.generator_sequence)


def test_format_generator_sequence_for_fundamental_tile(tiles: list[Tile]) -> None:
    assert tiles[0].format_generator_sequence() == "identity"


def test_format_generator_sequence_for_first_level_tile(tiles: list[Tile]) -> None:
    first_level = next(t for t in tiles if len(t.generator_sequence) == 1)
    assert first_level.format_generator_sequence() == f"g{first_level.generator_sequence[0]}"


def test_format_generator_sequence_for_multi_level_tile(tiles: list[Tile]) -> None:
    multi_level = [t for t in tiles if len(t.generator_sequence) >= 2]
    if not multi_level:
        pytest.skip("no multi-level tiles generated for this region size")
    assert " ∘ " in multi_level[0].format_generator_sequence()
