# Inverse Generators Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `Pattern` also composes the inverses of its generators by default (fixing issue #3), with `include_inverses=False` reproducing the old behaviour exactly.

**Architecture:** Two small `Transform2D` methods (`inverse`, `is_close`) support a keyword-only `include_inverses` flag on `Pattern`, which appends non-duplicate inverses after the original generators. The p31m construction modes opt out to keep their externally referenced tile order; the wallpaper example drops its own workaround. A before/after snapshot of every example's output guards against unintended changes.

**Tech Stack:** Python ≥ 3.13, uv workspace, pytest, Pillow (for comparing PNGs).

**Spec:** `docs/superpowers/specs/2026-10-03-inverse-generators-design.md`

## Global Constraints

- Requires Python >= 3.13; never call system `python` — always `uv run ...` from the repository root.
- `include_inverses` is keyword-only, default `True`; with `False`, generators, construction order and generator sequences are exactly as before.
- Inverses are appended after the original generators, in the same order; an inverse that `is_close` to a generator already in the list is skipped.
- `Transform2D.is_close` default tolerance: `1e-9`. `Transform2D.inverse` raises `ValueError` for a singular matrix.
- p31m: `include_inverses=False` only in `render_tiling_construction_frames` and `render_tiling_construction_beamer_frames`; p31m construction `.tex` outputs must be byte-identical before/after.
- Commit messages: `<type>(<scope>): <subject>`, subject ≤ 50 chars, imperative, no period; reference `#3` in the footer where relevant; end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Work on branch `fix/inverse-generators` (already checked out; contains the spec commit). Never push or fetch.
- Never commit generated output (`examples/*/output/`) or anything under `.superpowers/`.
- Regression tooling and snapshots live outside the repo, in `SCRATCH=/tmp/claude-1000/-home-nvcleemp-projecten-tilings-caleidoscope/6d0b0586-cddd-4a8a-bfde-058db64f6581/scratchpad/regression`.

---

### Task 1: Regression baseline and `Transform2D.inverse` / `is_close`

**Files:**
- Create (outside repo): `$SCRATCH/snapshot.sh`, `$SCRATCH/compare.py`
- Modify: `libs/caleidoscope/src/caleidoscope/affinetransformation.py` (add two methods to `Transform2D`, after `compose`)
- Test: `libs/caleidoscope/tests/test_transform2d.py` (append)

**Interfaces:**
- Consumes: `Transform2D(matrix)` (3×3 nested lists, last row `[0, 0, 1]`), `Transform2D.compose(other)` (applies `other` first), `Transform2D.rotate(angle, px, py)`, `Transform2D.translate(dx, dy)`, `Transform2D.reflect_x()`.
- Produces: `Transform2D.inverse() -> Transform2D`; `Transform2D.is_close(other: Transform2D, tolerance: float = 1e-9) -> bool`; baseline snapshots `$SCRATCH/before` and `$SCRATCH/before2`.

- [ ] **Step 1: Create the regression tooling**

`$SCRATCH/snapshot.sh` (make it executable with `chmod +x`):

```bash
#!/usr/bin/env bash
# Usage (from the repository root): snapshot.sh DEST
# Runs every `run-*` Makefile target, saving its stdout/stderr, and copies
# every example output file written during this run into DEST/files.
set -euo pipefail
dest=$1
rm -rf "$dest"
mkdir -p "$dest/stdout" "$dest/files"
marker=$(mktemp)
for target in $(grep -oE '^run-[a-z0-9-]+' Makefile); do
    make -s "$target" > "$dest/stdout/$target.txt" 2>&1
done
find examples -path '*/output/*' -type f -newer "$marker" | while read -r f; do
    mkdir -p "$dest/files/$(dirname "$f")"
    cp "$f" "$dest/files/$f"
done
rm -f "$marker"
```

`$SCRATCH/compare.py`:

