#!/usr/bin/env python3
"""Mux the dialogue-first sovereign AI cut.

The picture track is the long story cut. All generated clip ambience/music is
discarded; the only audio is the LTX-2.3 text-to-audio dialogue track.
"""

from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"
PICTURE = OUT / "FILM-sovereign-ai-story-long-1080x1920.mp4"
DIALOGUE = OUT / "audio" / "svai-t2a-dialogue-full.wav"
OUTPUT = OUT / "FILM-sovereign-ai-dialogue-cut-1080x1920.mp4"


def main() -> None:
    if not PICTURE.exists():
        raise SystemExit(f"missing picture track: {PICTURE}")
    if not DIALOGUE.exists():
        raise SystemExit(f"missing dialogue track: {DIALOGUE}")

    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(PICTURE),
        "-i",
        str(DIALOGUE),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-filter:a",
        "aresample=48000,loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.92",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(OUTPUT),
    ]
    subprocess.run(cmd, check=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
