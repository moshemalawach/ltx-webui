#!/usr/bin/env python3
"""V3 brand films: soft crossfade cuts, motion-alive trims, film-wide scrim,
absolute-time type overlays, and a continuous generated score under low-mixed
shot ambients. Fixes v2's audio valleys at cuts and frozen-frame cut-ins."""

import subprocess
from pathlib import Path

OV = Path(__file__).parent
OUT = OV.parent / "outputs"
XF = 0.25  # crossfade duration between all segments


def latest(sub: str) -> str:
    hits = sorted(OUT.glob(f"*{sub}*.mp4"), key=lambda p: p.stat().st_mtime)
    if not hits:
        raise SystemExit(f"missing clip: *{sub}*")
    return str(hits[-1])


def build(name: str, lockup: str, cold: str, bed: str, shots: list) -> None:
    """shots: list of (clip, start, dur, plate_or_None)."""
    n = len(shots)
    segs = [1.3] + [s[2] for s in shots] + [2.6]
    starts_abs = [0.0]
    for d in segs[:-1]:
        starts_abs.append(starts_abs[-1] + d - XF)
    total = starts_abs[-1] + segs[-1]

    inputs = ["-f", "lavfi", "-t", "1.3", "-i", "color=c=black:s=1080x1920:r=25",
              "-loop", "1", "-t", "1.3", "-i", cold]
    for clip, *_ in shots:
        inputs += ["-i", clip]
    inputs += ["-loop", "1", "-t", str(round(total, 2)), "-i", str(OV / "scrim.png")]
    plate_idx = {}
    for i, (_, _, d, plate) in enumerate(shots):
        if plate:
            plate_idx[i] = len(inputs) // 2  # placeholder, fixed below
    # rebuild input list index bookkeeping properly
    idx = 2 + n  # scrim input index
    scrim_in = idx
    fc = []
    pidx = scrim_in + 1
    plate_inputs = []
    for i, (_, _, d, plate) in enumerate(shots):
        if plate:
            plate_inputs += ["-loop", "1", "-t", str(round(total, 2)), "-i", plate]
            plate_idx[i] = pidx
            pidx += 1
    inputs += plate_inputs
    lockup_in = pidx
    bed_in = pidx + 1
    inputs += ["-loop", "1", "-t", "2.6", "-i", lockup, "-i", bed]

    # --- video segments ---
    fc.append("[1:v]format=rgba,fps=25,settb=AVTB,"
              "fade=t=in:st=0.15:d=0.4:alpha=1,fade=t=out:st=0.95:d=0.3:alpha=1[cold]")
    fc.append("[0:v]settb=AVTB[blk]")
    fc.append("[blk][cold]overlay=format=auto,format=yuv420p[seg0]")
    for i, (clip, s, d, _) in enumerate(shots):
        fc.append(f"[{2 + i}:v]crop=1080:1920,trim=start={s}:duration={d},"
                  f"setpts=PTS-STARTPTS,fps=25,settb=AVTB,"
                  f"eq=contrast=1.05:saturation=1.07,vignette=PI/5,format=yuv420p[seg{i + 1}]")
    fc.append(f"[{lockup_in}:v]format=yuv420p,fps=25,settb=AVTB,"
              f"fade=t=out:st=2.2:d=0.4[seg{n + 1}]")

    # xfade chain
    prev = "seg0"
    for k in range(1, n + 2):
        off = round(starts_abs[k], 2)
        outl = f"xf{k}" if k < n + 1 else "vchain"
        fc.append(f"[{prev}][seg{k}]xfade=transition=fade:duration={XF}:offset={off}[{outl}]")
        prev = outl

    # film-wide scrim then type plates at absolute times
    scrim_off = round(starts_abs[n + 1] - 0.2, 2)
    fc.append(f"[{scrim_in}:v]format=rgba,fps=25,settb=AVTB,"
              f"fade=t=in:st=1.0:d=0.6:alpha=1,fade=t=out:st={scrim_off}:d=0.7:alpha=1[scr]")
    fc.append("[vchain][scr]overlay=format=auto[vscr]")
    cur = "vscr"
    for i, (_, _, d, plate) in enumerate(shots):
        if not plate:
            continue
        t0 = round(starts_abs[i + 1] + 0.55, 2)
        t1 = round(starts_abs[i + 1] + d - 0.85, 2)
        fc.append(f"[{plate_idx[i]}:v]format=rgba,fps=25,settb=AVTB,"
                  f"fade=t=in:st={t0}:d=0.55:alpha=1,fade=t=out:st={t1}:d=0.45:alpha=1[tp{i}]")
        fc.append(f"[{cur}][tp{i}]overlay=x=0:"
                  f"y='26*(1-min(1,max(0,(t-{t0})/0.55)))':format=auto[vt{i}]")
        cur = f"vt{i}"
    fc.append(f"[{cur}]copy[vfilm]")

    # --- audio: silences + shot ambients acrossfaded, over the score bed ---
    fc.append("anullsrc=r=48000:cl=stereo:d=1.3[as0]")
    for i, (clip, s, d, _) in enumerate(shots):
        fc.append(f"[{2 + i}:a]aresample=48000,atrim=start={s}:duration={d},"
                  f"asetpts=PTS-STARTPTS[as{i + 1}]")
    fc.append(f"anullsrc=r=48000:cl=stereo:d=2.6[as{n + 1}]")
    prev = "as0"
    for k in range(1, n + 2):
        outl = f"ax{k}" if k < n + 1 else "achain"
        fc.append(f"[{prev}][as{k}]acrossfade=d={XF}:c1=tri:c2=tri[{outl}]")
        prev = outl
    bed_fade = round(total - 1.6, 2)
    fc.append(f"[{bed_in}:a]aresample=48000,atrim=duration={round(total, 2)},"
              f"afade=t=in:d=0.5,afade=t=out:st={bed_fade}:d=1.6,volume=1.0[abed]")
    fc.append("[achain]volume=0.4[alow]")
    fc.append("[alow][abed]amix=inputs=2:duration=longest:normalize=0,"
              "alimiter=limit=0.89,loudnorm=I=-14:TP=-1.5[afilm]")

    cmd = ["ffmpeg", "-y", "-v", "error", *inputs,
           "-filter_complex", ";".join(fc),
           "-map", "[vfilm]", "-map", "[afilm]", "-t", str(round(total, 2)),
           "-c:v", "libx264", "-preset", "slow", "-crf", "17",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", str(OUT / name)]
    subprocess.run(cmd, check=True)
    print(f"built {OUT / name} ({round(total, 2)}s)")


A = dict(a1=latest("a-bright-pulse-of-white-cyan"),
         a2=latest("a-pulse-of-white-light-travels"),
         a3=latest("bright-pulses-of-lime-green"),
         seam=latest("the-thin-seam-of-violet"),
         chan=latest("pulses-of-light-travel-along"))
L = dict(l1=latest("the-amber-block-cursor"),
         l2=latest("the-dense-amber-circuitry"),
         l3=latest("lines-of-soft-glowing"),
         emb=latest("tiny-orange-embers"),
         fan=latest("the-dark-fan-blades"))

build("FILMv3-aleph-sovereign-1080x1920.mp4",
      str(OV / "lockup-aleph.png"), str(OV / "cold-aleph.png"),
      str(OV / "bed-aleph.mp4"),
      [(A["a1"], 0.7, 4.0, str(OV / "t2-arrive.png")),
       (A["a2"], 1.0, 4.7, str(OV / "t2-machine.png")),
       (A["seam"], 0.7, 2.8, None),
       (A["a3"], 0.7, 4.0, str(OV / "t2-out.png")),
       (A["chan"], 0.7, 2.4, None)])

build("FILMv3-libertai-terminal-1080x1920.mp4",
      str(OV / "lockup-libertai.png"), str(OV / "cold-libertai.png"),
      str(OV / "bed-libertai.mp4"),
      [(L["l1"], 0.7, 4.0, str(OV / "t2-terminal.png")),
       (L["l2"], 1.0, 4.7, str(OV / "t2-engine.png")),
       (L["emb"], 0.7, 2.8, None),
       (L["l3"], 0.7, 4.0, str(OV / "t2-response.png")),
       (L["fan"], 0.7, 2.4, None)])
