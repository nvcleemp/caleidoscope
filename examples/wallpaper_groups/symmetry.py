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


@dataclass(frozen=True)
class Line:
    """A line in canonical form: angle in [0, pi) and signed offset.

    Its points p satisfy n . p = offset, with n = (-sin angle, cos angle).
    """

    angle: float
    offset: float

    @staticmethod
    def through(point: Point, direction: Point) -> "Line":
        angle = math.atan2(direction[1], direction[0]) % math.pi
        if angle > math.pi - TOLERANCE:
            angle = 0.0
        return Line(angle, -math.sin(angle) * point[0] + math.cos(angle) * point[1])

    @property
    def direction(self) -> Point:
        return (math.cos(self.angle), math.sin(self.angle))

    def distance_to(self, p: Point) -> float:
        return abs(-math.sin(self.angle) * p[0] + math.cos(self.angle) * p[1] - self.offset)

    def is_close(self, other: "Line", tolerance: float = TOLERANCE) -> bool:
        return (
            abs(self.angle - other.angle) < tolerance
            and abs(self.offset - other.offset) < tolerance
        )

    def clip(self, view: View) -> tuple[Point, Point] | None:
        """The part of this line inside `view`, or None if it misses it."""
        dx, dy = self.direction
        # Point on the line closest to the view's centre.
        nx, ny = -dy, dx
        shift = self.offset - (nx * view.center_x + ny * view.center_y)
        px, py = view.center_x + shift * nx, view.center_y + shift * ny
        t_min, t_max = -math.inf, math.inf
        for p, d, low, high in (
            (px, dx, view.center_x - view.width / 2, view.center_x + view.width / 2),
            (py, dy, view.center_y - view.height / 2, view.center_y + view.height / 2),
        ):
            if abs(d) < TOLERANCE:
                if not low <= p <= high:
                    return None
                continue
            t1, t2 = (low - p) / d, (high - p) / d
            t_min, t_max = max(t_min, min(t1, t2)), min(t_max, max(t1, t2))
        if t_min >= t_max:
            return None
        return (px + t_min * dx, py + t_min * dy), (px + t_max * dx, py + t_max * dy)


@dataclass(frozen=True)
class RotationCentre:
    point: Point
    order: int


@dataclass(frozen=True)
class SymmetryElements:
    rotations: list[RotationCentre]
    mirrors: list[Line]
    glides: list[Line]


def _add_line(lines: list[Line], line: Line) -> None:
    if not any(line.is_close(other) for other in lines):
        lines.append(line)


def derive(transformations: list[caleidoscope.Transform2D], view: View) -> SymmetryElements:
    """Collect the symmetry elements of the given group elements that meet `view`.

    A line only counts as a glide axis if it is not also a mirror line: a
    mirror composed with a translation along itself classifies as a glide.
    """
    rotations: list[tuple[Point, int]] = []
    mirrors: list[Line] = []
    glide_candidates: list[Line] = []
    for transformation in transformations:
        classification = transformation.classify()
        parameters = classification.parameters
        match classification.type:
            case "rotation":
                pivot = parameters["pivot"]
                order = round(2 * math.pi / abs(parameters["angle_rad"]))
                for i, (other, other_order) in enumerate(rotations):
                    if math.dist(pivot, other) < TOLERANCE:
                        rotations[i] = (other, max(order, other_order))
                        break
                else:
                    rotations.append((pivot, order))
            case "reflection":
                _add_line(mirrors, Line.through(parameters["axis_point"], parameters["axis_direction"]))
            case "glide_reflection":
                _add_line(glide_candidates, Line.through(parameters["axis_point"], parameters["axis_direction"]))
    glides = [g for g in glide_candidates if not any(g.is_close(m) for m in mirrors)]
    return SymmetryElements(
        rotations=[RotationCentre(p, order) for p, order in rotations if view.contains(p)],
        mirrors=[m for m in mirrors if m.clip(view) is not None],
        glides=[g for g in glides if g.clip(view) is not None],
    )


type Signature = tuple[frozenset[int], frozenset[int], int, bool]


def signature(elements: SymmetryElements) -> Signature:
    """(orders of centres on a mirror, orders of centres off every mirror,
    number of mirror directions, has glide axes)."""
    on_mirror: set[int] = set()
    off_mirror: set[int] = set()
    for centre in elements.rotations:
        if any(m.distance_to(centre.point) < TOLERANCE for m in elements.mirrors):
            on_mirror.add(centre.order)
        else:
            off_mirror.add(centre.order)
    directions: list[float] = []
    for m in elements.mirrors:
        if not any(abs(m.angle - d) < TOLERANCE for d in directions):
            directions.append(m.angle)
    return frozenset(on_mirror), frozenset(off_mirror), len(directions), bool(elements.glides)


def _marker(centre: RotationCentre, angle: float, size: float) -> list[Point]:
    """Outline of a rotation-centre marker, with a symmetry axis along `angle`."""
    x, y = centre.point
    if centre.order == 2:
        # Lens: two circular arcs between (-size, 0) and (size, 0), bulging
        # by half the size.
        bulge = size / 2
        k = (size * size - bulge * bulge) / (2 * bulge)
        radius = k + bulge
        half = math.atan2(size, k)
        arc = [(radius * math.sin(t), radius * math.cos(t) - k)
               for t in (half - 2 * half * i / 8 for i in range(9))]
        local = arc + [(-px, -py) for px, py in arc[1:-1]]
    else:
        # Regular polygon with a vertex on the axis, except squares, which
        # get an edge parallel to it.
        offset = math.pi / 4 if centre.order == 4 else 0.0
        local = [
            (size * math.cos(offset + 2 * math.pi * i / centre.order),
             size * math.sin(offset + 2 * math.pi * i / centre.order))
            for i in range(centre.order)
        ]
    c, s = math.cos(angle), math.sin(angle)
    return [(x + c * px - s * py, y + s * px + c * py) for px, py in local]


def to_tiles(elements: SymmetryElements, view: View, marker_size: float) -> list[caleidoscope.Tile]:
    """Two tiles in world coordinates: the clipped mirror/glide lines, then
    the rotation-centre markers (so markers are drawn on top of lines).

    A marker is aligned with a mirror through its centre, if there is one.
    """
    line_vertices: list[Point] = []
    line_edges: list[tuple[int, int, str]] = []
    for annotation, lines in (("glide", elements.glides), ("mirror", elements.mirrors)):
        for line in lines:
            segment = line.clip(view)
            if segment is None:
                continue
            line_vertices.extend(segment)
            line_edges.append((len(line_vertices) - 2, len(line_vertices) - 1, annotation))

    marker_vertices: list[Point] = []
    marker_polygons: list[tuple[list[int], str]] = []
    for centre in elements.rotations:
        angle = next(
            (m.angle for m in elements.mirrors if m.distance_to(centre.point) < TOLERANCE), 0.0
        )
        outline = _marker(centre, angle, marker_size)
        start = len(marker_vertices)
        marker_vertices.extend(outline)
        marker_polygons.append((list(range(start, start + len(outline))), f"rot{centre.order}"))

    identity = caleidoscope.Transform2D()
    return [
        caleidoscope.Tile(line_vertices, line_edges, [], identity, ()),
        caleidoscope.Tile(marker_vertices, [], marker_polygons, identity, ()),
    ]
