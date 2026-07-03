#!/usr/bin/env bash
# Assemble the two vertical brand films from generated shots + overlay plates.
# Usage: build_films.sh <monolith_clip>  (path to the 12s monolith take)
set -euo pipefail

OUT="${LTX_OUTPUTS:-$(cd "$(dirname "$0")/../outputs" && pwd)}"
OV="${LTX_OVERLAYS:-$(cd "$(dirname "$0")" && pwd)}"
MONO="${1:?pass monolith clip path}"

HALL="$OUT/20260703-171504-the-camera-drifts-forward-extremely-slow-s5.mp4"
PRISM="$OUT/20260703-170052-the-descending-fiber-optic-strands-shimm-s7.mp4"
CORE="$OUT/libertai-core-vertical-CONDITIONED-s7.mp4"
FURNACE="$OUT/20260703-170052-flames-flicker-and-surge-gently-inside-t-s7.mp4"
GPU="$OUT/20260703-171504-the-graphics-card-stays-perfectly-sharp-s5.mp4"

# seg <video> <start> <dur> <plate> <vout> <aout>  — one titled shot
film() { # name shot1... builds via generated filtergraph below
  :
}

build() {
  local name="$1" lockup="$2"; shift 2
  local -a clips starts durs plates
  while (( $# )); do clips+=("$1"); starts+=("$2"); durs+=("$3"); plates+=("$4"); shift 4; done

  local inputs=() fc="" vcat="" acat="" n=${#clips[@]}
  for i in "${!clips[@]}"; do
    inputs+=(-i "${clips[$i]}")
  done
  for i in "${!clips[@]}"; do
    inputs+=(-loop 1 -t "${durs[$i]}" -i "${plates[$i]}")
  done
  inputs+=(-loop 1 -t 2.4 -i "$lockup")
  inputs+=(-f lavfi -t 2.4 -i "anullsrc=r=48000:cl=stereo")

  for i in "${!clips[@]}"; do
    local s="${starts[$i]}" d="${durs[$i]}" p=$((n + i))
    local fadeout; fadeout=$(python3 -c "print(round(${d}-0.9,2))")
    fc+="[$i:v]crop=1080:1920,trim=start=${s}:duration=${d},setpts=PTS-STARTPTS,fps=25,settb=AVTB[v$i];"
    fc+="[$p:v]format=rgba,fps=25,settb=AVTB,fade=t=in:st=0.6:d=0.5:alpha=1,fade=t=out:st=${fadeout}:d=0.5:alpha=1[p$i];"
    fc+="[v$i][p$i]overlay=format=auto[o$i];"
    fc+="[$i:a]atrim=start=${s}:duration=${d},asetpts=PTS-STARTPTS,afade=t=in:d=0.25,afade=t=out:st=$(python3 -c "print(round(${d}-0.25,2))"):d=0.25[a$i];"
    vcat+="[o$i]"; acat+="[a$i]"
  done
  local lk=$((2 * n)) sil=$((2 * n + 1))
  fc+="[$lk:v]format=yuv420p,fps=25,settb=AVTB,fade=t=in:d=0.5[olk];"
  fc+="${vcat}[olk]concat=n=$((n + 1)):v=1:a=0[vfilm];"
  fc+="${acat}[$sil:a]concat=n=$((n + 1)):v=0:a=1,loudnorm=I=-14:TP=-1.5[afilm]"

  ffmpeg -y -v error "${inputs[@]}" -filter_complex "$fc" \
    -map "[vfilm]" -map "[afilm]" \
    -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -movflags +faststart "$OUT/$name"
  echo "built $OUT/$name"
}

build "FILM-aleph-sovereign-1080x1920.mp4" "$OV/lockup-aleph.png" \
  "$HALL"    0.4 5.5 "$OV/overlay-hall.png" \
  "$MONO"    0.8 6.0 "$OV/overlay-monolith.png" \
  "$PRISM"   0.4 6.0 "$OV/overlay-prism.png"

build "FILM-libertai-terminal-1080x1920.mp4" "$OV/lockup-libertai.png" \
  "$CORE"    0.2 6.0 "$OV/overlay-core.png" \
  "$FURNACE" 0.4 5.5 "$OV/overlay-furnace.png" \
  "$GPU"     0.4 5.5 "$OV/overlay-gpu.png"
