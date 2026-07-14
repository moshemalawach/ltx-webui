#!/usr/bin/env python3
"""V5 brand films: footage-backed cold opens, fuller lower-thirds, insert-beat
titles, blurred-video end lockups, and tighter voice/score ducking."""

from __future__ import annotations

import subprocess
from pathlib import Path

OV = Path(__file__).resolve().parent
OUT = OV.parent / "outputs"

XF = 0.28
COLD_DUR = 2.15
END_DUR = 2.85
FPS = 25


def latest(sub: str) -> str:
    hits = sorted(OUT.glob(f"*{sub}*.mp4"), key=lambda p: p.stat().st_mtime)
    if not hits:
        raise SystemExit(f"missing clip: *{sub}*")
    return str(hits[-1])


def build(name: str, lockup: str, cold: str, bed: str, vo: str, shots: list[tuple[str, float, float, str]]) -> None:
    """Build a vertical reel.

    shots: list of (clip, source_start, duration, plate_png)
    """
    n = len(shots)
    segs = [COLD_DUR] + [s[2] for s in shots] + [END_DUR]
    starts_abs = [0.0]
    for dur in segs[:-1]:
        starts_abs.append(starts_abs[-1] + dur - XF)
    total = starts_abs[-1] + segs[-1]

    inputs: list[str] = []
    inputs += ["-i", shots[0][0]]
    inputs += ["-loop", "1", "-t", f"{COLD_DUR:.2f}", "-i", cold]
    for clip, *_ in shots:
        inputs += ["-i", clip]

    scrim_in = 2 + n
    inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", str(OV / "scrim-v5.png")]

    plate_idx: dict[int, int] = {}
    next_input = scrim_in + 1
    for i, (_, _, _, plate) in enumerate(shots):
        inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", plate]
        plate_idx[i] = next_input
        next_input += 1

    lockup_in = next_input
    bed_in = next_input + 1
    vo_in = next_input + 2
    inputs += ["-loop", "1", "-t", f"{END_DUR:.2f}", "-i", lockup, "-i", bed, "-i", vo]

    fc: list[str] = []

    # Footage-backed cold open: blurred, darkened movement with a deterministic title plate.
    fc.append(
        f"[0:v]crop=1080:1920,trim=start=0.25:duration={COLD_DUR:.2f},"
        "setpts=PTS-STARTPTS,"
        f"fps={FPS},settb=AVTB,scale=1134:2016,crop=1080:1920,"
        "boxblur=8:2,eq=brightness=-0.13:contrast=1.16:saturation=0.82,"
        "setsar=1,format=yuv420p[coldbg]"
    )
    fc.append(
        f"[1:v]format=rgba,fps={FPS},settb=AVTB,"
        f"fade=t=in:st=0.10:d=0.48:alpha=1,"
        f"fade=t=out:st={COLD_DUR - 0.44:.2f}:d=0.38:alpha=1[coldtxt]"
    )
    fc.append("[coldbg][coldtxt]overlay=format=auto,format=yuv420p[seg0]")

    for i, (_, start, dur, _) in enumerate(shots):
        fc.append(
            f"[{2 + i}:v]crop=1080:1920,trim=start={start}:duration={dur},"
            f"setpts=PTS-STARTPTS,fps={FPS},settb=AVTB,"
            "eq=contrast=1.07:saturation=1.08:brightness=-0.01,"
            "unsharp=5:5:0.28:3:3:0.12,vignette=PI/5,"
            f"setsar=1,format=yuv420p[seg{i + 1}]"
        )

    last_input = 2 + n - 1
    fc.append(
        f"[{last_input}:v]crop=1080:1920,trim=start=0.45:duration={END_DUR:.2f},"
        f"setpts=PTS-STARTPTS,fps={FPS},settb=AVTB,scale=1134:2016,crop=1080:1920,"
        "boxblur=9:2,eq=brightness=-0.16:contrast=1.10:saturation=0.86,"
        "setsar=1,format=yuv420p[endbg]"
    )
    fc.append(
        f"[{lockup_in}:v]format=rgba,fps={FPS},settb=AVTB,"
        f"fade=t=in:st=0.18:d=0.54:alpha=1,"
        f"fade=t=out:st={END_DUR - 0.48:.2f}:d=0.42:alpha=1[lock]"
    )
    fc.append("[endbg][lock]overlay=format=auto,format=yuv420p[seg{n1}]".format(n1=n + 1))

    prev = "seg0"
    for k in range(1, n + 2):
        offset = round(starts_abs[k], 2)
        out_label = f"xf{k}" if k < n + 1 else "vchain"
        fc.append(f"[{prev}][seg{k}]xfade=transition=fade:duration={XF}:offset={offset}[{out_label}]")
        prev = out_label

    scrim_out = round(starts_abs[n + 1] - 0.28, 2)
    fc.append(
        f"[{scrim_in}:v]format=rgba,fps={FPS},settb=AVTB,"
        "fade=t=in:st=1.35:d=0.55:alpha=1,"
        f"fade=t=out:st={scrim_out}:d=0.55:alpha=1[scr]"
    )
    fc.append("[vchain][scr]overlay=format=auto[vscr]")

    cur = "vscr"
    for i, (_, _, dur, _) in enumerate(shots):
        t0 = round(starts_abs[i + 1] + 0.46, 2)
        t1 = round(starts_abs[i + 1] + dur - 0.58, 2)
        fc.append(
            f"[{plate_idx[i]}:v]format=rgba,fps={FPS},settb=AVTB,"
            f"fade=t=in:st={t0}:d=0.48:alpha=1,"
            f"fade=t=out:st={t1}:d=0.38:alpha=1[tp{i}]"
        )
        fc.append(
            f"[{cur}][tp{i}]overlay=x=0:"
            f"y='18*(1-min(1,max(0,(t-{t0})/0.48)))':format=auto[vt{i}]"
        )
        cur = f"vt{i}"
    fc.append(f"[{cur}]format=yuv420p[vfilm]")

    # Audio: shot ambients under score, then voice ducks music and ambients.
    fc.append(f"anullsrc=r=48000:cl=stereo:d={COLD_DUR:.2f}[as0]")
    for i, (_, start, dur, _) in enumerate(shots):
        fc.append(
            f"[{2 + i}:a]aresample=48000,atrim=start={start}:duration={dur},"
            f"asetpts=PTS-STARTPTS[as{i + 1}]"
        )
    fc.append(f"anullsrc=r=48000:cl=stereo:d={END_DUR:.2f}[as{n + 1}]")

    prev_a = "as0"
    for k in range(1, n + 2):
        out_label = f"ax{k}" if k < n + 1 else "achain"
        fc.append(f"[{prev_a}][as{k}]acrossfade=d={XF}:c1=tri:c2=tri[{out_label}]")
        prev_a = out_label

    bed_fade = round(total - 1.55, 2)
    fc.append(
        f"[{bed_in}:a]aresample=48000,atrim=duration={total:.2f},"
        f"afade=t=in:d=0.45,afade=t=out:st={bed_fade}:d=1.55,volume=0.92[abed]"
    )
    fc.append("[achain]volume=0.34[alow]")
    fc.append("[alow][abed]amix=inputs=2:duration=longest:normalize=0[amus]")
    fc.append(
        f"[{vo_in}:a]aresample=48000,adelay=950|950,"
        f"apad=whole_dur={total:.2f},volume=1.0,asplit=2[vo1][vo2]"
    )
    fc.append(
        "[amus][vo1]sidechaincompress=threshold=0.045:ratio=5.5:"
        "attack=45:release=420:makeup=1[aduck]"
    )
    fc.append(
        "[aduck][vo2]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.89,loudnorm=I=-14:TP=-1.5[afilm]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        *inputs,
        "-filter_complex",
        ";".join(fc),
        "-map",
        "[vfilm]",
        "-map",
        "[afilm]",
        "-t",
        f"{total:.2f}",
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "16",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(OUT / name),
    ]
    subprocess.run(cmd, check=True)
    print(f"built {OUT / name} ({total:.2f}s)")


