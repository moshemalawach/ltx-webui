#!/usr/bin/env python3
"""Build a tighter story cut from selected reboot shot ranges."""

from __future__ import annotations

from dataclasses import dataclass
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "reboot"
KEYFRAMES = BASE / "keyframes" / "reboot"
SCORE = OUT / "audio" / "svai-reboot-t2a-score.wav"


@dataclass(frozen=True)
class Segment:
    label: str
    path: Path
    start: float
    seconds: float


SEGMENTS = [
    Segment("cold reliance: Mara watches the tower", OUT / "s01-dependency-seed7101-832x1472-129f.mp4", 0.00, 2.15),
    Segment("personal stake: the workbench family photo", OUT / "s01-dependency-seed7101-832x1472-129f.mp4", 2.05, 1.35),
    Segment("decision: she turns back to the interface", OUT / "s01-dependency-seed7101-832x1472-129f.mp4", 3.05, 2.10),
    Segment("single point: rack access", OUT / "s02-single-point-seed7102-832x1472-129f.mp4", 0.00, 1.35),
    Segment("single point: the uplink cable", OUT / "s02-single-point-seed7102-832x1472-129f.mp4", 1.05, 3.20),
    Segment("central failure: tower alarm", OUT / "s02-single-point-seed7102-832x1472-129f.mp4", 5.55, 2.35),
    Segment("human cost: clinic fridge and waiting child", OUT / "s03-cost-seed7103-832x1472-129f.mp4", 0.00, 2.95),
    Segment("local first: portable node comes online", KEYFRAMES / "local-activation-clinic.png", 0.00, 2.65),
    Segment("restoration: the clinic light returns", OUT / "s04-local-first-seed7104-832x1472-129f.mp4", 4.05, 2.80),
    Segment("mesh spreads: neighbors share local nodes", KEYFRAMES / "courtyard-mesh.png", 0.00, 3.30),
    Segment("consent: community table", OUT / "s06-consent-seed7106-832x1472-129f.mp4", 0.00, 5.35),
    Segment("sovereign hardware: small cubes, many owners", OUT / "s06-consent-seed7106-832x1472-129f.mp4", 5.65, 1.95),
    Segment("city still here: the tower is dark", OUT / "s07-city-still-here-seed7207-832x1472-129f.mp4", 3.05, 4.95),
]

SOURCE = OUT / "FILM-sovereign-ai-reboot-v2-story-cut-1080x1920.mp4"
SHEET = OUT / "FILM-sovereign-ai-reboot-v2-story-cut-1080x1920.sheet.jpg"

WIDTH = 1080
HEIGHT = 1920
FPS = 24


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


def atempo_chain(speed: float) -> str:
    parts: list[float] = []
    while speed > 2.0:
        parts.append(2.0)
        speed /= 2.0
    while speed < 0.5:
        parts.append(0.5)
        speed /= 0.5
    parts.append(speed)
    return ",".join(f"atempo={part:.6f}" for part in parts)


def is_image(path: Path) -> bool:
    return path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}


def validate() -> None:
    missing = [str(segment.path) for segment in SEGMENTS if not segment.path.exists()]
    if missing:
        raise SystemExit("missing source clips:\n" + "\n".join(sorted(set(missing))))
    if not SCORE.exists():
        raise SystemExit(f"missing continuous score: {SCORE}")

    durations = {path: duration(path) for path in {segment.path for segment in SEGMENTS} if not is_image(path)}
    overrun = [
        f"{segment.label}: {segment.start + segment.seconds:.2f}s > {durations[segment.path]:.2f}s"
        for segment in SEGMENTS
        if not is_image(segment.path) and segment.start + segment.seconds > durations[segment.path] + 0.05
    ]
    if overrun:
        raise SystemExit("segment range exceeds clip duration:\n" + "\n".join(overrun))


def build_source() -> None:
    validate()
    total = sum(segment.seconds for segment in SEGMENTS)
    score_duration = duration(SCORE)
    score_speed = score_duration / total

    inputs: list[str] = []
    for segment in SEGMENTS:
        if is_image(segment.path):
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{segment.seconds:.3f}", "-i", str(segment.path)]
        else:
            inputs += ["-i", str(segment.path)]
    inputs += ["-i", str(SCORE)]

    video_parts = []
    for index, segment in enumerate(SEGMENTS):
        if is_image(segment.path):
            frames = max(int(round(segment.seconds * FPS)), 1)
            video_parts.append(
                f"[{index}:v]scale={WIDTH * 11 // 10}:{HEIGHT * 11 // 10}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH * 11 // 10}:{HEIGHT * 11 // 10},"
                f"zoompan=z='1+0.035*on/{frames}':"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d=1:s={WIDTH}x{HEIGHT}:fps={FPS},"
                f"trim=duration={segment.seconds:.3f},setpts=PTS-STARTPTS,setsar=1,"
                "eq=contrast=1.035:saturation=1.025:brightness=-0.008,"
                "format=yuv420p"
                f"[v{index}]"
            )
        else:
            video_parts.append(
                f"[{index}:v]trim=start={segment.start:.3f}:duration={segment.seconds:.3f},"
                "setpts=PTS-STARTPTS,"
                f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
                f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},"
                "eq=contrast=1.045:saturation=1.035:brightness=-0.012,"
                "format=yuv420p"
                f"[v{index}]"
            )

    concat_inputs = "".join(f"[v{index}]" for index in range(len(SEGMENTS)))
    score_index = len(SEGMENTS)
    score_filter = (
        f"[{score_index}:a]aresample=48000,atrim=0:{score_duration:.3f},asetpts=PTS-STARTPTS,"
        f"{atempo_chain(score_speed)},"
        f"atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
        "afade=t=in:st=0:d=0.8,"
        f"afade=t=out:st={max(total - 1.8, 0):.3f}:d=1.6,"
        "loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=0.92,"
        "aformat=sample_rates=48000:channel_layouts=stereo[aout]"
    )
    filter_complex = (
        ";".join(video_parts)
        + ";"
        + f"{concat_inputs}concat=n={len(SEGMENTS)}:v=1:a=0[vout];"
        + score_filter
    )

    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
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
            str(SOURCE),
        ]
    )


def make_sheet() -> None:
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(SOURCE),
            "-vf",
            "fps=1/3,scale=270:-1,tile=4x4",
            "-frames:v",
            "1",
            str(SHEET),
        ]
    )


def main() -> None:
    build_source()
    make_sheet()
    run(["ffmpeg", "-v", "error", "-i", str(SOURCE), "-f", "null", "-"])
    print(f"{SOURCE} ({duration(SOURCE):.2f}s)")
    print(SHEET)
    print("edit decision list:")
    cursor = 0.0
    for segment in SEGMENTS:
        print(f"{cursor:05.2f}-{cursor + segment.seconds:05.2f}  {segment.label}")
        cursor += segment.seconds


if __name__ == "__main__":
    main()
