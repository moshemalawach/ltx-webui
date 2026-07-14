#!/usr/bin/env python3
"""Assemble the standalone sovereign AI short from generated LTX shots."""

from pathlib import Path
import subprocess

OV = Path(__file__).parent
OUT = OV.parent / "outputs"
XF = 0.22
SHOT_DUR = 3.45
SHOT_START = 0.18


def latest(sub: str) -> str:
    hits = sorted(OUT.glob(f"*{sub}*.mp4"), key=lambda p: p.stat().st_mtime)
    if not hits:
        raise SystemExit(f"missing clip: *{sub}*")
    return str(hits[-1])


def build() -> None:
    shots = [
        (latest("rain-slides-across-a-rooftop-at-night"), SHOT_START, SHOT_DUR, OV / "svai-t01.png"),
        (latest("inside-a-vast-centralized-ai-chamber"), SHOT_START, SHOT_DUR, OV / "svai-t02.png"),
        (latest("in-a-quiet-apartment-workshop-a-compact"), SHOT_START, SHOT_DUR, OV / "svai-t03.png"),
        (latest("during-a-violent-rainstorm-the-centraliz"), SHOT_START, SHOT_DUR, OV / "svai-t04.png"),
        (latest("at-dawn-after-the-storm-many-small-local"), SHOT_START, SHOT_DUR, OV / "svai-t05.png"),
        (latest("inside-a-sunlit-civic-workshop-transpare"), SHOT_START, SHOT_DUR, OV / "svai-t06.png"),
    ]
    name = "FILM-sovereign-ai-risk-1080x1920.mp4"
    n = len(shots)
    segs = [1.35] + [s[2] for s in shots] + [2.45]
    starts_abs = [0.0]
    for dur in segs[:-1]:
        starts_abs.append(starts_abs[-1] + dur - XF)
    total = starts_abs[-1] + segs[-1]

    inputs = [
        "-f",
        "lavfi",
        "-t",
        "1.35",
        "-i",
        "color=c=black:s=1080x1920:r=25",
        "-loop",
        "1",
        "-t",
        "1.35",
        "-i",
        str(OV / "svai-cold.png"),
    ]
    for clip, *_ in shots:
        inputs += ["-i", clip]
    scrim_in = 2 + n
    inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", str(OV / "svai-scrim.png")]
    plate_idx = {}
    pidx = scrim_in + 1
    for i, (_, _, _, plate) in enumerate(shots):
        inputs += ["-loop", "1", "-t", f"{total:.2f}", "-i", str(plate)]
        plate_idx[i] = pidx
        pidx += 1
    end_in = pidx
    silence_in = pidx + 1
    drone_in = pidx + 2
    harm_in = pidx + 3
    air_in = pidx + 4
    inputs += [
        "-loop",
        "1",
        "-t",
        "2.45",
        "-i",
        str(OV / "svai-end.png"),
        "-f",
        "lavfi",
        "-t",
        "2.45",
        "-i",
        "anullsrc=r=48000:cl=stereo",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=46:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=138:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "anoisesrc=color=pink:sample_rate=48000:amplitude=0.018",
    ]

    fc = []
    fc.append(
        "[1:v]format=rgba,fps=25,settb=AVTB,"
        "fade=t=in:st=0.14:d=0.36:alpha=1,fade=t=out:st=1.03:d=0.28:alpha=1[cold]"
    )
    fc.append("[0:v]settb=AVTB[blk]")
    fc.append("[blk][cold]overlay=format=auto,format=yuv420p[seg0]")
    for i, (_, start, dur, _) in enumerate(shots):
        fc.append(
            f"[{2 + i}:v]crop=1080:1920,trim=start={start}:duration={dur},"
            "setpts=PTS-STARTPTS,fps=25,settb=AVTB,"
            "eq=contrast=1.06:saturation=1.05,vignette=PI/5,format=yuv420p"
            f"[seg{i + 1}]"
        )
    fc.append(
        f"[{end_in}:v]format=yuv420p,fps=25,settb=AVTB,"
        "fade=t=in:st=0:d=0.35,fade=t=out:st=2.05:d=0.4[seg7]"
    )

    prev = "seg0"
    for k in range(1, n + 2):
        out_label = f"xf{k}" if k < n + 1 else "vchain"
        fc.append(
            f"[{prev}][seg{k}]xfade=transition=fade:duration={XF}:"
            f"offset={starts_abs[k]:.2f}[{out_label}]"
        )
        prev = out_label

    scrim_out = starts_abs[-1] - 0.1
    fc.append(
        f"[{scrim_in}:v]format=rgba,fps=25,settb=AVTB,"
        f"fade=t=in:st=1.0:d=0.6:alpha=1,fade=t=out:st={scrim_out:.2f}:d=0.45:alpha=1[scr]"
    )
    fc.append("[vchain][scr]overlay=format=auto[vscr]")
    cur = "vscr"
    for i, (_, _, dur, _) in enumerate(shots):
        t0 = starts_abs[i + 1] + 0.5
        t1 = starts_abs[i + 1] + dur - 0.55
        fc.append(
            f"[{plate_idx[i]}:v]format=rgba,fps=25,settb=AVTB,"
            f"fade=t=in:st={t0:.2f}:d=0.48:alpha=1,"
            f"fade=t=out:st={t1:.2f}:d=0.38:alpha=1[tp{i}]"
        )
        fc.append(
            f"[{cur}][tp{i}]overlay=x=0:"
            f"y='18*(1-min(1,max(0,(t-{t0:.2f})/0.48)))':format=auto[vt{i}]"
        )
        cur = f"vt{i}"
    fc.append(f"[{cur}]copy[vfilm]")

    fc.append("anullsrc=r=48000:cl=stereo:d=1.35[as0]")
    for i, (_, start, dur, _) in enumerate(shots):
        fc.append(
            f"[{2 + i}:a]aresample=48000,atrim=start={start}:duration={dur},"
            f"asetpts=PTS-STARTPTS,volume=0.42[as{i + 1}]"
        )
    fc.append(f"[{silence_in}:a]aresample=48000[as7]")
    prev = "as0"
    for k in range(1, n + 2):
        out_label = f"ax{k}" if k < n + 1 else "amb"
        fc.append(f"[{prev}][as{k}]acrossfade=d={XF}:c1=tri:c2=tri[{out_label}]")
        prev = out_label

    fade_out = total - 1.3
    fc.append(
        f"[{drone_in}:a]aformat=channel_layouts=stereo,volume=0.13,"
        f"afade=t=in:d=1.2,afade=t=out:st={fade_out:.2f}:d=1.3[drone]"
    )
    fc.append(
        f"[{harm_in}:a]aformat=channel_layouts=stereo,volume=0.055,"
        f"afade=t=in:st=8.0:d=4.5,afade=t=out:st={fade_out:.2f}:d=1.2[harm]"
    )
    fc.append(
        f"[{air_in}:a]aformat=channel_layouts=stereo,highpass=f=220,lowpass=f=4200,"
        f"volume=0.22,afade=t=in:d=0.8,afade=t=out:st={fade_out:.2f}:d=1.1[air]"
    )
    fc.append("[drone][harm][air]amix=inputs=3:duration=first:normalize=0[score]")
    fc.append(
        "[amb][score]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.88,loudnorm=I=-14:TP=-1.5[afilm]"
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
        "17",
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


if __name__ == "__main__":
    build()
