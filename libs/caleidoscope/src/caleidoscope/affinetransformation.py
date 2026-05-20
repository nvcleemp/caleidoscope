"""
Euclidean geometry transformations in 2D.

This module provides 2D affine transformations using homogeneous coordinates
represented as 3x3 matrices, without requiring external dependencies.

Example usage:
    >>> # Create a transformation from segment (0,0)-(1,0) to (5,5)-(5,6)
    >>> transform = Transform2D.from_two_segments((0, 0), (1, 0), (5, 5), (5, 6), keep_orientation=True)
    >>> result = transform.apply((1, 0))
    >>> print(result)  # Should be close to (5, 6)
"""

import math
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class TransformationClassification:
    """
    Machine-readable classification of an affine transformation.

    Attributes:
        type: The type of transformation (identity, translation, rotation, etc.)
        parameters: Dictionary containing type-specific parameters:
            - identity: {} (no parameters)
            - translation: {"vector": (tx, ty)}
            - rotation: {"angle_rad": float, "pivot": (cx, cy)}
            - reflection: {"axis_point": (px, py), "axis_direction": (dx, dy), 
                          "line_equation": (a, b, c)}
            - glide_reflection: {"axis_point": (px, py), "axis_direction": (dx, dy), 
                                "glide_vector": (gx, gy), "line_equation": (a, b, c)}
            - uniform_scaling: {"factor": float, "translation": (tx, ty)}
            - non_uniform_scaling: {"x_factor": float, "y_factor": float, 
                                   "translation": (tx, ty)}
            - complex_affine: {"matrix": [[a, b, tx], [c, d, ty]]}

    Note:
        For reflection/glide_reflection, the line_equation (a, b, c) represents: a*x + b*y + c = 0
    """
    type: Literal[
        "identity",
        "translation",
        "rotation",
        "reflection",
        "glide_reflection",
        "uniform_scaling",
        "non_uniform_scaling",
        "complex_affine"
    ]
    parameters: dict[str, Any]


