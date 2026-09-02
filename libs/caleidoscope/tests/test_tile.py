"""Tests for the Tile dataclass: construction, polygon conversion, immutability."""

import dataclasses

import pytest

from caleidoscope import Transform2D
from caleidoscope.constructed_pattern import Tile


def _make_tile(polygons: list[tuple[list[int], str]] | None = None) -> Tile:
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    edges = [(0, 1, "a"), (1, 2, "b"), (2, 3, "a"), (3, 0, "b")]
    return Tile(vertices, edges, polygons or [], Transform2D(), ())


def test_vertices_and_edges_stored_as_tuples() -> None:
    tile = _make_tile()
    assert tile.vertices == ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    assert isinstance(tile.vertices, tuple)
    assert tile.edges == ((0, 1, "a"), (1, 2, "b"), (2, 3, "a"), (3, 0, "b"))
    assert isinstance(tile.edges, tuple)


def test_polygons_are_converted_to_nested_tuples() -> None:
    tile = _make_tile(polygons=[([0, 1, 2, 3], "face")])
    assert tile.polygons == (((0, 1, 2, 3), "face"),)
    assert isinstance(tile.polygons[0][0], tuple)


def test_multiple_polygons_preserve_order_and_annotation() -> None:
    tile = _make_tile(polygons=[([0, 1, 2], "tri1"), ([0, 2, 3], "tri2")])
    assert tile.polygons == (((0, 1, 2), "tri1"), ((0, 2, 3), "tri2"))


def test_tile_is_frozen() -> None:
    tile = _make_tile()
    with pytest.raises(dataclasses.FrozenInstanceError):
        tile.generator_sequence = (0,)
