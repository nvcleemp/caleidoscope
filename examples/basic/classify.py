#!/usr/bin/env python3
"""
Example usage of the classify() method for machine-readable transformation classification.
"""

import math

from caleidoscope import Transform2D


def example_basic_usage():
    """Demonstrate basic usage of classify()."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Create a rotation transformation
    t = Transform2D.rotate(math.pi / 3, 5, 5)  # 60 degrees around (5, 5)

    # Get machine-readable classification
    classification = t.classify()

    print(f"Type: {classification.type}")
    print(f"Angle (radians): {classification.parameters['angle_rad']:.6f}")
    print(f"Angle (degrees): {math.degrees(classification.parameters['angle_rad']):.2f}")
    print(f"Pivot: {classification.parameters['pivot']}")
    print()

    # Compare with human-readable version
    print("Human-readable version:")
    print(f"  {t.identify()}")
    print()


def example_reflection_axis():
    """Demonstrate axis representation for reflections."""
    print("=" * 60)
    print("Example 2: Reflection Axis Information")
    print("=" * 60)

    # Create a reflection
    t = Transform2D.reflect_x()
    classification = t.classify()

    print(f"Type: {classification.type}")
    print(f"Axis point: {classification.parameters['axis_point']}")
    print(f"Axis direction: {classification.parameters['axis_direction']}")

    # Get line equation
    a, b, c = classification.parameters['line_equation']
    print(f"Line equation: {a:.4f}*x + {b:.4f}*y + {c:.4f} = 0")
    print()

    # Verify a point on the line
    px, py = classification.parameters['axis_point']
    result = a * px + b * py + c
    print(f"Verification: Point ({px}, {py}) on line gives: {result:.10f}")
    print()


def example_programmatic_handling():
    """Demonstrate programmatic handling of different transformation types."""
    print("=" * 60)
    print("Example 3: Programmatic Handling")
    print("=" * 60)

    transformations = [
        Transform2D(),  # Identity
        Transform2D.translate(3, 4),  # Translation
        Transform2D.rotate(math.pi / 4),  # Rotation
        Transform2D([[2.0, 0, 0], [0, 3.0, 0], [0, 0, 1]]),  # Non-uniform scaling
    ]

    for i, t in enumerate(transformations, 1):
        classification = t.classify()
        print(f"Transformation {i}:")
        print(f"  Type: {classification.type}")

        # Handle different types programmatically
        if classification.type == "identity":
            print("  → No transformation needed")

        elif classification.type == "translation":
            dx, dy = classification.parameters["vector"]
            print(f"  → Shift by ({dx:.2f}, {dy:.2f})")

        elif classification.type == "rotation":
            angle = classification.parameters["angle_rad"]
            pivot = classification.parameters["pivot"]
            print(f"  → Rotate {math.degrees(angle):.1f}° around {pivot}")

        elif classification.type == "non_uniform_scaling":
            sx = classification.parameters["x_factor"]
            sy = classification.parameters["y_factor"]
            print(f"  → Scale by ({sx:.1f}x, {sy:.1f}x)")

        print()


def example_composition_analysis():
    """Demonstrate analyzing composed transformations."""
    print("=" * 60)
    print("Example 4: Composition Analysis")
    print("=" * 60)

    # Compose transformations
    t1 = Transform2D.translate(5, 0)
    t2 = Transform2D.rotate(math.pi / 2)
    composed = t2.compose(t1)

    print("Original transformations:")
    print(f"  T1: {t1.identify()}")
    print(f"  T2: {t2.identify()}")
    print()

    print("Composed (T2 ∘ T1):")
    classification = composed.classify()
    print(f"  Type: {classification.type}")

    if classification.type == "rotation":
        angle = classification.parameters["angle_rad"]
        pivot = classification.parameters["pivot"]
        print(f"  Result: Rotation by {math.degrees(angle):.2f}° around {pivot}")

    print()


def example_serialization():
    """Demonstrate how classification can be used for serialization."""
    print("=" * 60)
    print("Example 5: Serialization/Storage")
    print("=" * 60)

    # Create a transformation
    original = Transform2D.rotate(math.pi / 6, 10, 20)

    # Get classification (could be serialized to JSON, database, etc.)
    classification = original.classify()

    print("Serializable data:")
    print(f"  Type: '{classification.type}'")
    print(f"  Parameters: {classification.parameters}")
    print()

    # Reconstruct the transformation from classification
    if classification.type == "rotation":
        params = classification.parameters
        reconstructed = Transform2D.rotate(
            params["angle_rad"],
            params["pivot"][0],
            params["pivot"][1]
        )

        # Test that reconstruction works
        test_point = (15, 25)
        original_result = original.apply(test_point)
        reconstructed_result = reconstructed.apply(test_point)

        print(f"Test point: {test_point}")
        print(f"Original transform: {original_result}")
        print(f"Reconstructed transform: {reconstructed_result}")
        print(f"Match: {abs(original_result[0] - reconstructed_result[0]) < 1e-10 and abs(original_result[1] - reconstructed_result[1]) < 1e-10}")

    print()


if __name__ == "__main__":
    example_basic_usage()
    example_reflection_axis()
    example_programmatic_handling()
    example_composition_analysis()
    example_serialization()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
