import itertools
import math
from pathlib import Path

import caleidoscope

OUTPUT_DIR = Path(__file__).parent / "output"


def polar_to_cartesian(r, theta):
    """Convert polar coordinates to Cartesian coordinates."""
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    return (x, y)


def midpoint(p1, p2):
    """Calculate the midpoint between two points."""
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def barycenter(points):
    """Calculate the barycenter (centroid) of a list of points."""
    n = len(points)
    if n == 0:
        return (0, 0)
    x_sum = sum(p[0] for p in points)
    y_sum = sum(p[1] for p in points)
    return (x_sum / n, y_sum / n)


def wrap_tikz_picture(tikz_content):
    """Wrap the TikZ content in a tikz picture environment."""
    return f"""\\begin{{tikzpicture}}
{tikz_content}\\end{{tikzpicture}}
"""


def wrap_standalone(content):
    """Wrap the TikZ content in a standalone document."""
    return f"""\\documentclass[tikz]{{standalone}}
\\begin{{document}}
{content}
\\end{{document}}
"""


def write_standalone_tex(path, content):
    """Write content, wrapped in a standalone document, to path."""
    with open(path, "w") as f:
        f.write(wrap_standalone(content))


def generate_pgg_symmetries_simple(
    representatives: list[
        caleidoscope.affinetransformation.TransformationClassification
    ],
    bbox,
    margin=0.5,
):
    """
    Generates rotation centers and clipped glide axes using only pure Python.
    Assumes given representatives intersect or lie within the bounding box.
    """
    xmin, ymin, xmax, ymax = bbox

    # 1. Parse input data
    rot_seeds = []
    glide_seeds = []

    for rep in representatives:
        params = rep.parameters
        if rep.type == "rotation":
            rot_seeds.append(params["pivot"])
        elif rep.type == "glide_reflection":
            glide_seeds.append(
                {
                    "point": params["axis_point"],
                    "dir": params["axis_direction"],
                    "vec": params["glide_vector"],
                }
            )

    # 2. Extract pure translation lattice vectors (2 * glide_vector)
    # g1 and g2 are the two minimal glide vectors
    g1 = glide_seeds[0]["vec"]
    g2 = glide_seeds[1]["vec"]

    t1 = (g1[0], g1[1])
    t2 = (g2[0], g2[1])

    # Calculate bounding box dimensions to determine maximum loop steps
    box_width = xmax - xmin
    box_height = ymax - ymin
    box_diag = math.sqrt(box_width**2 + box_height**2)

    # Step sizes (lengths of the translation vectors)
    len_t1 = math.sqrt(t1[0] ** 2 + t1[1] ** 2)
    len_t2 = math.sqrt(t2[0] ** 2 + t2[1] ** 2)

    # Conservatively estimate how many grid steps are needed to cover the box
    max_steps_1 = int(ceil_div(box_diag, len_t1)) + 2
    max_steps_2 = int(ceil_div(box_diag, len_t2)) + 2

    # Helper function to clip an infinite line to the bounding box
    def get_bounded_line(px, py, dx, dy):
        # Normalize direction vector
        mag = math.sqrt(dx * dx + dy * dy)
        dx, dy = dx / mag, dy / mag

        t_values = []
        # Intersect with vertical boundaries
        if abs(dx) > 1e-9:
            t_values.append((xmin - px) / dx)
            t_values.append((xmax - px) / dx)
        # Intersect with horizontal boundaries
        if abs(dy) > 1e-9:
            t_values.append((ymin - py) / dy)
            t_values.append((ymax - py) / dy)

        # Filter points that land on the box boundaries
        valid_pts = []
        for t in t_values:
            ix = px + t * dx
            iy = py + t * dy
            if (xmin - 1e-5 <= ix <= xmax + 1e-5) and (
                ymin - 1e-5 <= iy <= ymax + 1e-5
            ):
                valid_pts.append((t, ix, iy))

        if len(valid_pts) < 2:
            return None

        # Sort by t to find entry and exit points, then apply margin
        valid_pts.sort(key=lambda item: item[0])
        _, x_start, y_start = valid_pts[0]
        _, x_end, y_end = valid_pts[-1]

        return (
            (x_start - margin * dx, y_start - margin * dy),
            (x_end + margin * dx, y_end + margin * dy),
        )

    # --- GENERATE ROTATION CENTERS ---
    rotation_centers = []
    seen_rot = set()

    for rx, ry in rot_seeds:
        for i in range(-max_steps_1, max_steps_1 + 1):
            for j in range(-max_steps_2, max_steps_2 + 1):
                cx = rx + i * t1[0] + j * t2[0]
                cy = ry + i * t1[1] + j * t2[1]

                if xmin <= cx <= xmax and ymin <= cy <= ymax:
                    key = (round(cx, 4), round(cy, 4))
                    if key not in seen_rot:
                        seen_rot.add(key)
                        rotation_centers.append((cx, cy))

    # --- GENERATE GLIDE REFLECTION AXES ---
    glide_axes = []
    seen_axes = set()

    for idx, glide in enumerate(glide_seeds):
        px, py = glide["point"]
        dx, dy = glide["dir"]

        # Parallel lines shift by the *other* glide translation vector
        shift_v = t2 if idx == 0 else t1

        # For unique tracking, compute line normal vector
        nx, ny = -dy, dx
        mag = math.sqrt(nx * nx + ny * ny)
        nx, ny = nx / mag, ny / mag

        for k in range(-max_steps_1, max_steps_1 + 1 if idx == 1 else max_steps_2 + 1):
            # Shift the anchor point perpendicularly
            lx = px + k * shift_v[0]
            ly = py + k * shift_v[1]

            # Distance from origin along the normal uniquely identifies this parallel line
            axis_key = (idx, round(lx * nx + ly * ny, 4))
            if axis_key in seen_axes:
                continue

            segment = get_bounded_line(lx, ly, dx, dy)
            if segment:
                seen_axes.add(axis_key)
                glide_axes.append(segment)

    return rotation_centers, glide_axes


