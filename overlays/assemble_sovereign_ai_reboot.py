#!/usr/bin/env python3
"""Assemble the reboot sovereign-AI rough cut from accepted shot candidates."""

from __future__ import annotations

import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "reboot"

SHOTS = [
    OUT / "s01-dependency-seed7101-832x1472-129f.mp4",
    OUT / "s02-single-point-seed7102-832x1472-129f.mp4",
    OUT / "s03-cost-seed7103-832x1472-129f.mp4",
    OUT / "s04-local-first-seed7104-832x1472-129f.mp4",
    OUT / "s05-mesh-seed7105-832x1472-129f.mp4",
    OUT / "s06-consent-seed7106-832x1472-129f.mp4",
    OUT / "s07-city-still-here-seed7207-832x1472-129f.mp4",
]

PICTURE_LOCK = OUT / "FILM-sovereign-ai-reboot-picture-lock-1080x1920.mp4"
SHEET = OUT / "FILM-sovereign-ai-reboot-picture-lock-1080x1920.sheet.jpg"


def duration(path: Path) -> float:
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(raw)


def main() -> None:
    missing = [str(path) for path in SHOTS if not path.exists()]
    if missing:
        raise SystemExit("missing shots:\n" + "\n".join(missing))

    total = sum(duration(path) for path in SHOTS)
    inputs: list[str] = []
    for shot in SHOTS:
        inputs += ["-i", str(shot)]
    inputs += [
        "-f",
        "lavfi",
        "-t",
        f"{total:.3f}",
        "-i",
        "anoisesrc=color=brown:amplitude=0.045:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.3f}",
        "-i",
        "sine=frequency=46:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.3f}",
        "-i",
        "sine=frequency=147:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.3f}",
        "-i",
        "sine=frequency=220:sample_rate=48000",
    ]

    video_parts = []
    for i in range(len(SHOTS)):
        video_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,fps=24,format=yuv420p[v{i}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(len(SHOTS)))
    audio_base = len(SHOTS)
    filter_complex = (
        ";".join(video_parts)
        + ";"
        + f"{concat_inputs}concat=n={len(SHOTS)}:v=1:a=0[vout];"
        + f"[{audio_base}:a]highpass=f=450,lowpass=f=6500,volume=0.18,"
        + "afade=t=in:st=0:d=2,afade=t=out:st=54:d=2[rain];"
        + f"[{audio_base + 1}:a]volume='if(lt(t,16),0.075,0.035)':eval=frame,"
        + "afade=t=in:st=0:d=4,afade=t=out:st=50:d=6[sub];"
        + f"[{audio_base + 2}:a]volume='if(gte(t,28),0.035,0)':eval=frame,"
        + "afade=t=in:st=28:d=8[warm1];"
        + f"[{audio_base + 3}:a]volume='if(gte(t,40),0.025,0)':eval=frame,"
        + "afade=t=in:st=40:d=6[warm2];"
        + "[rain][sub][warm1][warm2]amix=inputs=4:duration=first,"
        + "alimiter=limit=0.85,loudnorm=I=-18:TP=-2:LRA=10,"
        + "aformat=sample_rates=48000:channel_layouts=stereo[aout]"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(PICTURE_LOCK),
        ],
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(PICTURE_LOCK),
            "-vf",
            "fps=1/4,scale=270:-1,tile=4x4",
            "-frames:v",
            "1",
            str(SHEET),
        ],
        check=True,
    )
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(PICTURE_LOCK), "-f", "null", "-"], check=True)
    print(PICTURE_LOCK)
    print(SHEET)


if __name__ == "__main__":
    main()