```python
"""Compare two snapshot directories; print one line per file that differs.

Usage: uv run --package caleidoscope python compare.py BEFORE AFTER
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops


def files(root: Path) -> set[Path]:
    return {p.relative_to(root) for p in root.rglob("*") if p.is_file()}


def main() -> None:
    before, after = Path(sys.argv[1]), Path(sys.argv[2])
    for rel in sorted(files(before) | files(after)):
        a, b = before / rel, after / rel
        if not a.exists():
            print(f"ONLY-AFTER {rel}")
        elif not b.exists():
            print(f"ONLY-BEFORE {rel}")
        elif a.read_bytes() == b.read_bytes():
            continue
        elif rel.suffix == ".png":
            image_a = Image.open(a).convert("RGBA")
            image_b = Image.open(b).convert("RGBA")
            if image_a.size != image_b.size:
                print(f"PNG-SIZE {rel} {image_a.size} -> {image_b.size}")
                continue
            difference = ImageChops.difference(image_a, image_b)
            changed = sum(1 for pixel in difference.getdata() if pixel != (0, 0, 0, 0))
            print(f"PNG-PIXELS {rel} {changed} of {image_a.size[0] * image_a.size[1]} pixels differ")
        else:
            lines_a = a.read_text().splitlines()
            lines_b = b.read_text().splitlines()
            kind = "TEXT-REORDERED" if sorted(lines_a) == sorted(lines_b) else "TEXT-CHANGED"
            print(f"{kind} {rel} ({len(lines_a)} -> {len(lines_b)} lines)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Capture the baseline twice (before any code change)**

Confirm the working tree is clean (`git status --short` prints nothing), then run:

```bash
SCRATCH=/tmp/claude-1000/-home-nvcleemp-projecten-tilings-caleidoscope/6d0b0586-cddd-4a8a-bfde-058db64f6581/scratchpad/regression
$SCRATCH/snapshot.sh $SCRATCH/before
$SCRATCH/snapshot.sh $SCRATCH/before2
uv run --package caleidoscope python $SCRATCH/compare.py $SCRATCH/before $SCRATCH/before2
```

Expected: the compare prints nothing (all examples deterministic). If it prints lines, record them in the report: those files are nondeterministic and later differences in them must be discounted. Use generous timeouts (the full run can take several minutes).

- [ ] **Step 3: Write the failing tests**

Append to `libs/caleidoscope/tests/test_transform2d.py`:

```python
@pytest.mark.parametrize(
    "transform",
    [
        Transform2D.rotate(1.0, 2.0, 3.0),
        Transform2D.translate(1.0, -2.0),
        # (x, y) -> (x + 1, 1 - y): a glide reflection.
        Transform2D.translate(1.0, 1.0).compose(Transform2D.reflect_x()),
    ],
)
def test_inverse_composes_to_identity(transform: Transform2D) -> None:
    assert transform.compose(transform.inverse()).is_close(Transform2D())
    assert transform.inverse().compose(transform).is_close(Transform2D())


def test_inverse_of_singular_matrix_raises() -> None:
    singular = Transform2D([[1.0, 2.0, 0.0], [2.0, 4.0, 0.0], [0.0, 0.0, 1.0]])
    with pytest.raises(ValueError):
        singular.inverse()


def test_is_close_within_tolerance() -> None:
    a = Transform2D.translate(1.0, 2.0)
    assert a.is_close(Transform2D.translate(1.0 + 1e-12, 2.0))
    assert not a.is_close(Transform2D.translate(1.0 + 1e-6, 2.0))
    assert a.is_close(Transform2D.translate(1.0 + 1e-6, 2.0), tolerance=1e-5)
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `uv run --package caleidoscope pytest libs/caleidoscope/tests/test_transform2d.py -v`
Expected: the new tests FAIL with `AttributeError: 'Transform2D' object has no attribute 'is_close'` / `'inverse'`.

- [ ] **Step 5: Implement**

In `libs/caleidoscope/src/caleidoscope/affinetransformation.py`, add to `Transform2D` directly after `compose`:

