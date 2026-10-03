.PHONY: run-basic-classify run-basic-filtered-rendering run-basic-from-two-segments \
	run-basic-quadtree run-basic-transformation-tracking run-decoration \
	run-glue-and-split run-p31m-tiling run-two-tilings run-svg-decoration \
	run-png-decoration run-wallpaper-groups

run-basic-classify:
	uv run --package basic-examples python examples/basic/classify.py

run-basic-filtered-rendering:
	uv run --package basic-examples python examples/basic/filtered_rendering.py

run-basic-from-two-segments:
	uv run --package basic-examples python examples/basic/from_two_segments.py

run-basic-quadtree:
	uv run --package basic-examples python examples/basic/quadtree.py

run-basic-transformation-tracking:
	uv run --package basic-examples python examples/basic/transformation_tracking.py

run-decoration:
	uv run --package decoration python examples/decoration/main.py

run-glue-and-split:
	uv run --package glue-and-split python examples/glue_and_split/main.py

run-p31m-tiling:
	uv run --package p31m-tiling python examples/p31m_tiling/main.py

run-two-tilings:
	uv run --package two-tilings python examples/two_tilings/main.py

run-svg-decoration:
	uv run --package svg-decoration python examples/svg_decoration/main.py

run-png-decoration:
	uv run --package png-decoration python examples/png_decoration/main.py

run-wallpaper-groups:
	uv run --package wallpaper-groups python examples/wallpaper_groups/main.py
