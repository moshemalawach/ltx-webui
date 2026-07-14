#!/usr/bin/env python3
"""Mux the reboot picture lock with the continuous LTX-2.3 T2A score."""

from __future__ import annotations

import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "reboot"
PICTURE = OUT / "FILM-sovereign-ai-reboot-picture-lock-1080x1920.mp4"
SCORE = OUT / "audio" / "svai-reboot-t2a-score.wav"
FINAL = OUT / "FILM-sovereign-ai-reboot-final-1080x1920.mp4"
SHEET = OUT / "FILM-sovereign-ai-reboot-final-1080x1920.sheet.jpg"
WAVEFORM = OUT / "audio" / "svai-reboot-t2a-score.waveform.png"


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
    if not PICTURE.exists():
        raise SystemExit(f"missing picture lock: {PICTURE}")
    if not SCORE.exists():
        raise SystemExit(f"missing T2A score: {SCORE}")

    total = duration(PICTURE)
    audio_filter = (
        f"atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
        "aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=10,"
        "afade=t=in:st=0:d=1.2,"
        f"afade=t=out:st={max(total - 2.4, 0):.3f}:d=2.2,"
        "alimiter=limit=0.92,"
        "aformat=sample_rates=48000:channel_layouts=stereo[aout]"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(PICTURE),
            "-i",
            str(SCORE),
            "-filter_complex",
            f"[1:a]{audio_filter}",
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(FINAL),
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
            str(FINAL),
            "-vf",
            "fps=1/4,scale=270:-1,tile=4x4",
            "-frames:v",
            "1",
            str(SHEET),
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
            str(SCORE),
            "-filter_complex",
            "aformat=channel_layouts=mono,showwavespic=s=1600x360:colors=0xffb020",
            "-frames:v",
            "1",
            str(WAVEFORM),
        ],
        check=True,
    )
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(FINAL), "-f", "null", "-"], check=True)
    print(FINAL)
    print(SHEET)
    print(WAVEFORM)


if __name__ == "__main__":
    main()