```python
    def inverse(self) -> "Transform2D":
        """
        Return the inverse transformation.

        Returns:
            A new Transform2D that undoes this one.

        Raises:
            ValueError: If the transformation is not invertible.
        """
        (a, b, tx), (c, d, ty) = self.matrix[0], self.matrix[1]
        det = a * d - b * c
        if abs(det) < 1e-12:
            raise ValueError("Transformation is not invertible")
        ia, ib = d / det, -b / det
        ic, id_ = -c / det, a / det
        return Transform2D([
            [ia, ib, -(ia * tx + ib * ty)],
            [ic, id_, -(ic * tx + id_ * ty)],
            [0.0, 0.0, 1.0],
        ])

    def is_close(self, other: "Transform2D", tolerance: float = 1e-9) -> bool:
        """
        Check whether two transformations are equal up to a tolerance.

        Args:
            other: Another Transform2D instance.
            tolerance: Maximum allowed difference per affine matrix entry.

        Returns:
            True if all six affine entries differ by at most `tolerance`.
        """
        return all(
            abs(self.matrix[i][j] - other.matrix[i][j]) <= tolerance
            for i in range(2)
            for j in range(3)
        )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run --package caleidoscope pytest -v`
Expected: all library tests PASS (128 existing + 5 new = 133).

- [ ] **Step 7: Commit**

```bash
git add libs/caleidoscope/src/caleidoscope/affinetransformation.py libs/caleidoscope/tests/test_transform2d.py
git commit -m "feat(transform): add inverse and is_close

Refs #3

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: `Pattern(include_inverses=...)`, p31m opt-out, README

**Files:**
- Modify: `libs/caleidoscope/src/caleidoscope/pattern.py` (`__init__`, `generators`)
- Modify: `libs/caleidoscope/tests/test_pattern.py` (update one assertion, append tests)
- Modify: `examples/p31m_tiling/main.py` (the two construction functions)
- Modify: `README.md` (one paragraph after the square example)

**Interfaces:**
- Consumes: `Transform2D.inverse()`, `Transform2D.is_close(other)` from Task 1; `$SCRATCH/snapshot.sh`, `$SCRATCH/compare.py`, `$SCRATCH/before` from Task 1.
- Produces: `Pattern(vertices, edges, polygons, center, tolerance, identifications, *, include_inverses: bool = True)`; `Pattern.include_inverses` attribute; `Pattern.generators` = originals followed by non-duplicate inverses.

- [ ] **Step 1: Write the failing tests**

In `libs/caleidoscope/tests/test_pattern.py`, `test_generators_are_lazily_computed` currently asserts `len(generators) == 1` for a single translation; with inverses that becomes 2. Replace that assertion line with:

```python
    assert len(generators) == 2  # the translation and its inverse
```

Append to the same file:

```python
def _readme_square(**kwargs: bool) -> Pattern:
    """The square example from the README: left/right and bottom/top edges
    identified by translations."""
    vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    edges = [(0, 1, "bottom"), (1, 2, "right"), (2, 3, "top"), (3, 0, "left")]
    identifications = [((0, 3), (1, 2), True), ((0, 1), (3, 2), True)]
    return Pattern(
        vertices, edges, [], center=(0.5, 0.5), tolerance=0.01,
        identifications=identifications, **kwargs,
    )


def test_translations_fill_the_whole_region_by_default() -> None:
    assert _readme_square().construct(0, 0, 6, 6).tile_count == 36


def test_include_inverses_false_keeps_only_the_given_generators() -> None:
    pattern = _readme_square(include_inverses=False)
    assert len(pattern.generators) == 2
    assert pattern.construct(0, 0, 6, 6).tile_count == 9


def test_inverses_are_appended_after_the_original_generators() -> None:
    original = _readme_square(include_inverses=False).generators
    generators = _readme_square().generators
    assert len(generators) == 4
    for generator, expected in zip(generators[:2], original):
        assert generator.is_close(expected)
    for generator, expected in zip(generators[2:], original):
        assert generator.is_close(expected.inverse())


def test_self_inverse_generators_are_not_duplicated() -> None:
    mirrors = [
        ((0, 1), (0, 1), False),
        ((1, 2), (1, 2), False),
        ((3, 2), (3, 2), False),
        ((0, 3), (0, 3), False),
    ]
    assert len(_square_pattern(mirrors).generators) == 4


