#!/usr/bin/env bash
# V2 brand films: cold open, linked sequence shots with sliding type,
# textless macro inserts, unified grade, continuous audio bed, lockup.
# Usage: build_films_v2.sh  (expects the seq-* / ins-* renders in outputs/)
set -euo pipefail

OUT="${LTX_OUTPUTS:-$(cd "$(dirname "$0")/../outputs" && pwd)}"
OV="${LTX_OVERLAYS:-$(cd "$(dirname "$0")" && pwd)}"

latest() { ls -t "$OUT"/*"$1"*.mp4 | head -1; }

# ---- shot table helpers -----------------------------------------------------
# assemble NAME LOCKUP COLD BED  then quads: clip start dur plate(or "-")
assemble() {
  local name="$1" lockup="$2" cold="$3" bed="$4"; shift 4
  local -a clips starts durs plates
  while (( $# )); do clips+=("$1"); starts+=("$2"); durs+=("$3"); plates+=("$4"); shift 4; done
  local n=${#clips[@]}

  local inputs=(-f lavfi -t 1.3 -i "color=c=black:s=1080x1920:r=25"
                -loop 1 -t 1.3 -i "$cold")
  for i in "${!clips[@]}"; do inputs+=(-i "${clips[$i]}"); done
  inputs+=(-loop 1 -i "$OV/scrim.png")
  for i in "${!clips[@]}"; do
    [ "${plates[$i]}" != "-" ] && inputs+=(-loop 1 -t "${durs[$i]}" -i "${plates[$i]}")
  done
  inputs+=(-loop 1 -t 2.6 -i "$lockup" -i "$bed")

  # input indexing
  local scrim=$((2 + n))
  local pidx=$((scrim + 1))
  local fc="" vcat="" acat=""
  # count plated shots, pre-split the scrim stream (one consumer per use)
  local nplates=0 sci=0
  for i in "${!clips[@]}"; do [ "${plates[$i]}" != "-" ] && nplates=$((nplates + 1)); done
  fc+="[$scrim:v]format=rgba,fps=25,settb=AVTB,split=${nplates}"
  for ((k = 0; k < nplates; k++)); do fc+="[sck$k]"; done
  fc+=";"
  # cold open: black + card fade
  fc+="[1:v]format=rgba,fps=25,settb=AVTB,fade=t=in:st=0.15:d=0.4:alpha=1,fade=t=out:st=0.95:d=0.3:alpha=1[cold];"
  fc+="[0:v]settb=AVTB[blk];[blk][cold]overlay=format=auto[vcold];"
  vcat+="[vcold]"

  local total=1.3
  for i in "${!clips[@]}"; do
    local vin=$((2 + i)) s="${starts[$i]}" d="${durs[$i]}"
    fc+="[$vin:v]crop=1080:1920,trim=start=${s}:duration=${d},setpts=PTS-STARTPTS,fps=25,settb=AVTB,"
    fc+="eq=contrast=1.05:saturation=1.07,vignette=PI/5[w$i];"
    if [ "${plates[$i]}" != "-" ]; then
      local fo; fo=$(python3 -c "print(round(${d}-0.8,2))")
      fc+="[sck$sci]trim=duration=${d}[sc$i];"
      sci=$((sci + 1))
      fc+="[w$i][sc$i]overlay=format=auto[ws$i];"
      fc+="[$pidx:v]format=rgba,fps=25,settb=AVTB,fade=t=in:st=0.45:d=0.55:alpha=1,fade=t=out:st=${fo}:d=0.45:alpha=1[tp$i];"
      fc+="[ws$i][tp$i]overlay=x=0:y='26*(1-min(1,max(0,(t-0.45)/0.55)))':format=auto[o$i];"
      pidx=$((pidx + 1))
    else
      fc+="[w$i]copy[o$i];"
    fi
    fc+="[$vin:a]atrim=start=${s}:duration=${d},asetpts=PTS-STARTPTS,afade=t=in:d=0.3,afade=t=out:st=$(python3 -c "print(round(${d}-0.3,2))"):d=0.3[a$i];"
    vcat+="[o$i]"; acat+="[a$i]"
    total=$(python3 -c "print(round(${total}+${d},2))")
  done

  local lk=$pidx bedin=$((pidx + 1))
  local filmdur; filmdur=$(python3 -c "print(round(${total}+2.6,2))")
  # last shot dips to black via lockup fade-in over black-padded end
  fc+="[$lk:v]format=yuv420p,fps=25,settb=AVTB,fade=t=in:d=0.6,fade=t=out:st=2.2:d=0.4[olk];"
  fc+="${vcat}[olk]concat=n=$((n + 2)):v=1:a=0[vfilm];"
  # audio: shot ambients delayed past the cold open, over a continuous bed
  fc+="${acat}concat=n=${n}:v=0:a=1[ashots];"
  fc+="[ashots]adelay=1300|1300,apad=whole_dur=${filmdur}[avox];"
  fc+="[$bedin:a]aloop=loop=-1:size=2e9,atrim=duration=${filmdur},afade=t=in:d=0.8,afade=t=out:st=$(python3 -c "print(round(${filmdur}-1.2,2))"):d=1.2,volume=0.45[abed];"
  fc+="[avox][abed]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[afilm]"

  ffmpeg -y -v error "${inputs[@]}" -filter_complex "$fc" \
    -map "[vfilm]" -map "[afilm]" \
    -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
    -c:a aac -b:a 192k -movflags +faststart "$OUT/$name"
  echo "built $OUT/$name ($filmdur s)"
}

A1=$(latest "a-bright-pulse-of-white-cyan");  A2=$(latest "a-pulse-of-white-light-travels")
A3=$(latest "bright-pulses-of-lime-green");   SEAM=$(latest "the-thin-seam-of-violet")
CHAN=$(latest "pulses-of-light-travel-along")
L1=$(latest "the-amber-block-cursor");        L2=$(latest "the-dense-amber-circuitry")
L3=$(latest "lines-of-soft-glowing");         EMB=$(latest "tiny-orange-embers")
FAN=$(latest "the-dark-fan-blades")

assemble "FILMv2-aleph-sovereign-1080x1920.mp4" "$OV/lockup-aleph.png" "$OV/cold-aleph.png" "$A2" \
  "$A1"   0.3 4.6 "$OV/t2-arrive.png" \
  "$A2"   0.3 5.6 "$OV/t2-machine.png" \
  "$SEAM" 0.3 2.6 "-" \
  "$A3"   0.3 4.6 "$OV/t2-out.png" \
  "$CHAN" 0.3 2.4 "-"

assemble "FILMv2-libertai-terminal-1080x1920.mp4" "$OV/lockup-libertai.png" "$OV/cold-libertai.png" "$L2" \
  "$L1"  0.3 4.6 "$OV/t2-terminal.png" \
  "$L2"  0.3 5.6 "$OV/t2-engine.png" \
  "$EMB" 0.3 2.6 "-" \
  "$L3"  0.3 4.6 "$OV/t2-response.png" \
  "$FAN" 0.3 2.4 "-"
