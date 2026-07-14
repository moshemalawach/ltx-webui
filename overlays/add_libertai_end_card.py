#!/usr/bin/env python3
"""Append a LibertAI end card to the reboot film."""

from __future__ import annotations

import subprocess
import argparse
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "reboot"
OVERLAYS = BASE / "overlays"

SOURCE = OUT / "FILM-sovereign-ai-reboot-final-1080x1920.mp4"
MESSAGE_SVG = OVERLAYS / "endcard-libertai-message.svg"
LOGO_SVG = OVERLAYS / "endcard-libertai-logo.svg"
MESSAGE_PNG = OUT / "endcard-libertai-message.png"
LOGO_PNG = OUT / "endcard-libertai-logo.png"
VOICEOVER = OUT / "audio" / "libertai-end-voiceover-t2a.wav"
END_CARD = OUT / "libertai-end-card-1080x1920.mp4"
FINAL = OUT / "FILM-sovereign-ai-reboot-final-libertai-1080x1920.mp4"
SHEET = OUT / "FILM-sovereign-ai-reboot-final-libertai-1080x1920.sheet.jpg"

WIDTH = 1080
HEIGHT = 1920
FPS = 24
END_CARD_SECONDS = 7.0
TRANSITION_SECONDS = 1.0
VOICE_START_BEFORE_TRANSITION_SECONDS = 1.05


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


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


def render_png(svg: Path, png: Path) -> None:
    run(
        [
            "magick",
            "-background",
            "none",
            "-density",
            "192",
            str(svg),
            "-resize",
            f"{WIDTH}x{HEIGHT}!",
            str(png),
        ]
    )


def build_end_card() -> None:
    render_png(MESSAGE_SVG, MESSAGE_PNG)
    render_png(LOGO_SVG, LOGO_PNG)
    filter_complex = (
        "[0:v]format=rgba[bg];"
        "[1:v]format=rgba,fade=t=in:st=0.35:d=0.75:alpha=1,"
        "fade=t=out:st=3.05:d=0.85:alpha=1[msg];"
        "[2:v]format=rgba,fade=t=in:st=3.55:d=1.0:alpha=1,"
        "fade=t=out:st=6.55:d=0.45:alpha=1[logo];"
        "[bg][msg]overlay=0:0:format=auto[tmp];"
        "[tmp][logo]overlay=0:0:format=auto,format=yuv420p[v];"
        "[3:a]highpass=f=280,lowpass=f=5200,volume=0.035,"
        "afade=t=in:st=0:d=0.8,afade=t=out:st=6.2:d=0.8[air];"
        "[4:a]volume=0.035,afade=t=in:st=0:d=1.2,afade=t=out:st=6.0:d=1.0[tone];"
        "[air][tone]amix=inputs=2:duration=first,"
        "alimiter=limit=0.85,"
        "aformat=sample_rates=48000:channel_layouts=stereo[a]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-r",
            str(FPS),
            "-t",
            f"{END_CARD_SECONDS:.3f}",
            "-i",
            f"color=c=0x09070f:s={WIDTH}x{HEIGHT}",
            "-loop",
            "1",
            "-t",
            f"{END_CARD_SECONDS:.3f}",
            "-i",
            str(MESSAGE_PNG),
            "-loop",
            "1",
            "-t",
            f"{END_CARD_SECONDS:.3f}",
            "-i",
            str(LOGO_PNG),
            "-f",
            "lavfi",
            "-t",
            f"{END_CARD_SECONDS:.3f}",
            "-i",
            "anoisesrc=color=pink:amplitude=0.018:sample_rate=48000",
            "-f",
            "lavfi",
            "-t",
            f"{END_CARD_SECONDS:.3f}",
            "-i",
            "sine=frequency=147:sample_rate=48000",
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
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
            str(END_CARD),
        ]
    )


def append_end_card(source: Path, final: Path, voiceover: Path) -> None:
    source_duration = duration(source)
    offset = max(source_duration - TRANSITION_SECONDS, 0)
    voice_start = max(offset - VOICE_START_BEFORE_TRANSITION_SECONDS, 0)
    voice_delay_ms = int(round(voice_start * 1000))
    total = source_duration + END_CARD_SECONDS - TRANSITION_SECONDS
    filter_complex = (
        "[0:v]settb=AVTB,fps=24,format=yuv420p[v0];"
        "[1:v]settb=AVTB,fps=24,format=yuv420p[v1];"
        f"[v0][v1]xfade=transition=fade:duration={TRANSITION_SECONDS:.3f}:offset={offset:.3f},"
        "format=yuv420p[v];"
        f"[0:a][1:a]acrossfade=d={TRANSITION_SECONDS:.3f}:c1=tri:c2=tri,"
        "aformat=sample_rates=48000:channel_layouts=stereo[base];"
        "[2:a]aresample=48000,atrim=0:8.15,asetpts=PTS-STARTPTS,"
        "volume=1.08,afade=t=in:st=0:d=0.18,afade=t=out:st=7.65:d=0.45,"
        f"adelay={voice_delay_ms}|{voice_delay_ms},"
        f"apad=whole_dur={total:.3f},"
        "asplit=2[vo_sc][vo_mix];"
        "[base][vo_sc]sidechaincompress=threshold=0.036:ratio=7:"
        "attack=35:release=420:makeup=1[duck];"
        "[duck][vo_mix]amix=inputs=2:duration=first:normalize=0,"
        "alimiter=limit=0.9,loudnorm=I=-15:TP=-1.5:LRA=9,"
        "aformat=sample_rates=48000:channel_layouts=stereo[a]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(source),
            "-i",
            str(END_CARD),
            "-i",
            str(voiceover),
            "-filter_complex",
            filter_complex,
            "-map",
            "[v]",
            "-map",
            "[a]",
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
            str(final),
        ]
    )


def make_sheet(final: Path, sheet: Path) -> None:
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(final),
            "-vf",
            "fps=1/4,scale=270:-1,tile=4x5",
            "-frames:v",
            "1",
            str(sheet),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--voiceover", type=Path, default=VOICEOVER)
    parser.add_argument("--final", type=Path, default=FINAL)
    parser.add_argument("--sheet", type=Path, default=SHEET)
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"missing source film: {args.source}")
    if not args.voiceover.exists():
        raise SystemExit(f"missing voiceover: {args.voiceover}")
    build_end_card()
    append_end_card(args.source, args.final, args.voiceover)
    make_sheet(args.final, args.sheet)
    run(["ffmpeg", "-v", "error", "-i", str(args.final), "-f", "null", "-"])
    print(args.final)
    print(args.sheet)
    print(END_CARD)


if __name__ == "__main__":
    main()
