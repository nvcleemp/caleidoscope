#!/usr/bin/env python3
"""
Example demonstrating QuadTree insertion, tolerance-based duplicate
rejection, and subdivision.
"""

from caleidoscope import QuadTree


def main():
    tree = QuadTree()
    print("Test 1 - Basic insertion:")
    print(f"  Insert (1.0, 2.0): {tree.insert((1.0, 2.0), 0.01)}")
    print(f"  Insert (5.0, 6.0): {tree.insert((5.0, 6.0), 0.01)}")
    print(f"  Size: {tree.size()}")

    # Test duplicate rejection
    print("\nTest 2 - Duplicate rejection:")
    print(f"  Insert (1.0, 2.0) again: {tree.insert((1.0, 2.0), 0.01)}")
    print(f"  Size: {tree.size()}")

    # Test tolerance-based duplicate
    print("\nTest 3 - Tolerance-based duplicate:")
    print(f"  Insert (1.0001, 2.0001) with tolerance 0.001: {tree.insert((1.0001, 2.0001), 0.001)}")
    print(f"  Size: {tree.size()}")

    # Test subdivision (insert >4 points)
    print("\nTest 4 - Subdivision (insert 5 distinct points):")
    tree.clear()
    for i in range(5):
        result = tree.insert((i * 10.0, i * 10.0), 0.01)
        print(f"  Insert ({i * 10.0}, {i * 10.0}): {result}")
    print(f"  Final size: {tree.size()}")

    # Test clear
    print("\nTest 5 - Clear:")
    tree.clear()
    print(f"  Size after clear: {tree.size()}")

    print("\n✓ All tests completed successfully!")


if __name__ == "__main__":
    main()