def ceil_div(a, b):
    return -(-a // b)


def render_coloured_tile(vertices, edges, identifications, tolerance, renderer):
    """Render a single tile with its octagon/square faces filled in, cropped to its own footprint."""
    tiling = caleidoscope.Pattern(
        vertices=vertices,
        edges=edges,
        polygons=[
            ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], "octagon"),
            ([0, 1, 8, 9], "square"),
        ],
        center=vertices[10],
        tolerance=tolerance,
        identifications=identifications,
    )
    cp = tiling.construct(width=16, height=16)
    return cp.render(
        renderer=renderer,
        edge_filter=lambda edge, tile: edge[2] == "s2",
        margin=2,
    )


def interpolated_vertices(start, end, percentage):
    """Interpolate between two sets of vertices."""
    return [
        (
            start[i][0] + percentage * (end[i][0] - start[i][0]),
            start[i][1] + percentage * (end[i][1] - start[i][1]),
        )
        for i in range(len(start))
    ]


def get_rescaling_between_tilings(t1, t2):
    t1_glide_1_magnitude = math.hypot(
        *t1.generators[2].classify().parameters["glide_vector"]
    )
    t1_glide_2_magnitude = math.hypot(
        *t1.generators[3].classify().parameters["glide_vector"]
    )
    t2_glide_1_magnitude = math.hypot(
        *t2.generators[2].classify().parameters["glide_vector"]
    )
    t2_glide_2_magnitude = math.hypot(
        *t2.generators[3].classify().parameters["glide_vector"]
    )

    return caleidoscope.Transform2D.from_orthogonal_scaling(
        t1.generators[2].classify().parameters["axis_direction"],
        t2_glide_1_magnitude / t1_glide_1_magnitude,
        t1.generators[3].classify().parameters["axis_direction"],
        t2_glide_2_magnitude / t1_glide_2_magnitude,
    )


