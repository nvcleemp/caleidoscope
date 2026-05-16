"""
QuadTree data structure for efficient 2D point storage with duplicate detection.

This module provides a spatial data structure for storing 2D points with
tolerance-based duplicate checking. Points are organized hierarchically
for efficient spatial queries and duplicate detection.

Example usage:
    >>> tree = QuadTree()
    >>> tree.insert((1.0, 2.0), tolerance=0.01)
    True
    >>> tree.insert((1.0, 2.0), tolerance=0.01)  # Duplicate
    False
    >>> tree.size()
    1
"""

import math


def euclidean_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """
    Calculate the Euclidean distance between two 2D points.

    Args:
        p1: First point as tuple (x, y).
        p2: Second point as tuple (x, y).

    Returns:
        The Euclidean distance as a float.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx * dx + dy * dy)


class Boundary:
    """
    Represents a rectangular region in 2D space.

    The boundary is defined by a center point and half-dimensions,
    representing an axis-aligned rectangle.
    """

    def __init__(self, center_x: float, center_y: float, half_width: float, half_height: float) -> None:
        """
        Initialize a boundary.

        Args:
            center_x: X coordinate of the center point.
            center_y: Y coordinate of the center point.
            half_width: Half the width of the rectangle (must be positive).
            half_height: Half the height of the rectangle (must be positive).

        Raises:
            ValueError: If half_width or half_height is not positive.
        """
        if half_width <= 0:
            raise ValueError(f"half_width must be positive, got {half_width}")
        if half_height <= 0:
            raise ValueError(f"half_height must be positive, got {half_height}")
        
        self.center_x = center_x
        self.center_y = center_y
        self.half_width = half_width
        self.half_height = half_height

    def contains(self, point: tuple[float, float]) -> bool:
        """
        Check if a point is within this boundary.

        Args:
            point: A tuple (x, y) representing the point coordinates.

        Returns:
            True if the point is within or on the boundary, False otherwise.
        """
        x, y = point
        return (
            x >= self.center_x - self.half_width
            and x <= self.center_x + self.half_width
            and y >= self.center_y - self.half_height
            and y <= self.center_y + self.half_height
        )

    def intersects(self, other: "Boundary") -> bool:
        """
        Check if this boundary intersects with another boundary.

        Args:
            other: Another Boundary instance.

        Returns:
            True if the boundaries overlap, False otherwise.
        """
        return not (
            self.center_x - self.half_width > other.center_x + other.half_width
            or self.center_x + self.half_width < other.center_x - other.half_width
            or self.center_y - self.half_height > other.center_y + other.half_height
            or self.center_y + self.half_height < other.center_y - other.half_height
        )

    def bounds(self) -> tuple[float, float, float, float]:
        """
        Get the bounding box of this boundary.

        Returns:
            A tuple (min_x, min_y, max_x, max_y) representing the corners of the rectangle.
        """
        return (
            self.center_x - self.half_width,
            self.center_y - self.half_height,
            self.center_x + self.half_width,
            self.center_y + self.half_height,
        )


class QuadTreeNode:
    """
    A node in the QuadTree structure.

    Each node represents a rectangular region and can contain a limited number
    of points before subdividing into four child quadrants.
    """

    def __init__(self, boundary: Boundary, capacity: int = 4) -> None:
        """
        Initialize a QuadTree node.

        Args:
            boundary: A Boundary instance defining the node's region.
            capacity: Maximum number of points before subdivision (default 4).
        """
        self.boundary = boundary
        self.capacity = capacity
        self.points: list[tuple[float, float]] = []
        self.children: list[QuadTreeNode] | None = None  # Will be [NW, NE, SW, SE] after subdivision

    def is_leaf(self) -> bool:
        """
        Check if this node is a leaf (has no children).

        Returns:
            True if the node is a leaf, False otherwise.
        """
        return self.children is None

    def subdivide(self) -> None:
        """
        Subdivide this node into four child quadrants.

        Creates four child nodes representing the NW, NE, SW, and SE
        quadrants of this node"s boundary.
        """
        cx = self.boundary.center_x
        cy = self.boundary.center_y
        hw = self.boundary.half_width / 2
        hh = self.boundary.half_height / 2

        # Create four child boundaries
        nw = Boundary(cx - hw, cy + hh, hw, hh)  # Northwest
        ne = Boundary(cx + hw, cy + hh, hw, hh)  # Northeast
        sw = Boundary(cx - hw, cy - hh, hw, hh)  # Southwest
        se = Boundary(cx + hw, cy - hh, hw, hh)  # Southeast

        self.children = [
            QuadTreeNode(nw, self.capacity),
            QuadTreeNode(ne, self.capacity),
            QuadTreeNode(sw, self.capacity),
            QuadTreeNode(se, self.capacity),
        ]

    def has_point_within_tolerance(self, point: tuple[float, float], tolerance: float) -> bool:
        """
        Check if a point within tolerance already exists in this subtree.

        Args:
            point: A tuple (x, y) representing the point to check.
            tolerance: Maximum distance for considering points as duplicates.

        Returns:
            True if a point within tolerance exists, False otherwise.
        """
        # Check points in current node
        for existing_point in self.points:
            if euclidean_distance(point, existing_point) <= tolerance:
                return True

        # Recursively check children if not a leaf
        if self.children is not None:
            for child in self.children:
                if child.boundary.contains(point):
                    if child.has_point_within_tolerance(point, tolerance):
                        return True

        return False

    def insert(self, point: tuple[float, float], tolerance: float) -> bool:
        """
        Insert a point into this node or its children.

        Args:
            point: A tuple (x, y) representing the point to insert.
            tolerance: Maximum distance for considering points as duplicates.

        Returns:
            True if the point was successfully inserted, False if it's a
            duplicate within tolerance or outside the boundary.
        """
        # Check if point is within this node"s boundary
        if not self.boundary.contains(point):
            return False

        # Check for duplicates within tolerance in this subtree
        if self.has_point_within_tolerance(point, tolerance):
            return False

        # If we"re a leaf and have capacity, add the point here
        if self.is_leaf():
            if len(self.points) < self.capacity:
                self.points.append(point)
                return True
            else:
                # Subdivide and redistribute points
                self.subdivide()
                # Redistribute existing points to children
                old_points = self.points
                self.points = []
                for p in old_points:
                    self._insert_into_children(p)
                # Now insert the new point
                return self._insert_into_children(point)
        else:
            # We're not a leaf, insert into appropriate child
            return self._insert_into_children(point)

    def _insert_into_children(self, point: tuple[float, float]) -> bool:
        """
        Insert a point into the appropriate child node(s).

        Args:
            point: A tuple (x, y) representing the point to insert.

        Returns:
            True if inserted successfully, False otherwise.
        """
        if self.children is None:
            return False
        for child in self.children:
            if child.boundary.contains(point):
                return child.insert(point, 0)  # No tolerance check, already done
        return False


class QuadTree:
    """
    A QuadTree spatial data structure for efficient 2D point storage.

    The QuadTree organizes points in a hierarchical structure, automatically
    subdividing regions as they fill up. It supports tolerance-based duplicate
    detection to prevent storing nearly identical points.
    """

    def __init__(self, boundary: Boundary | None = None) -> None:
        """
        Initialize a QuadTree.

        Args:
            boundary: Optional Boundary instance defining the tree"s region.
                     If None, uses a default boundary from (-1000, -1000) to (1000, 1000).
        """
        if boundary is None:
            boundary = Boundary(0, 0, 1000, 1000)
        self.root = QuadTreeNode(boundary)
        self.count = 0

    def insert(self, point: tuple[float, float], tolerance: float) -> bool:
        """
        Insert a point into the QuadTree.

        Args:
            point: A tuple (x, y) representing the point to insert.
            tolerance: Maximum distance for considering points as duplicates.
                      If another point within this distance already exists,
                      the insertion will fail.

        Returns:
            True if the point was successfully inserted, False if it"s a
            duplicate within tolerance or outside the tree"s boundary.
        """
        if self.root.insert(point, tolerance):
            self.count += 1
            return True
        return False

    def size(self) -> int:
        """
        Get the number of points stored in the QuadTree.

        Returns:
            The count of points as an integer.
        """
        return self.count

    def clear(self) -> None:
        """
        Remove all points from the QuadTree.

        Resets the tree to its initial empty state with the same boundary.
        """
        boundary = self.root.boundary
        self.root = QuadTreeNode(boundary)
        self.count = 0

if __name__ == "__main__":
    # Test basic insertion
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