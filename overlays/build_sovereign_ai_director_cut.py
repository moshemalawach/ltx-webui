#!/usr/bin/env python3
"""No-text director's cut for the sovereign AI short."""

from pathlib import Path
import subprocess

OV = Path(__file__).parent
OUT = OV.parent / "outputs"

XF = 0.24
SRC_DUR = 3.62
SPEED = 1.12
SHOT_DUR = SRC_DUR * SPEED
START_BLACK = 0.72
END_BLACK = 0.95


def latest(sub: str) -> str:
    hits = sorted(OUT.glob(f"*{sub}*.mp4"), key=lambda p: p.stat().st_mtime)
    if not hits:
        raise SystemExit(f"missing clip: *{sub}*")
    return str(hits[-1])


def build() -> None:
    shots = [
        (latest("rain-slides-across-a-rooftop-at-night"), 0.10),
        (latest("extreme-telephoto-detail-of-the-centrali"), 0.10),
        (latest("inside-a-vast-centralized-ai-chamber"), 0.10),
        (latest("in-a-quiet-apartment-at-night-family-pho"), 0.10),
        (latest("in-a-quiet-apartment-workshop-a-compact"), 0.10),
        (latest("macro-close-up-on-hands-at-the-apartment"), 0.10),
        (latest("during-a-violent-rainstorm-the-centraliz"), 0.10),
        (latest("street-level-view-during-the-centralized"), 0.10),
        (latest("a-quiet-residential-stairwell-during-the"), 0.10),
        (latest("at-dawn-after-the-storm-many-small-local"), 0.10),
        (latest("inside-a-sunlit-civic-workshop-transpare"), 0.10),
        (latest("final-intimate-close-shot-inside-the-sun"), 0.10),
    ]

    seg_durs = [START_BLACK] + [SHOT_DUR for _ in shots] + [END_BLACK]
    starts_abs = [0.0]
    for dur in seg_durs[:-1]:
        starts_abs.append(starts_abs[-1] + dur - XF)
    total = starts_abs[-1] + seg_durs[-1]
    outage_time = starts_abs[7]

    inputs = [
        "-f",
        "lavfi",
        "-t",
        f"{START_BLACK:.2f}",
        "-i",
        "color=c=black:s=1080x1920:r=25",
        "-f",
        "lavfi",
        "-t",
        f"{END_BLACK:.2f}",
        "-i",
        "color=c=black:s=1080x1920:r=25",
    ]
    for clip, _ in shots:
        inputs += ["-i", clip]

    drone_in = 2 + len(shots)
    sub_in = drone_in + 1
    high_in = drone_in + 2
    warm_in = drone_in + 3
    air_in = drone_in + 4
    pulse_in = drone_in + 5
    hit_in = drone_in + 6
    inputs += [
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=43:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=86:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=920:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=164:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "anoisesrc=color=pink:sample_rate=48000:amplitude=0.028",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=110:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        "1.6",
        "-i",
        "sine=frequency=48:sample_rate=48000",
    ]

    fc = []
    fc.append("[0:v]settb=AVTB,format=yuv420p[seg0]")
    for i, (_, start) in enumerate(shots, start=1):
        fc.append(
            f"[{i + 1}:v]crop=1080:1920,trim=start={start}:duration={SRC_DUR:.2f},"
            f"setpts=(PTS-STARTPTS)*{SPEED:.5f},fps=25,settb=AVTB,"
            "eq=contrast=1.045:saturation=1.04,vignette=PI/6,format=yuv420p"
            f"[seg{i}]"
        )
    fc.append("[1:v]settb=AVTB,format=yuv420p[seg13]")

    prev = "seg0"
    for k in range(1, len(seg_durs)):
        out_label = f"xf{k}" if k < len(seg_durs) - 1 else "vfilm"
        fc.append(
            f"[{prev}][seg{k}]xfade=transition=fade:duration={XF}:"
            f"offset={starts_abs[k]:.2f}[{out_label}]"
        )
        prev = out_label

    fc.append(f"anullsrc=r=48000:cl=stereo:d={START_BLACK:.2f}[as0]")
    atempo = 1.0 / SPEED
    for i, (_, start) in enumerate(shots, start=1):
        fade_start = SHOT_DUR - 0.35
        fc.append(
            f"[{i + 1}:a]aresample=48000,atrim=start={start}:duration={SRC_DUR:.2f},"
            f"asetpts=PTS-STARTPTS,atempo={atempo:.5f},"
            f"afade=t=in:d=0.08,afade=t=out:st={fade_start:.2f}:d=0.28,"
            "volume=0.58"
            f"[as{i}]"
        )
    fc.append(f"anullsrc=r=48000:cl=stereo:d={END_BLACK:.2f}[as13]")
    prev = "as0"
    for k in range(1, len(seg_durs)):
        out_label = f"ax{k}" if k < len(seg_durs) - 1 else "amb"
        fc.append(f"[{prev}][as{k}]acrossfade=d={XF}:c1=tri:c2=tri[{out_label}]")
        prev = out_label

    fade_out = total - 2.2
    fc.append(
        f"[{drone_in}:a]aformat=channel_layouts=stereo,volume=0.075,"
        f"afade=t=in:d=2.4,afade=t=out:st={fade_out:.2f}:d=2.2[drone]"
    )
    fc.append(
        f"[{sub_in}:a]aformat=channel_layouts=stereo,volume=0.038,"
        f"afade=t=in:d=4.0,afade=t=out:st={fade_out:.2f}:d=2.2[sub]"
    )
    fc.append(
        f"[{high_in}:a]aformat=channel_layouts=stereo,volume=0.022,"
        "afade=t=in:d=1.5,afade=t=out:st=20.0:d=7.0[high]"
    )
    fc.append(
        f"[{warm_in}:a]aformat=channel_layouts=stereo,volume=0.052,"
        f"afade=t=in:st=20.0:d=10.0,afade=t=out:st={fade_out:.2f}:d=2.1[warm]"
    )
    fc.append(
        f"[{air_in}:a]aformat=channel_layouts=stereo,highpass=f=260,lowpass=f=3800,"
        f"volume=0.16,afade=t=in:d=1.0,afade=t=out:st={fade_out:.2f}:d=2.0[air]"
    )
    fc.append(
        f"[{pulse_in}:a]aformat=channel_layouts=stereo,tremolo=f=0.82:d=0.86,"
        f"volume=0.030,afade=t=in:st=18.0:d=8.0,afade=t=out:st={fade_out:.2f}:d=2.0[pulse]"
    )
    delay_ms = int(outage_time * 1000)
    fc.append(
        f"[{hit_in}:a]aformat=channel_layouts=stereo,afade=t=out:st=0.18:d=1.25,"
        f"volume=0.18,adelay={delay_ms}|{delay_ms}[hit]"
    )
    fc.append("[drone][sub][high][warm][air][pulse][hit]amix=inputs=7:duration=longest:normalize=0[score]")
    fc.append(
        "[amb][score]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.88,loudnorm=I=-15:TP=-1.5[afilm]"
    )

    output = OUT / "FILM-sovereign-ai-director-cut-1080x1920.mp4"
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
        str(output),
    ]
    subprocess.run(cmd, check=True)
    print(f"built {output} ({total:.2f}s)")


if __name__ == "__main__":
    build()