def test_reverse_identification_given_by_caller_is_not_duplicated() -> None:
    both_directions = [((0, 3), (1, 2), True), ((1, 2), (0, 3), True)]
    assert len(_square_pattern(both_directions).generators) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --package caleidoscope pytest libs/caleidoscope/tests/test_pattern.py -v`
Expected: FAIL — `test_generators_are_lazily_computed` (`assert 1 == 2`), the `_readme_square` tests (`TypeError: ... unexpected keyword argument 'include_inverses'` or wrong counts).

- [ ] **Step 3: Implement**

In `libs/caleidoscope/src/caleidoscope/pattern.py`:

Change the end of the `__init__` signature from

```python
                 identifications: list[tuple[tuple[int, int], tuple[int, int], bool]]
                ):
```

to

```python
                 identifications: list[tuple[tuple[int, int], tuple[int, int], bool]],
                 *,
                 include_inverses: bool = True
                ):
```

Add to the `Args:` section of its docstring, after `identifications`:

```
            include_inverses: If True (the default), the inverse of every generator
                           is also used as a generator (appended after the original
                           ones, skipping inverses that equal an existing generator),
                           so e.g. a translation tiles in both directions. If False,
                           only the generators derived from the identifications are
                           used, which reproduces the construction order of earlier
                           versions.
```

Store it next to the other attributes (after `self.identifications = identifications`):

```python
        self.include_inverses = include_inverses
```

Replace the body of the `generators` property's `if self._generators is None:` block with:

```python
        if self._generators is None:
            generators = [
                Transform2D.from_two_segments(
                    self.vertices[f[0]],
                    self.vertices[f[1]],
                    self.vertices[t[0]],
                    self.vertices[t[1]],
                    keep_orientation=o,
                )
                for f, t, o in self.identifications
            ]
            if self.include_inverses:
                for generator in list(generators):
                    inverse = generator.inverse()
                    if not any(inverse.is_close(other) for other in generators):
                        generators.append(inverse)
            self._generators = generators
```

and update the property docstring's first paragraph to: "Generators are computed from the identifications on first access and cached for subsequent calls. With `include_inverses`, their inverses follow them in the same order, skipping any inverse that equals an earlier generator."

- [ ] **Step 4: Run library tests**

Run: `uv run --package caleidoscope pytest -v`
Expected: all PASS (133 + 5 new = 138). If any test other than the ones in Step 1 fails, do not edit it — report it (DONE_WITH_CONCERNS) with the failure output.

- [ ] **Step 5: Opt out in the p31m construction modes**

In `examples/p31m_tiling/main.py`, in both `render_tiling_construction_frames` and `render_tiling_construction_beamer_frames`, change the `caleidoscope.Pattern(...)` call by adding, after `identifications=domain.identifications,`:

```python
        # The tile numbering below follows construction order, which is
        # referred to in texts outside this repository: keep the original
        # generators only, so that order stays unchanged.
        include_inverses=False,
