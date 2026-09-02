#!/usr/bin/env python3
"""
Example demonstrating Transform2D.from_two_segments().
"""

from caleidoscope import Transform2D


def main():
    print("Example 1: Identity-like transformation")
    t1 = Transform2D.from_two_segments((0, 0), (1, 0), (0, 0), (1, 0), keep_orientation=True)
    print(f"  Transform (0,0): {t1.apply((0, 0))}")
    print(f"  Transform (1,0): {t1.apply((1, 0))}")
    print()

    print("Example 2: 90-degree rotation")
    t2 = Transform2D.from_two_segments((0, 0), (1, 0), (0, 0), (0, 1), keep_orientation=True)
    print(f"  Transform (0,0): {t2.apply((0, 0))}")
    print(f"  Transform (1,0): {t2.apply((1, 0))}")
    print()

    print("Example 3: Translation")
    t3 = Transform2D.from_two_segments((0, 0), (1, 0), (5, 3), (6, 3), keep_orientation=True)
    print(f"  Transform (0,0): {t3.apply((0, 0))}")
    print(f"  Transform (1,0): {t3.apply((1, 0))}")
    print()

    print("Example 4: Reflection (keep_orientation=False)")
    t4 = Transform2D.from_two_segments((0, 0), (1, 0), (0, 0), (1, 0), keep_orientation=False)
    print(f"  Transform (0,0): {t4.apply((0, 0))}")
    print(f"  Transform (1,0): {t4.apply((1, 0))}")
    print(f"  Transform (0,1): {t4.apply((0, 1))}")  # Should flip y


if __name__ == "__main__":
    main()
