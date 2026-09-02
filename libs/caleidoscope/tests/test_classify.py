"""Tests for Transform2D.classify()."""

import math

import pytest

from caleidoscope import Transform2D


def test_identity() -> None:
    t = Transform2D()  # Identity by default
    result = t.classify()
    assert result.type == "identity"
    assert result.parameters == {}


def test_translation() -> None:
    t = Transform2D.translate(5.0, 3.0)
    result = t.classify()
    assert result.type == "translation"
    assert result.parameters["vector"][0] == pytest.approx(5.0)
    assert result.parameters["vector"][1] == pytest.approx(3.0)


def test_rotation() -> None:
    angle = math.pi / 4  # 45 degrees
    t = Transform2D.rotate(angle, 2.0, 3.0)
    result = t.classify()
    assert result.type == "rotation"
    assert result.parameters["angle_rad"] == pytest.approx(angle)
    assert result.parameters["pivot"][0] == pytest.approx(2.0)
    assert result.parameters["pivot"][1] == pytest.approx(3.0)


def test_reflection() -> None:
    # Reflect across the x-axis
    t = Transform2D.reflect_x()
    result = t.classify()
    assert result.type == "reflection"
    assert "axis_point" in result.parameters
    assert "axis_direction" in result.parameters
    assert "line_equation" in result.parameters


def test_reflection_across_non_axis_aligned_line() -> None:
    # Reflection across the line y = x: swaps x and y.
    t = Transform2D([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    result = t.classify()
    assert result.type == "reflection"
    vx, vy = result.parameters["axis_direction"]
    # The axis direction must be parallel to (1, 1) (the line y = x): vx == vy.
    assert vx == pytest.approx(vy, abs=1e-6)


def test_uniform_scaling() -> None:
    scale_factor = 2.5
    t = Transform2D([[scale_factor, 0.0, 0.0],
                      [0.0, scale_factor, 0.0],
                      [0.0, 0.0, 1.0]])
    result = t.classify()
    assert result.type == "uniform_scaling"
    assert result.parameters["factor"] == pytest.approx(scale_factor)


def test_non_uniform_scaling() -> None:
    x_scale, y_scale = 2.0, 3.0
    t = Transform2D([[x_scale, 0.0, 0.0],
                      [0.0, y_scale, 0.0],
                      [0.0, 0.0, 1.0]])
    result = t.classify()
    assert result.type == "non_uniform_scaling"
    assert result.parameters["x_factor"] == pytest.approx(x_scale)
    assert result.parameters["y_factor"] == pytest.approx(y_scale)


def test_glide_reflection() -> None:
    # Glide reflection: reflection followed by translation
    reflect = Transform2D.reflect_x()
    translate = Transform2D.translate(2.0, 0.0)
    t = translate.compose(reflect)
    result = t.classify()
    assert result.type == "glide_reflection"
    assert "axis_point" in result.parameters
    assert "axis_direction" in result.parameters
    assert "glide_vector" in result.parameters
    assert "line_equation" in result.parameters


def test_complex_affine() -> None:
    # Shear transformation
    shear_factor = 0.5
    t = Transform2D([[1.0, shear_factor, 0.0],
                      [0.0, 1.0, 0.0],
                      [0.0, 0.0, 1.0]])
    result = t.classify()
    assert result.type == "complex_affine"
    assert "matrix" in result.parameters


def test_line_equation_holds_for_points_on_axis() -> None:
    # Reflection across x-axis
    t = Transform2D.reflect_x()
    result = t.classify()
    a, b, c = result.parameters["line_equation"]

    for x, y in [(0, 0), (1, 0), (5, 0), (-3, 0)]:
        value = a * x + b * y + c
        assert value == pytest.approx(0.0, abs=1e-6), f"Point ({x}, {y}) should be on the line"
