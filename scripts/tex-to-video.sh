#!/usr/bin/env bash
# Compile a standalone multi-page TikZ .tex file (one page per animation
# frame) into an .mp4: latexmk -> PDF, pdftoppm -> PNG frames, ffmpeg -> video.
set -euo pipefail

usage() {
    cat >&2 <<EOF
Usage: $(basename "$0") <input.tex> [output.mp4] [--fps N] [--dpi N]

  input.tex    LaTeX file with one page per frame (e.g. \\documentclass[tikz]{standalone}).
  output.mp4   Defaults to <input>.mp4 next to the .tex file.
  --fps N      Frames per second (default: 12).
  --dpi N      Rasterization resolution for pdftoppm (default: 300).
EOF
    exit 1
}

fps=12
dpi=300
input=
output=

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fps)
            fps="$2"
            shift 2
            ;;
        --dpi)
            dpi="$2"
            shift 2
            ;;
        -h | --help)
            usage
            ;;
        *)
            if [[ -z "$input" ]]; then
                input="$1"
            elif [[ -z "$output" ]]; then
                output="$1"
            else
                usage
            fi
            shift
            ;;
    esac
done

[[ -z "$input" ]] && usage
[[ "$input" == *.tex ]] || {
    echo "error: input must be a .tex file" >&2
    exit 1
}
[[ -f "$input" ]] || {
    echo "error: no such file: $input" >&2
    exit 1
}

input="$(realpath "$input")"
tex_dir="$(dirname "$input")"
base="$(basename "$input" .tex)"
pdf="$tex_dir/$base.pdf"

output="${output:-$tex_dir/$base.mp4}"
mkdir -p "$(dirname "$output")"
output="$(realpath -m "$output")"

echo "Compiling $input..."
latexmk -pdf -interaction=nonstopmode -halt-on-error -output-directory="$tex_dir" "$input" >/dev/null

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

echo "Exporting pages to PNG at ${dpi}dpi..."
pdftoppm -png -r "$dpi" "$pdf" "$workdir/frame"

echo "Encoding video at ${fps}fps..."
ffmpeg -y -framerate "$fps" -pattern_type glob -i "$workdir/frame-*.png" \
    -pix_fmt yuv420p -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" "$output" \
    -loglevel error

echo "Wrote $output"
