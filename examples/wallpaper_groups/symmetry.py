"""
Derive the symmetry elements (rotation centres, mirror lines, glide axes) of
a constructed pattern from its tiles' transformations, and turn them into
synthetic tiles that any caleidoscope renderer can draw.
"""

import math
from dataclasses import dataclass

import caleidoscope

type Point = tuple[float, float]

TOLERANCE = 1e-6


@dataclass(frozen=True)
class View:
    """An axis-aligned rectangle, given by its centre and size."""

    center_x: float
    center_y: float
    width: float
    height: float

    def contains(self, p: Point) -> bool:
        return (
            abs(p[0] - self.center_x) <= self.width / 2
            and abs(p[1] - self.center_y) <= self.height / 2
        )