A = {
    "a1": latest("a-bright-pulse-of-white-cyan"),
    "a2": latest("a-pulse-of-white-light-travels"),
    "a3": latest("bright-pulses-of-lime-green"),
    "seam": latest("the-thin-seam-of-violet"),
    "chan": latest("pulses-of-light-travel-along"),
}

L = {
    "l1": latest("the-amber-block-cursor"),
    "l2": latest("the-dense-amber-circuitry"),
    "l3": latest("lines-of-soft-glowing"),
    "emb": latest("tiny-orange-embers"),
    "fan": latest("the-dark-fan-blades"),
}

build(
    "FILMv5-aleph-sovereign-1080x1920.mp4",
    str(OV / "lockup-aleph-v5.png"),
    str(OV / "cold-aleph-v5.png"),
    str(OV / "bed-aleph.mp4"),
    str(OV / "vo-aleph3.mp4"),
    [
        (A["a1"], 0.55, 3.95, str(OV / "t5-arrive.png")),
        (A["a2"], 0.95, 4.65, str(OV / "t5-machine.png")),
        (A["seam"], 0.55, 2.65, str(OV / "t5-seam.png")),
        (A["a3"], 0.55, 3.95, str(OV / "t5-out.png")),
        (A["chan"], 0.55, 2.55, str(OV / "t5-channels.png")),
    ],
)

build(
    "FILMv5-libertai-terminal-1080x1920.mp4",
    str(OV / "lockup-libertai-v5.png"),
    str(OV / "cold-libertai-v5.png"),
    str(OV / "bed-libertai.mp4"),
    str(OV / "vo-libertai3.mp4"),
    [
        (L["l1"], 0.55, 3.95, str(OV / "t5-terminal.png")),
        (L["l2"], 0.95, 4.65, str(OV / "t5-engine.png")),
        (L["emb"], 0.55, 2.65, str(OV / "t5-embers.png")),
        (L["l3"], 0.55, 3.95, str(OV / "t5-response.png")),
        (L["fan"], 0.55, 2.55, str(OV / "t5-fan.png")),
    ],
)
