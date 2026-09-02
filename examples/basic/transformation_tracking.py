#!/usr/bin/env python3
"""
Example demonstrating the transformation tracking feature in Caleidoscope.

This example shows how to:
1. Access the transformation and generator sequence for each tile
2. Use the format_generator_sequence() method for human-readable output
3. Query tiles by their construction history
"""

import math

from caleidoscope import Pattern


def main():
    print("\n" + "=" * 70)
    print("Transformation Tracking Example")
    print("=" * 70)

    # Create a simple equilateral triangle pattern
    h = math.sqrt(3) / 2
    vertices = [
        (0.0, 0.0),      # bottom-left
        (1.0, 0.0),      # bottom-right
        (0.5, h),        # top
    ]
    edges = [(0, 1, ""), (1, 2, ""), (2, 0, "")]
    center = (0.5, h / 3)
    tolerance = 0.01

    # Three generators for triangle tessellation
    identifications = [
        ((0, 1), (1, 0), True),  # g0: reflection across bottom edge
        ((1, 2), (2, 1), True),  # g1: reflection across right edge
        ((2, 0), (0, 2), True),  # g2: reflection across left edge
    ]

    pattern = Pattern(vertices, edges, [], center, tolerance, identifications)

    # Construct the pattern
    print("\nConstructing pattern...")
    constructed = pattern.construct(center_x=0.5, center_y=h/3, width=3.0, height=3.0)
    tiles = constructed.get_tiles()
    print(f"Generated {len(tiles)} tiles")

    # Example 1: Accessing the fundamental tile
    print("\n" + "-" * 70)
    print("Example 1: Fundamental Tile")
    print("-" * 70)
    fundamental = tiles[0]
    print(f"Generator sequence: {fundamental.generator_sequence}")
    print(f"Formatted: {fundamental.format_generator_sequence()}")
    print(f"Vertices: {fundamental.vertices}")

    # Example 2: First-generation tiles (single generator)
    print("\n" + "-" * 70)
    print("Example 2: First-Generation Tiles")
    print("-" * 70)
    first_gen = [t for t in tiles if len(t.generator_sequence) == 1]
    print(f"Found {len(first_gen)} first-generation tiles:")
    for i, tile in enumerate(first_gen, 1):
        print(f"  Tile {i}:")
        print(f"    Generator sequence: {tile.generator_sequence}")
        print(f"    Formatted: {tile.format_generator_sequence()}")
        print(f"    Center: ({tile.vertices[0][0]:.3f}, {tile.vertices[0][1]:.3f})")

    # Example 3: Second-generation tiles (composition of two generators)
    print("\n" + "-" * 70)
    print("Example 3: Second-Generation Tiles (showing first 5)")
    print("-" * 70)
    second_gen = [t for t in tiles if len(t.generator_sequence) == 2]
    print(f"Found {len(second_gen)} second-generation tiles")
    for i, tile in enumerate(second_gen[:5], 1):
        print(f"  Tile {i}:")
        print(f"    Generator sequence: {tile.generator_sequence}")
        print(f"    Formatted: {tile.format_generator_sequence()}")

    # Example 4: Finding tiles by generator sequence
    print("\n" + "-" * 70)
    print("Example 4: Finding Tiles by Generator Sequence")
    print("-" * 70)

    # Find all tiles that used generator 0 first
    tiles_with_g0_first = [t for t in tiles if t.generator_sequence and t.generator_sequence[0] == 0]
    print(f"Tiles starting with g0: {len(tiles_with_g0_first)}")

    # Find tiles with specific sequence
    target_sequence = (0, 1)
    matching_tiles = [t for t in tiles if t.generator_sequence == target_sequence]
    if matching_tiles:
        print(f"\nTiles with sequence {target_sequence}:")
        for tile in matching_tiles:
            print(f"  {tile.format_generator_sequence()}")

    # Example 5: Analyzing transformation compositions
    print("\n" + "-" * 70)
    print("Example 5: Transformation Analysis")
    print("-" * 70)

    # Get a multi-level tile
    complex_tiles = [t for t in tiles if len(t.generator_sequence) >= 3]
    if complex_tiles:
        tile = complex_tiles[0]
        print(f"Analyzing tile with sequence: {tile.format_generator_sequence()}")
        print(f"Generator sequence: {tile.generator_sequence}")
        print(f"Transformation matrix:")
        for row in tile.transformation.matrix:
            print(f"  [{row[0]:7.4f}, {row[1]:7.4f}, {row[2]:7.4f}]")

        # Apply transformation to a test point
        test_point = (0.0, 0.0)
        transformed = tile.transformation.apply(test_point)
        print(f"\nTransformation test:")
        print(f"  Original point: {test_point}")
        print(f"  Transformed point: ({transformed[0]:.4f}, {transformed[1]:.4f})")

    # Example 6: Statistics about generator usage
    print("\n" + "-" * 70)
    print("Example 6: Generator Usage Statistics")
    print("-" * 70)

    # Count how many times each generator appears in sequences
    generator_counts = {}
    for tile in tiles:
        for gen_idx in tile.generator_sequence:
            generator_counts[gen_idx] = generator_counts.get(gen_idx, 0) + 1

    print("Generator usage frequency:")
    for gen_idx in sorted(generator_counts.keys()):
        count = generator_counts[gen_idx]
        print(f"  g{gen_idx}: used {count} times")

    # Distribution by sequence length
    print("\nDistribution by composition depth:")
    length_dist = {}
    for tile in tiles:
        length = len(tile.generator_sequence)
        length_dist[length] = length_dist.get(length, 0) + 1

    for length in sorted(length_dist.keys()):
        count = length_dist[length]
        print(f"  Depth {length}: {count} tiles")

    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
