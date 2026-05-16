"""
Euclidean geometry transformations in 2D.

This module provides 2D affine transformations using homogeneous coordinates
represented as 3x3 matrices, without requiring external dependencies.
"""

import math


class Transform2D:
    """
    Represents a 2D affine transformation using a 3x3 matrix in homogeneous coordinates.

    The transformation matrix has the form:
    [[m00, m01, m02],
     [m10, m11, m12],
     [0,   0,   1  ]]

    Where (m02, m12) represents translation, and the 2x2 upper-left submatrix
    represents rotation, reflection, scaling, and shear.
    """

    def __init__(self, matrix=None):
        """
        Initialize a transformation.

        Args:
            matrix: 3x3 matrix as a list of lists. If None, creates identity matrix.
        """
        if matrix is None:
            # Identity matrix
            self.matrix = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        else:
            self.matrix = [row[:] for row in matrix]  # Deep copy

    def apply(self, point):
        """
        Apply the transformation to a point.

        Args:
            point: A tuple (x, y) representing the point coordinates.

        Returns:
            A tuple (x', y') representing the transformed coordinates.
        """
        x, y = point
        # Homogeneous coordinates: [x, y, 1]
        x_new = self.matrix[0][0] * x + self.matrix[0][1] * y + self.matrix[0][2]
        y_new = self.matrix[1][0] * x + self.matrix[1][1] * y + self.matrix[1][2]
        return (x_new, y_new)

    def compose(self, other):
        """
        Compose this transformation with another (apply other first, then this).

        Args:
            other: Another Transform2D instance.

        Returns:
            A new Transform2D representing the composition.
        """
        result = [[0.0, 0.0, 0.0] for _ in range(3)]

        # Matrix multiplication: self.matrix @ other.matrix
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    result[i][j] += self.matrix[i][k] * other.matrix[k][j]

        return Transform2D(result)

    @staticmethod
    def translate(dx, dy):
        """
        Create a translation transformation.

        Args:
            dx: Translation in x direction.
            dy: Translation in y direction.

        Returns:
            A Transform2D representing the translation.
        """
        return Transform2D([[1.0, 0.0, dx], [0.0, 1.0, dy], [0.0, 0.0, 1.0]])

    @staticmethod
    def rotate(angle_rad, pivot_x=0.0, pivot_y=0.0):
        """
        Create a rotation transformation around a pivot point.

        Args:
            angle_rad: Rotation angle in radians (counter-clockwise).
            pivot_x: X coordinate of the pivot point.
            pivot_y: Y coordinate of the pivot point.

        Returns:
            A Transform2D representing the rotation.
        """
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        if pivot_x == 0.0 and pivot_y == 0.0:
            # Rotation around origin
            return Transform2D(
                [[cos_a, -sin_a, 0.0], [sin_a, cos_a, 0.0], [0.0, 0.0, 1.0]]
            )
        else:
            # Rotation around pivot: translate to origin, rotate, translate back
            # Combined matrix: T(pivot) * R * T(-pivot)
            tx = pivot_x - cos_a * pivot_x + sin_a * pivot_y
            ty = pivot_y - sin_a * pivot_x - cos_a * pivot_y

            return Transform2D(
                [[cos_a, -sin_a, tx], [sin_a, cos_a, ty], [0.0, 0.0, 1.0]]
            )

    @staticmethod
    def reflect_x():
        """
        Create a reflection transformation across the x-axis.

        Returns:
            A Transform2D representing the reflection.
        """
        return Transform2D([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]])

    def __repr__(self):
        """String representation for debugging."""
        return (
            f"Transform2D([\n"
            f"  [{self.matrix[0][0]:.6f}, {self.matrix[0][1]:.6f}, {self.matrix[0][2]:.6f}],\n"
            f"  [{self.matrix[1][0]:.6f}, {self.matrix[1][1]:.6f}, {self.matrix[1][2]:.6f}],\n"
            f"  [{self.matrix[2][0]:.6f}, {self.matrix[2][1]:.6f}, {self.matrix[2][2]:.6f}]\n"
            f"])"
        )