def build_reference_tiling(vertices, edges, identifications, tolerance):
    """
    Build a Pattern from vertices (whose center is at index 10) and extract
    the pivots of its three independent rotation generators.

    This is not a general function: it assumes the first two generators are
    rotations and the third, composed with itself and the second, gives the
    third rotation. This matches create_alignment_rotation's assumption and
    is specific to the tilings in this example.
    """
    tiling = caleidoscope.Pattern(
        vertices=vertices,
        edges=edges,
        polygons=[],
        center=vertices[10],
        tolerance=tolerance,
        identifications=identifications,
    )
    rotations = [
        tiling.generators[1],
        tiling.generators[0],
        tiling.generators[0].compose(tiling.generators[2]).compose(tiling.generators[2]),
    ]
    rotation_centers = [r.classify().parameters["pivot"] for r in rotations]
    return tiling, rotation_centers


def create_alignment_rotation(tiling_from, tiling_to):
    """
    Create a rotation that aligns tiling_from to tiling_to.

    This is done by first rescaling tiling_from to match the
    glide vector magnitudes of tiling_to, then finding the rotation
    that aligns the rotation centers, and finally applying the inverse
    rescaling to the rotation pivot to get the correct final rotation.

    This is not a general function, and uses the specific structure of the
    tilings in this example, which have the same number of generators and
    the same types of symmetries in the same order. It also assumes that the
    first two generators are rotations and the next two are glide reflections,
    which is true for the tilings in this example but definitely not true in
    general.
    """
    rescaling = get_rescaling_between_tilings(tiling_from, tiling_to)
    rescaling_inverse = get_rescaling_between_tilings(tiling_to, tiling_from)

    vertices_from_rescaled = [rescaling.apply(v) for v in tiling_from.vertices]

    tiling_from_rescaled = caleidoscope.Pattern(
        vertices=vertices_from_rescaled,
        edges=tiling_from.edges,
        polygons=[],
        center=(0, 0),
        tolerance=0.05,
        identifications=tiling_from.identifications,
    )

    # Rotation
    from_rot1 = tiling_from_rescaled.generators[0].classify()
    from_rot2 = tiling_from_rescaled.generators[1].classify()
    from_rot3 = (
        tiling_from_rescaled.generators[2]
        .compose(tiling_from_rescaled.generators[2])
        .compose(tiling_from_rescaled.generators[1])
        .classify()
    )
    to_rot1 = tiling_to.generators[0].classify()
    to_rot2 = tiling_to.generators[1].classify()
    to_rot3 = (
        tiling_to.generators[2]
        .compose(tiling_to.generators[2])
        .compose(tiling_to.generators[1])
        .classify()
    )
    rot = caleidoscope.Transform2D.from_two_triplets(
        (
            from_rot1.parameters["pivot"],
            from_rot2.parameters["pivot"],
            from_rot3.parameters["pivot"],
        ),
        (
            to_rot1.parameters["pivot"],
            to_rot2.parameters["pivot"],
            to_rot3.parameters["pivot"],
        ),
    )
    rot_angle = rot.classify().parameters["angle_rad"]
    rot_pivot = rot.classify().parameters["pivot"]

    # Apply the inverse scaling to the pivot
    new_rot_pivot = rescaling_inverse.apply(rot_pivot)
    return caleidoscope.Transform2D.rotate(
        rot_angle, new_rot_pivot[0], new_rot_pivot[1]
    )


