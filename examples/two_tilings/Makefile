FPS ?= 12
DPI ?= 300
SCRIPT := ../../scripts/tex-to-video.sh

TEX_FILES := $(wildcard output/*.tex)
VIDEOS := $(TEX_FILES:.tex=.mp4)

.PHONY: videos clean-videos
videos: $(VIDEOS)

output/%.mp4: output/%.tex
	$(SCRIPT) $< $@ --fps $(FPS) --dpi $(DPI)

clean-videos:
	rm -f output/*.mp4