```

Do not change any other `Pattern(...)` call in this file.

- [ ] **Step 6: Document the flag in the README**

In `README.md`, directly after the square example's code block (the block ending with `tikz_code = pattern.render(TikzRenderer(), width=6, height=6)` and its closing fence), insert this paragraph (with a blank line before and after):

```markdown
The inverse of every generator is used as well, so the square above tiles in
all directions even though each identification only lists one direction.
Pass `include_inverses=False` to `Pattern` to use only the generators derived
from the identifications, as earlier versions did; this keeps the
construction order (and so the numbering of tiles in
`ConstructedPattern.get_tiles()`) the same as before.
```

- [ ] **Step 7: Regression comparison**

Run:

```bash
SCRATCH=/tmp/claude-1000/-home-nvcleemp-projecten-tilings-caleidoscope/6d0b0586-cddd-4a8a-bfde-058db64f6581/scratchpad/regression
$SCRATCH/snapshot.sh $SCRATCH/after-task2
uv run --package caleidoscope python $SCRATCH/compare.py $SCRATCH/before $SCRATCH/after-task2
```

Requirements (check each and put the full compare output in the report):
- No line may mention `examples/p31m_tiling/output/p31m_tiling_construction` (both the per-step and the `_beamer` files, for both domains): those must be byte-identical.
- No `ONLY-BEFORE` lines (no example lost an output).
- For every other reported file, explain the difference in the report: `TEXT-REORDERED` is expected where a pattern has non-self-inverse generators (rotations by less than 180°, glide reflections, translations) since the tile order changes; `PNG-PIXELS`/`TEXT-CHANGED` must be explained by looking at the files (e.g. more tiles now fill a region that was previously only partly tiled, or anti-aliasing at overlaps drawn in a different order). Do not try to make such differences go away by changing examples; report them.

- [ ] **Step 8: Commit**

```bash
git add libs/caleidoscope/src/caleidoscope/pattern.py libs/caleidoscope/tests/test_pattern.py examples/p31m_tiling/main.py README.md
git commit -m "fix(pattern): also compose inverse generators

Pattern now appends the inverse of each generator (skipping
duplicates), so translations tile in both directions. The new
include_inverses=False keeps the old behaviour; the p31m
construction modes use it to keep their tile order.

Fixes #3

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Remove the wallpaper example's workaround

**Files:**
- Modify: `examples/wallpaper_groups/construction.py`
- Modify: `examples/wallpaper_groups/tests/test_groups.py`

**Interfaces:**
- Consumes: `Pattern` with default `include_inverses=True` (Task 2); `$SCRATCH/snapshot.sh`, `$SCRATCH/compare.py`, `$SCRATCH/before`.
- Produces: `construction.construct_tiles(group)` unchanged in signature; `construction.with_inverses` removed.

- [ ] **Step 1: Remove the workaround**

In `examples/wallpaper_groups/construction.py`:
- delete the whole `with_inverses` function;
- in `construct_tiles`, change `identifications=with_inverses(group.identifications),` to `identifications=group.identifications,`;
- change `from groups import Identification, WallpaperGroup` to `from groups import WallpaperGroup` (confirm with `grep -n Identification examples/wallpaper_groups/construction.py` that nothing else uses it).

In `examples/wallpaper_groups/tests/test_groups.py`:
- change `from construction import construct_tiles, view_for, with_inverses` to `from construction import construct_tiles, view_for`;
- delete the whole `test_with_inverses_skips_self_gluings` function.

Leave `test_tiles_cover_view_corners` (and its comment about missing inverse generators) as is: it now checks the library behaviour.

(The example's README does not mention the workaround; nothing to change there.)

- [ ] **Step 2: Run the example tests**

Run: `uv run --package wallpaper-groups pytest examples/wallpaper_groups -v`
Expected: all PASS (78 − 1 removed = 77).

- [ ] **Step 3: Regression comparison**

Run:

```bash
SCRATCH=/tmp/claude-1000/-home-nvcleemp-projecten-tilings-caleidoscope/6d0b0586-cddd-4a8a-bfde-058db64f6581/scratchpad/regression
$SCRATCH/snapshot.sh $SCRATCH/after-task3
uv run --package caleidoscope python $SCRATCH/compare.py $SCRATCH/before $SCRATCH/after-task3
```

Requirements: no line mentions `examples/wallpaper_groups/output/` (the library's inverses equal the workaround's, in the same order, so the images are byte-identical); the remaining lines are the same as Task 2's compare output. Include the output in the report.

- [ ] **Step 4: Full test run**

Run: `uv run --locked --package caleidoscope pytest && uv run --package wallpaper-groups pytest examples/wallpaper_groups`
Expected: 138 passed; 77 passed.

- [ ] **Step 5: Commit**

```bash
git add examples/wallpaper_groups/construction.py examples/wallpaper_groups/tests/test_groups.py
git commit -m "refactor(wallpaper-groups): drop inverse workaround

Pattern now adds inverse generators itself (#3).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