def _compute_angle_xy(x: float, y: float) -> float:
    """
    Compute the angle of a 2D vector with respect to the positive x-axis in radians.

    Args:
        x: X component of the vector
        y: Y component of the vector

    Returns:
        Angle in radians, in the range [0, 2π) for most cases.
    """
    if x != 0:
        a = math.atan(abs(y) / abs(x))

        if x > 0:
            if y > 0:
                return a
            else:
                return 2.0 * math.pi - a
        else:  # x < 0
            if y > 0:
                return math.pi - a
            else:
                return math.pi + a
    elif y > 0:
        return 0.5 * math.pi
    else:  # y < 0
        return 1.5 * math.pi

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

    def __init__(self, matrix: list[list[float]] | None = None) -> None:
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

    def apply(self, point: tuple[float, float]) -> tuple[float, float]:
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

    def compose(self, other: "Transform2D") -> "Transform2D":
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
    def translate(dx: float, dy: float) -> "Transform2D":
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
    def rotate(angle_rad: float, pivot_x: float = 0.0, pivot_y: float = 0.0) -> "Transform2D":
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
    def reflect_x() -> "Transform2D":
        """
        Create a reflection transformation across the x-axis.

        Returns:
            A Transform2D representing the reflection.
        """
        return Transform2D([[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0]])

    @staticmethod
    def from_two_segments(a1: tuple[float, float], b1: tuple[float, float], a2: tuple[float, float], b2: tuple[float, float], keep_orientation: bool = True) -> "Transform2D":
        """
        Create a transformation that maps segment a1-b1 to segment a2-b2.

        This function creates a 2D affine transformation that maps point a1 to a2
        and point b1 to b2. The transformation preserves distances (assuming the
        segments have the same length).

        Based on code from Tegula.

        Args:
            a1: Source point as tuple (x, y).
            b1: Source point as tuple (x, y).
            a2: Target point as tuple (x, y).
            b2: Target point as tuple (x, y).
            keep_orientation: If True, preserves orientation (rotation only).
                             If False, allows reflection (flips orientation).

        Returns:
            A Transform2D object representing the transformation.

        Example:
            >>> # Map horizontal segment to vertical segment
            >>> t = Transform2D.from_two_segments((0, 0), (1, 0), (0, 0), (0, 1), keep_orientation=True)
            >>> result = t.apply((1, 0))
            >>> # result should be close to (0, 1)
        """
        a1_x, a1_y = a1
        b1_x, b1_y = b1
        a2_x, a2_y = a2
        b2_x, b2_y = b2

        # Compute direction vectors
        v1_x = b1_x - a1_x
        v1_y = b1_y - a1_y
        v2_x = b2_x - a2_x
        v2_y = b2_y - a2_y

        if keep_orientation:
            # Compute angle difference
            angle1 = _compute_angle_xy(v1_x, v1_y)
            angle2 = _compute_angle_xy(v2_x, v2_y)
            diff = angle2 - angle1

            # Create transformations: rotate around a1, then translate to a2
            rotate = Transform2D.rotate(diff, a1_x, a1_y)
            translate = Transform2D.translate(a2_x - a1_x, a2_y - a1_y)

            # Compose: translate(rotate(...))
            return translate.compose(rotate)
        else:
            # More complex transformation with reflection
            angle1 = _compute_angle_xy(v1_x, v1_y)
            angle2 = _compute_angle_xy(v2_x, v2_y)

            # Step 1: Rotate so that a1-b1 is parallel to x-axis
            rotate1 = Transform2D.rotate(-angle1, a1_x, a1_y)

            # Step 2: Translate to x-axis
            trans_to_x_axis = Transform2D.translate(0, -a1_y)

            # Step 3: Reflect across x-axis
            reflect = Transform2D.reflect_x()

            # Step 4: Translate back from x-axis
            trans_back = Transform2D.translate(0, a1_y)

            # Step 5: Rotate to match angle of a2-b2
            rotate2 = Transform2D.rotate(angle2, a1_x, a1_y)

            # Step 6: Translate a1 to a2
            translate = Transform2D.translate(a2_x - a1_x, a2_y - a1_y)

            # Compose all transformations (right to left)
            # translate(rotate2(trans_back(reflect(trans_to_x_axis(rotate1(...))))))
            result = translate
            result = result.compose(rotate2)
            result = result.compose(trans_back)
            result = result.compose(reflect)
            result = result.compose(trans_to_x_axis)
            result = result.compose(rotate1)

            return result

    @staticmethod
    def from_two_triplets(
        triplet_from: tuple[tuple[float, float], tuple[float, float], tuple[float, float]],
        triplet_to: tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    ) -> "Transform2D":
        """
        Create a transformation that maps one triplet of points to another.

        Each triplet is a tuple of three points that can be seen as determining
        a base (origin, x_endpoint, y_endpoint) of 2D space. This method creates a
        transformation that maps the three points of triplet_from to the
        corresponding three points of triplet_to.

        Args:
            triplet_from: Tuple of three points ((a1x, a1y), (b1x, b1y), (c1x, c1y))
                      representing the source triplet.
            triplet_to: Tuple of three points ((a2x, a2y), (b2x, b2y), (c2x, c2y))
                    representing the target triplet.

        Returns:
            A Transform2D representing the triplet transition.

        Raises:
            ValueError: If the basis vectors in triplet_from are collinear or degenerate.

        Example:
            >>> # Map standard basis translated by (5,3)
            >>> triplet_from = ((0, 0), (1, 0), (0, 1))
            >>> triplet_to = ((5, 3), (6, 3), (5, 4))
            >>> t = Transform2D.from_two_triplets(triplet_from, triplet_to)
            >>> result = t.apply((0, 0))
            >>> # result should be (5, 3)
        """
        # Extract points from each triplet
        a_from, b_from, c_from = triplet_from
        a_to, b_to, c_to = triplet_to

        # Compute basis vectors for triplet_from
        x_vec_from_x = b_from[0] - a_from[0]
        x_vec_from_y = b_from[1] - a_from[1]
        y_vec_from_x = c_from[0] - a_from[0]
        y_vec_from_y = c_from[1] - a_from[1]

        # Compute basis vectors for triplet_to
        x_vec_to_x = b_to[0] - a_to[0]
        x_vec_to_y = b_to[1] - a_to[1]
        y_vec_to_x = c_to[0] - a_to[0]
        y_vec_to_y = c_to[1] - a_to[1]

        # Compute determinant of triplet_from matrix
        det = x_vec_from_x * y_vec_from_y - x_vec_from_y * y_vec_from_x

        if abs(det) < 1e-10:
            raise ValueError(
                "triplet_from vectors are collinear or degenerate (determinant near zero)"
            )

        # Compute inverse of triplet_from matrix
        b_from_inv_00 = y_vec_from_y / det
        b_from_inv_01 = -y_vec_from_x / det
        b_from_inv_10 = -x_vec_from_y / det
        b_from_inv_11 = x_vec_from_x / det

        # Compute linear transformation matrix: L = B_to * B_from_inv
        m00 = x_vec_to_x * b_from_inv_00 + y_vec_to_x * b_from_inv_10
        m01 = x_vec_to_x * b_from_inv_01 + y_vec_to_x * b_from_inv_11
        m10 = x_vec_to_y * b_from_inv_00 + y_vec_to_y * b_from_inv_10
        m11 = x_vec_to_y * b_from_inv_01 + y_vec_to_y * b_from_inv_11

        # Compute translation components
        # The transformation maps: a_to + L * (point - a_from)
        # Expanding: a_to + L * point - L * a_from
        tx = a_to[0] - m00 * a_from[0] - m01 * a_from[1]
        ty = a_to[1] - m10 * a_from[0] - m11 * a_from[1]

        return Transform2D([[m00, m01, tx], [m10, m11, ty], [0.0, 0.0, 1.0]])

    def classify(self) -> TransformationClassification:
        """
        Analyzes the transformation matrix and returns a machine-readable
        classification with structured parameters.

        Returns:
            TransformationClassification object containing the type and parameters
            of the transformation.

        Example:
            >>> t = Transform2D.translate(5, 3)
            >>> result = t.classify()
            >>> print(result.type)  # "translation"
            >>> print(result.parameters)  # {"vector": (5.0, 3.0)}
        """
        a, b, tx = self.matrix[0][0], self.matrix[0][1], self.matrix[0][2]
        c, d, ty = self.matrix[1][0], self.matrix[1][1], self.matrix[1][2]

        # Helper for floating point comparisons
        def is_zero(val):
            return abs(val) < 1e-6

        def is_equal(v1, v2):
            return abs(v1 - v2) < 1e-6

        det_R = a * d - b * c
        det_A = (a - 1) * (d - 1) - b * c

        # Check if the 2x2 submatrix is orthogonal (represents rigid motion)
        # Conditions: a^2 + c^2 = 1, b^2 + d^2 = 1, dot product (ab + cd) = 0
        is_orthogonal = (
            is_equal(a * a + c * c, 1.0)
            and is_equal(b * b + d * d, 1.0)
            and is_zero(a * b + c * d)
        )

        if is_orthogonal:
            if is_equal(det_R, 1.0):
                # --- Orientation-Preserving (Identity, Translation, Rotation) ---
                if is_equal(a, 1.0) and is_equal(d, 1.0) and is_zero(b) and is_zero(c):
                    if is_zero(tx) and is_zero(ty):
                        return TransformationClassification(
                            type="identity",
                            parameters={}
                        )
                    else:
                        return TransformationClassification(
                            type="translation",
                            parameters={"vector": (tx, ty)}
                        )
                else:
                    # It's a rotation. Calculate angle and center.
                    angle_rad = math.atan2(c, a)

                    # Solve for fixed point: (R - I) * Center = -T
                    center_x = (-tx * (d - 1) + b * ty) / det_A
                    center_y = (-ty * (a - 1) + c * tx) / det_A

                    return TransformationClassification(
                        type="rotation",
                        parameters={"angle_rad": angle_rad, "pivot": (center_x, center_y)}
                    )

            elif is_equal(det_R, -1.0):
                # --- Orientation-Reversing (Reflection, Glide Reflection) ---
                # Shortcut: A reflection applied twice gives Identity.
                # A glide reflection applied twice gives a pure translation.
                squared = self.compose(self)
                t2x, t2y = squared.matrix[0][2], squared.matrix[1][2]

                # Calculate axis direction vector (eigenvector for lambda = 1)
                if not is_zero(b):
                    vx, vy = -b, a - 1
                elif not is_zero(c):
                    vx, vy = d - 1, -c
                else:
                    vx, vy = (1.0, 0.0) if a > 0 else (0.0, 1.0)

                # Normalize the direction vector
                mag = math.hypot(vx, vy)
                vx, vy = vx / mag, vy / mag

                # One point on the line is the midpoint of the origin's transformation
                mid_x, mid_y = tx / 2.0, ty / 2.0

                # Compute line equation: a*x + b*y + c = 0
                # Normal vector: (-vy, vx) perpendicular to direction (vx, vy)
                line_a = -vy
                line_b = vx
                line_c = vy * mid_x - vx * mid_y

                if is_zero(t2x) and is_zero(t2y):
                    return TransformationClassification(
                        type="reflection",
                        parameters={
                            "axis_point": (mid_x, mid_y),
                            "axis_direction": (vx, vy),
                            "line_equation": (line_a, line_b, line_c)
                        }
                    )
                else:
                    # The glide vector is exactly half of the double-translation
                    gx, gy = t2x / 2.0, t2y / 2.0
                    return TransformationClassification(
                        type="glide_reflection",
                        parameters={
                            "axis_point": (mid_x, mid_y),
                            "axis_direction": (vx, vy),
                            "glide_vector": (gx, gy),
                            "line_equation": (line_a, line_b, line_c)
                        }
                    )

        # --- Non-Rigid Transformations ---
        if is_zero(b) and is_zero(c):
            if is_equal(a, d):
                return TransformationClassification(
                    type="uniform_scaling",
                    parameters={"factor": a, "translation": (tx, ty)}
                )
            else:
                return TransformationClassification(
                    type="non_uniform_scaling",
                    parameters={"x_factor": a, "y_factor": d, "translation": (tx, ty)}
                )

        return TransformationClassification(
            type="complex_affine",
            parameters={"matrix": [[a, b, tx], [c, d, ty]]}
        )

    def identify(self) -> str:
        """
        Analyzes the transformation matrix and returns a human-readable
        string identifying the geometric transformation.

        Returns:
            A human-readable string describing the transformation.

        Example:
            >>> t = Transform2D.rotate(math.pi/2, 0, 0)
            >>> print(t.identify())  # "Rotation by 90.00° around pivot (0.0000, 0.0000)"
        """
        classification = self.classify()
        params = classification.parameters

        if classification.type == "identity":
            return "Identity"

        elif classification.type == "translation":
            tx, ty = params["vector"]
            return f"Pure Translation by vector ({tx:.4f}, {ty:.4f})"

        elif classification.type == "rotation":
            angle_rad = params["angle_rad"]
            angle_deg = math.degrees(angle_rad)
            # Normalize angle to [0, 360)
            if angle_deg < 0:
                angle_deg += 360
            cx, cy = params["pivot"]
            return f"Rotation by {angle_deg:.2f}° around pivot ({cx:.4f}, {cy:.4f})"

        elif classification.type == "reflection":
            px, py = params["axis_point"]
            vx, vy = params["axis_direction"]
            axis_info = f"passing through ({px:.4f}, {py:.4f}) with direction ({vx:.4f}, {vy:.4f})"
            return f"Pure Reflection across axis {axis_info}"

        elif classification.type == "glide_reflection":
            px, py = params["axis_point"]
            vx, vy = params["axis_direction"]
            gx, gy = params["glide_vector"]
            axis_info = f"passing through ({px:.4f}, {py:.4f}) with direction ({vx:.4f}, {vy:.4f})"
            return f"Glide Reflection across axis {axis_info}, gliding by ({gx:.4f}, {gy:.4f})"

        elif classification.type == "uniform_scaling":
            factor = params["factor"]
            return f"Uniform Scaling by factor {factor:.4f}"

        elif classification.type == "non_uniform_scaling":
            x_factor = params["x_factor"]
            y_factor = params["y_factor"]
            return f"Non-uniform Scaling by factors (X: {x_factor:.4f}, Y: {y_factor:.4f})"

        else:  # complex_affine
            return "Complex Affine (Combination of Shear/Scale/Rotation)"

    def __repr__(self):
        """String representation for debugging."""
        return (
            f"Transform2D([\n"
            f"  [{self.matrix[0][0]:.6f}, {self.matrix[0][1]:.6f}, {self.matrix[0][2]:.6f}],\n"
            f"  [{self.matrix[1][0]:.6f}, {self.matrix[1][1]:.6f}, {self.matrix[1][2]:.6f}],\n"
            f"  [{self.matrix[2][0]:.6f}, {self.matrix[2][1]:.6f}, {self.matrix[2][2]:.6f}]\n"
            f"])"
        )