def main():

    # the hexagon that forms the basis of the midpoint tiling
    hexagon = [
        polar_to_cartesian(1, 5 * math.pi / 3),  # 0
        (1, 0),  # 1
        polar_to_cartesian(1, math.pi / 3),  # 2
        polar_to_cartesian(1, 2 * math.pi / 3),  # 3
        (-1, 0),  # 4
        polar_to_cartesian(1, 4 * math.pi / 3),  # 5
    ]

    # the ten vertices of the base tile
    midpoint_vertices = [
        hexagon[0],  # 0
        midpoint(hexagon[0], hexagon[1]),  # 1
        hexagon[1],  # 2
        hexagon[2],  # 3
        midpoint(hexagon[2], hexagon[3]),  # 4
        hexagon[3],  # 5
        midpoint(hexagon[3], hexagon[4]),  # 6
        hexagon[4],  # 7
        midpoint(hexagon[4], hexagon[5]),  # 8
        hexagon[5],  # 9
        (0, 0.25),  # 10, the center point of the octagon
        barycenter(
            [
                midpoint(hexagon[0], hexagon[1]),
                midpoint(hexagon[4], hexagon[5]),
                hexagon[0],
                hexagon[5],
            ]
        ),  # 11, the center point of the quadrangle
    ]

    midpoint_vertices += [
        # octagon edge midpoints
        midpoint(midpoint_vertices[1], midpoint_vertices[2]),  # 12
        midpoint(midpoint_vertices[2], midpoint_vertices[3]),  # 13
        midpoint(midpoint_vertices[3], midpoint_vertices[4]),  # 14
        midpoint(midpoint_vertices[4], midpoint_vertices[5]),  # 15
        midpoint(midpoint_vertices[5], midpoint_vertices[6]),  # 16
        midpoint(midpoint_vertices[6], midpoint_vertices[7]),  # 17
        midpoint(midpoint_vertices[7], midpoint_vertices[8]),  # 18
        midpoint(midpoint_vertices[8], midpoint_vertices[1]),  # 19
        # quadrangle edge midpoints
        # 19
        midpoint(midpoint_vertices[0], midpoint_vertices[1]),  # 20
        midpoint(midpoint_vertices[8], midpoint_vertices[9]),  # 21
        midpoint(midpoint_vertices[9], midpoint_vertices[0]),  # 22
    ]

    tolerance = 0.05

    edges = [
        (0, 1, "s2"),
        (1, 2, "s2"),
        (2, 3, "s2"),
        (3, 4, "s2"),
        (4, 5, "s2"),
        (5, 6, "s2"),
        (6, 7, "s2"),
        (7, 8, "s2"),
        (8, 9, "s2"),
        (9, 0, "s2"),
        (1, 8, "s2"),
        (10, 1, "s1"),
        (10, 2, "s1"),
        (10, 3, "s1"),
        (10, 4, "s1"),
        (10, 5, "s1"),
        (10, 6, "s1"),
        (10, 7, "s1"),
        (10, 8, "s1"),
        (11, 0, "s1"),
        (11, 1, "s1"),
        (11, 8, "s1"),
        (11, 9, "s1"),
        (10, 12, "s0"),
        (10, 13, "s0"),
        (10, 14, "s0"),
        (10, 15, "s0"),
        (10, 16, "s0"),
        (10, 17, "s0"),
        (10, 18, "s0"),
        (10, 19, "s0"),
        (11, 19, "s0"),
        (11, 20, "s0"),
        (11, 21, "s0"),
        (11, 22, "s0"),
    ]

    # All identifications below are correct, but some are superfluous: the
    # commented-out ones are implied by the others. The active ones form a
    # minimal generating set.
    identifications = [
        ((9, 0), (0, 9), True),  # 180 degrees rotation
        ((2, 3), (3, 2), True),  # 180 degrees rotation
        ((6, 7), (1, 2), False),  # glide reflection
        # ((5, 6), (0, 1), False),  # glide reflection
        ((4, 5), (8, 9), False),  # glide reflection
        # ((0, 1), (5, 6), False),  # glide reflection
        # ((1, 2), (6, 7), False),  # glide reflection
        # ((3, 4), (7, 8), False),  # glide reflection
        # ((7, 8), (3, 4), False),  # glide reflection
        # ((8, 9), (4, 5), False),  # glide reflection
    ]

    midpoint_tiling, midpoint_rotation_centers = build_reference_tiling(
        midpoint_vertices, edges, identifications, tolerance
    )

    ############################################################################
    # We now construct the starting tile                                       #
    ############################################################################

    # the ten vertices of the base tile
    vertices_starting_point = [
        (1, 0),  # 0
        (1, 0.25),  # 1
        (1, 0.5),  # 2
        (0, 0.5),  # 3
        (-0.25, 0.5),  # 4
        (-0.5, 0.5),  # 5
        (-0.75, 0.5),  # 6
        (-1, 0.5),  # 7
        (-1, 0.25),  # 8
        (-1, 0),  # 9
        (0, 0.375),  # 10, the center point of the octagon
        (0, 0.125),  # 11, the center point of the quadrangle
    ]

    vertices_starting_point += [
        # octagon edge midpoints
        midpoint(vertices_starting_point[1], vertices_starting_point[2]),  # 12
        midpoint(vertices_starting_point[2], vertices_starting_point[3]),  # 13
        midpoint(vertices_starting_point[3], vertices_starting_point[4]),  # 14
        midpoint(vertices_starting_point[4], vertices_starting_point[5]),  # 15
        midpoint(vertices_starting_point[5], vertices_starting_point[6]),  # 16
        midpoint(vertices_starting_point[6], vertices_starting_point[7]),  # 17
        midpoint(vertices_starting_point[7], vertices_starting_point[8]),  # 18
        midpoint(vertices_starting_point[8], vertices_starting_point[1]),  # 19
        # quadrangle edge midpoints
        # 19
        midpoint(vertices_starting_point[0], vertices_starting_point[1]),  # 20
        midpoint(vertices_starting_point[8], vertices_starting_point[9]),  # 21
        midpoint(vertices_starting_point[9], vertices_starting_point[0]),  # 22
    ]

    # Rescale (x2) and shift so the octagon center (vertex 10) lands at the
    # same point as midpoint_vertices[10], roughly matching scale and
    # position before we compute an exact aligning transform below.
    vertices_starting_point = [
        (2 * x, 2 * (y - 0.25)) for (x, y) in vertices_starting_point
    ]

    starting_point_tiling, starting_point_rotation_centers = build_reference_tiling(
        vertices_starting_point, edges, identifications, tolerance
    )

    tf = caleidoscope.Transform2D.from_two_triplets(
        tuple(starting_point_rotation_centers), tuple(midpoint_rotation_centers)
    )
    vertices_starting_point_aligned = [tf.apply(v) for v in vertices_starting_point]

    starting_point_tiling_aligned = caleidoscope.Pattern(
        vertices=vertices_starting_point_aligned,
        edges=edges,
        polygons=[],
        center=vertices_starting_point_aligned[10],
        tolerance=0.05,
        identifications=identifications,
    )

    # We cannot just interpolate between starting_point_tiling and starting_point_tiling_aligned
    # because the intermediate states would not align with the symmetries.
    # The transformation between the two can be decomposed into a pure rescaling along the symmetry axes,
    # and a rotation.
    starting_point_rotation = create_alignment_rotation(
        starting_point_tiling, midpoint_tiling
    )

    vertices_starting_point_rotated = [
        starting_point_rotation.apply(v) for v in vertices_starting_point
    ]
    starting_point_tiling_rotated = caleidoscope.Pattern(
        vertices=vertices_starting_point_rotated,
        edges=edges,
        polygons=[],
        center=vertices_starting_point_rotated[10],
        tolerance=0.05,
        identifications=identifications,
    )

    # starting_point_tiling_rotated is now the new starting point

    ############################################################################
    # We now construct the end tile                                            #
    ############################################################################

    # the ten vertices of the base tile
    vertices_end_point = [
        (2, 0),  # 0
        (2, 3),  # 1
        (3, 3),  # 2
        (6, 3),  # 3
        (6, 4),  # 4
        (3, 4),  # 5
        (0, 4),  # 6
        (0, 3),  # 7
        (1, 3),  # 8
        (1, 0),  # 9
    ]

    vertices_end_point += [
        barycenter(
            [vertices_end_point[i] for i in (3, 4, 6, 7)]
        ),  # 10, the center point of the octagon
        barycenter(
            vertices_end_point[0:2] + vertices_end_point[8:10]
        ),  # 11, the center point of the quadrangle
    ]
    vertices_end_point += [
        # octagon edge midpoints
        midpoint(vertices_end_point[1], vertices_end_point[2]),  # 12
        midpoint(vertices_end_point[2], vertices_end_point[3]),  # 13
        midpoint(vertices_end_point[3], vertices_end_point[4]),  # 14
        midpoint(vertices_end_point[4], vertices_end_point[5]),  # 15
        midpoint(vertices_end_point[5], vertices_end_point[6]),  # 16
        midpoint(vertices_end_point[6], vertices_end_point[7]),  # 17
        midpoint(vertices_end_point[7], vertices_end_point[8]),  # 18
        midpoint(vertices_end_point[8], vertices_end_point[1]),  # 19
        # quadrangle edge midpoints
        # 19
        midpoint(vertices_end_point[0], vertices_end_point[1]),  # 20
        midpoint(vertices_end_point[8], vertices_end_point[9]),  # 21
        midpoint(vertices_end_point[9], vertices_end_point[0]),  # 22
    ]

    end_point_tiling, end_point_rotation_centers = build_reference_tiling(
        vertices_end_point, edges, identifications, tolerance
    )

    tf = caleidoscope.Transform2D.from_two_triplets(
        tuple(end_point_rotation_centers), tuple(midpoint_rotation_centers)
    )
    vertices_end_point_aligned = [tf.apply(v) for v in vertices_end_point]

    end_point_tiling_aligned = caleidoscope.Pattern(
        vertices=vertices_end_point_aligned,
        edges=edges,
        polygons=[],
        center=vertices_end_point_aligned[10],
        tolerance=0.05,
        identifications=identifications,
    )

    # We cannot just interpolate between end_point_tiling and end_point_tiling_aligned
    # because the intermediate states would not align with the symmetries.
    # The transformation between the two can be decomposed into a pure rescaling along the symmetry axes,
    # and a rotation.
    end_point_rotation = create_alignment_rotation(end_point_tiling, midpoint_tiling)

    vertices_end_point_rotated = [
        end_point_rotation.apply(v) for v in vertices_end_point
    ]
    end_point_tiling_rotated = caleidoscope.Pattern(
        vertices=vertices_end_point_rotated,
        edges=edges,
        polygons=[],
        center=vertices_end_point_rotated[10],
        tolerance=0.05,
        identifications=identifications,
    )

    # end_point_tiling_rotated is now the new end point

    steps = 49
    alignment_steps = 10
    interpolated_tilings_start_to_midpoint = [
        caleidoscope.Pattern(
            interpolated_vertices(
                vertices_starting_point_aligned, midpoint_vertices, p / steps
            ),
            edges,
            [],
            interpolated_vertices(
                vertices_starting_point_aligned, midpoint_vertices, p / steps
            )[10],
            tolerance,
            identifications,
        )
        for p in range(1, steps)
    ]
    # Rescaling the starting point to match the scale of the midpoint
    alignment_tilings_starting_point = [
        caleidoscope.Pattern(
            interpolated_vertices(
                vertices_starting_point_rotated,
                vertices_starting_point_aligned,
                p / alignment_steps,
            ),
            edges,
            [],
            interpolated_vertices(
                vertices_starting_point_rotated,
                vertices_starting_point_aligned,
                p / alignment_steps,
            )[10],
            tolerance,
            identifications,
        )
        for p in range(1, alignment_steps)
    ]

    interpolated_tilings_midpoint_to_end = [
        caleidoscope.Pattern(
            interpolated_vertices(
                midpoint_vertices, vertices_end_point_aligned, p / steps
            ),
            edges,
            [],
            interpolated_vertices(
                midpoint_vertices, vertices_end_point_aligned, p / steps
            )[10],
            tolerance,
            identifications,
        )
        for p in range(1, steps)
    ]
    alignment_tilings_end_point = [
        caleidoscope.Pattern(
            interpolated_vertices(
                vertices_end_point_aligned,
                vertices_end_point_rotated,
                p / alignment_steps,
            ),
            edges,
            [],
            interpolated_vertices(
                vertices_end_point_aligned,
                vertices_end_point_rotated,
                p / alignment_steps,
            )[10],
            tolerance,
            identifications,
        )
        for p in range(1, alignment_steps)
    ]

    def construct_tiling_renderer(draw_barycenter: bool, draw_symmetry_elements: bool):
        def render_tiling(
            tiling: caleidoscope.Pattern, renderer: caleidoscope.TikzRenderer
        ) -> str:
            cp = tiling.construct(width=16, height=16)
            gs = tiling.generators
            rots, axes = generate_pgg_symmetries_simple(
                [g.classify() for g in gs], (-8, -8, 8, 8)
            )
            return (
                (
                    cp.render(
                        renderer,
                        lambda edge, _: len(edge) == 3 and edge[2] in ["s0", "s1"],
                    )
                    if draw_barycenter
                    else ""
                )
                + cp.render(
                    renderer, lambda edge, _: len(edge) == 3 and edge[2] in ["s2"]
                )
                + (
                    "\n".join(
                        [
                            f"  \\node[fill=blue, circle, inner sep=1pt] at ({c[0]:.3f}, {c[1]:.3f}) {{}};"
                            for c in rots
                        ]
                        + [
                            f"  \\draw[blue, thick, dotted] ({a[0][0]:.3f}, {a[0][1]:.3f}) -- ({a[1][0]:.3f}, {a[1][1]:.3f});"
                            for a in axes
                        ]
                    )
                    if draw_symmetry_elements
                    else ""
                )
            )

        return render_tiling

    OUTPUT_DIR.mkdir(exist_ok=True)

    renderer = caleidoscope.TikzRenderer(
        {
            "s0": "green, ultra thin",
            "s1": "red, ultra thin",
            "s2": "black, thick",
        }
    )

    # align: include the rotation/rescale transition frames at each end,
    # not to be confused with the "_aligned" tilings, which are always included.
    for bary, symm, align in itertools.product([True, False], repeat=3):
        tiling_renderer = construct_tiling_renderer(
            draw_barycenter=bary, draw_symmetry_elements=symm
        )

        path = (
            OUTPUT_DIR
            / f"animation{'_bary' if bary else ''}{'_symm' if symm else ''}{'_align' if align else ''}.tex"
        )
        tilings = (
            (
                [starting_point_tiling_rotated] + alignment_tilings_starting_point
                if align
                else []
            )
            + [starting_point_tiling_aligned]
            + interpolated_tilings_start_to_midpoint
            + [midpoint_tiling]
            + interpolated_tilings_midpoint_to_end
            + [end_point_tiling_aligned]
            + (
                alignment_tilings_end_point + [end_point_tiling_rotated]
                if align
                else []
            )
        )
        write_standalone_tex(
            path,
            "\n\n".join(
                [
                    wrap_tikz_picture(tiling_renderer(tiling, renderer))
                    for tiling in tilings
                ]
            ),
        )

    coloured_renderer = caleidoscope.TikzRenderer(
        {
            "s2": "black, thick",
            "square": "fill=teal",
            "octagon": "fill=orange",
        }
    )

    coloured_tilings_input = [
        ("starting_tiling_coloured.tex", vertices_starting_point_rotated),
        ("end_tiling_coloured.tex", [(x / 1.5, y / 1.5) for (x, y) in vertices_end_point_rotated]),
        ("starting_tiling_coloured_aligned.tex", vertices_starting_point_aligned),
        ("end_tiling_coloured_aligned.tex", vertices_end_point_aligned),
        ("mid_tiling_coloured.tex", midpoint_vertices),
    ]

    for filename, vertices in coloured_tilings_input:
        write_standalone_tex(
            OUTPUT_DIR / filename,
            wrap_tikz_picture(
                render_coloured_tile(vertices, edges, identifications, 0.05, coloured_renderer)
            ),
        )

    uncoloured_tilings_input = [
        ("uncoloured_starting_tiling.tex", vertices_starting_point_rotated),
        ("uncoloured_end_tiling.tex", [(x / 1.5, y / 1.5) for (x, y) in vertices_end_point_rotated]),
        ("uncoloured_starting_tiling_aligned.tex", vertices_starting_point_aligned),
        ("uncoloured_end_tiling_aligned.tex", vertices_end_point_aligned),
        ("uncoloured_mid_tiling.tex", midpoint_vertices),
    ]

    for filename, vertices in uncoloured_tilings_input:
        pattern = caleidoscope.Pattern(
            vertices=vertices,
            edges=edges,
            polygons=[],
            center=vertices[10],
            tolerance=0.05,
            identifications=identifications,
        )
        write_standalone_tex(
            OUTPUT_DIR / filename,
            wrap_tikz_picture(
                pattern.render(renderer, margin=2, edge_filter=lambda edge, _: edge[2] == "s2", width=16, height=16)
            ),
        )


if __name__ == "__main__":
    main()
