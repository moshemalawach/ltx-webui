#!/usr/bin/env python3
"""Generate and assemble a longer no-text story cut for the sovereign AI film.

This follows the long-video workflow shape: generate a segment, extract its
last frame, and use that frame as weak continuity conditioning for the next
segment while stronger timed keyframes drive the next dramatic beat.
"""

from __future__ import annotations

import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"
KEYFRAMES = BASE / "keyframes"
RUNS = BASE / "logs" / "story-runs"
API = "http://127.0.0.1:7860"

WIDTH = 832
HEIGHT = 1472
NUM_FRAMES = 249
FRAME_RATE = 16.0
XF = 0.65


@dataclass(frozen=True)
class TimedKeyframe:
    file: str
    frame: int
    strength: float


@dataclass(frozen=True)
class Scene:
    slug: str
    seed: int
    prompt: str
    keyframes: list[TimedKeyframe] = field(default_factory=list)


SCENES = [
    Scene(
        slug="svai-story-01-witness",
        seed=3101,
        keyframes=[
            TimedKeyframe("svai3-01-witness.png", 0, 0.95),
            TimedKeyframe("svai3-02-decision.png", 200, 0.68),
        ],
        prompt=(
            "A single continuous narrative scene, no text. Night apartment during heavy rain. "
            "A middle-aged Afro-European woman infrastructure engineer with short silver-black hair "
            "and an amber rain jacket wakes to cold blue light from a huge centralized AI tower outside. "
            "Private family photos and personal objects on the table begin emitting thin blue data-filaments "
            "toward the rain-streaked window. She crosses the room, follows the filaments with her eyes, "
            "then sees a small warm amber local compute cube under the table and grabs it. The camera starts "
            "intimate on the photos, pans with the blue filaments to the window, then swings back as she moves "
            "decisively to the workbench. Real human motion, urgent but controlled, no readable text, no logos, "
            "no UI labels. Audio: rain on glass, distant transformer hum, small glass vibrations, her breath, "
            "the cold blue hum growing until the amber cube answers with a faint warm tone."
        ),
    ),
    Scene(
        slug="svai-story-02-decision",
        seed=3102,
        keyframes=[
            TimedKeyframe("svai3-02-decision.png", 56, 0.96),
            TimedKeyframe("svai-04-red-outage.png", 210, 0.56),
        ],
        prompt=(
            "A continuous action scene in the same apartment workshop, no text. The woman slams the warm compute "
            "cube onto the workbench, opens its side panel, pulls a cold blue cloud uplink cable out, and connects "
            "a warm amber local mesh cable. The compact device changes from blue to amber as relays click alive. "
            "Outside the window the centralized AI tower notices: its cold blue grid flickers, then turns red. "
            "The action must be physical and readable: hands, cable, click, face reaction, tower response. "
            "Camera moves from tight hands to her face to the tower reflected in the window, then back to the "
            "device as amber light spills across tools. No readable text, no logos, no UI labels. Audio: cable "
            "friction, connector click, relay ticks, blue electrical whine collapsing, red alarm-like sub tone "
            "from the tower, amber harmonic pulse rising."
        ),
    ),
    Scene(
        slug="svai-story-03-blackout",
        seed=3103,
        keyframes=[
            TimedKeyframe("svai3-03-stairwell.png", 56, 0.95),
            TimedKeyframe("svai2-08-street-outage.png", 210, 0.60),
        ],
        prompt=(
            "A continuous escape and consequence scene, no text. City power fails as the central AI tower goes red. "
            "The woman runs from the apartment into a dark concrete stairwell carrying the amber local compute cube "
            "in both hands. Doors open one by one; neighbors step out, first afraid, then drawn by the warm light. "
            "She hands a small node to an older neighbor while still moving down the stairs. The camera follows from "
            "behind, then passes her to reveal the stairwell filling with people and amber light. Through narrow "
            "windows the distant tower pulses red and public screens outside are dead. No readable apartment numbers, "
            "no signs, no logos. Audio: blackout thump, elevator stopping, doors opening, footsteps, rain through "
            "walls, muted voices, warm node pulses answering each other."
        ),
    ),
    Scene(
        slug="svai-story-04-relay",
        seed=3104,
        keyframes=[
            TimedKeyframe("svai3-04-relay.png", 56, 0.96),
            TimedKeyframe("svai-05-dawn-mesh.png", 216, 0.64),
        ],
        prompt=(
            "A continuous relay scene across a rainy courtyard and street, no text. Neighbors carry small amber "
            "local AI nodes out of the building. The woman kneels to connect the first node to a courtyard cable; "
            "then people pass nodes hand to hand through the rain. Warm network lines grow from window to window "
            "and rooftop to rooftop while the distant red central tower loses dominance. The camera starts low with "
            "wet pavement reflections, tracks with running feet, rises to reveal the whole courtyard becoming a "
            "human-scale mesh. Make the movement clear and communal, not abstract. No readable signs, no logos, "
            "no UI labels. Audio: rain, quick footsteps, cable snaps, small devices chiming into sync, red tower "
            "tone breaking apart under the warmer mesh harmony."
        ),
    ),
    Scene(
        slug="svai-story-05-sovereign",
        seed=3105,
        keyframes=[
            TimedKeyframe("svai3-05-workshop.png", 64, 0.96),
            TimedKeyframe("svai2-12-human-circle.png", 216, 0.78),
        ],
        prompt=(
            "A final continuous resolution scene, no text. Dawn after the storm inside a civic workshop. The woman "
            "and neighbors link several transparent local compute cubes into one warm sovereign AI cluster. Children, "
            "elders, and technicians lean in; nobody worships the machine, they work with it. The cluster stabilizes "
            "and amber light travels out through the windows to many small local nodes across the city. In the far "
            "distance the centralized AI tower is dark and no longer commands the skyline. The camera begins behind "
            "her shoulder, circles the table with faces and hands, then pushes in on the cluster as people exhale. "
            "No readable text, no logos, no UI labels, no flags. Audio: morning room tone, soft tools, quiet human "
            "breaths, amber harmonic resolving into warm low strings and air."
        ),
    ),
]


def api_json(path: str, payload: dict[str, Any] | None = None) -> Any:
    url = f"{API}{path}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_for_api() -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            api_json("/api/gallery")
            return
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(0.5)
    raise SystemExit("LTX web UI is not responding on http://127.0.0.1:7860")


def job_by_id(job_id: str) -> dict[str, Any]:
    for job in api_json("/api/jobs"):
        if job["id"] == job_id:
            return job
    raise RuntimeError(f"job disappeared from API: {job_id}")


def submit(scene: Scene, prev_tail: str | None) -> str:
    images: list[dict[str, Any]] = []
    if prev_tail:
        images.append({"file": prev_tail, "frame": 0, "strength": 0.38})
    for kf in scene.keyframes:
        images.append({"file": kf.file, "frame": kf.frame, "strength": kf.strength})
    body = {
        "prompt": f"{scene.slug}. {scene.prompt}",
        "width": WIDTH,
        "height": HEIGHT,
        "num_frames": NUM_FRAMES,
        "frame_rate": FRAME_RATE,
        "seed": scene.seed,
        "keyframes": images,
    }
    result = api_json("/api/generate", body)
    print(f"queued {scene.slug}: {result['id']}")
    return result["id"]


def wait(job_id: str, scene_slug: str) -> str:
    last_status = None
    while True:
        job = job_by_id(job_id)
        status = job["status"]
        if status != last_status:
            print(f"{scene_slug}: {status}")
            last_status = status
        if status == "done":
            print(f"{scene_slug}: {job['file']}")
            return job["file"]
        if status == "failed":
            raise SystemExit(f"{scene_slug} failed: {job.get('error')}")
        time.sleep(8)


def extract_tail(video_file: str, dest_name: str) -> None:
    video = OUT / video_file
    dest = KEYFRAMES / dest_name
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-sseof",
            "-0.16",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-update",
            "1",
            str(dest),
        ],
        check=True,
    )


def duration(path: str) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(OUT / path),
        ],
        text=True,
    ).strip()
    return float(out)


def build_film(files: list[str]) -> Path:
    durs = [duration(f) for f in files]
    total = sum(durs) - XF * (len(durs) - 1)
    scene3_start = durs[0] + durs[1] - 2 * XF
    fade_out = total - 4.5

    inputs: list[str] = []
    for file in files:
        inputs += ["-i", str(OUT / file)]

    drone_i = len(files)
    sub_i = drone_i + 1
    warm_i = drone_i + 2
    air_i = drone_i + 3
    pulse_i = drone_i + 4
    hit_i = drone_i + 5
    inputs += [
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=41:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=82:sample_rate=48000",
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
        "anoisesrc=color=pink:sample_rate=48000:amplitude=0.026",
        "-f",
        "lavfi",
        "-t",
        f"{total:.2f}",
        "-i",
        "sine=frequency=108:sample_rate=48000",
        "-f",
        "lavfi",
        "-t",
        "2.2",
        "-i",
        "sine=frequency=50:sample_rate=48000",
    ]

    fc: list[str] = []
    for i in range(len(files)):
        fc.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setpts=PTS-STARTPTS,fps=25,settb=AVTB,"
            "eq=contrast=1.045:saturation=1.035,vignette=PI/7,format=yuv420p"
            f"[v{i}]"
        )
        fc.append(
            f"[{i}:a]aresample=48000,asetpts=PTS-STARTPTS,"
            "afade=t=in:d=0.10,afade=t=out:st="
            f"{max(durs[i] - 0.55, 0):.2f}:d=0.45,volume=0.70[a{i}]"
        )

    current = "v0"
    current_duration = durs[0]
    for i in range(1, len(files)):
        label = f"vx{i}" if i < len(files) - 1 else "vfilm"
        fc.append(f"[{current}][v{i}]xfade=transition=fade:duration={XF}:offset={current_duration - XF:.2f}[{label}]")
        current = label
        current_duration += durs[i] - XF

    current = "a0"
    for i in range(1, len(files)):
        label = f"ax{i}" if i < len(files) - 1 else "amb"
        fc.append(f"[{current}][a{i}]acrossfade=d={XF}:c1=tri:c2=tri[{label}]")
        current = label

    fc.append(
        f"[{drone_i}:a]aformat=channel_layouts=stereo,volume=0.070,"
        f"afade=t=in:d=4.0,afade=t=out:st={fade_out:.2f}:d=4.2[drone]"
    )
    fc.append(
        f"[{sub_i}:a]aformat=channel_layouts=stereo,volume=0.035,"
        f"afade=t=in:d=8.0,afade=t=out:st={fade_out:.2f}:d=4.0[sub]"
    )
    fc.append(
        f"[{warm_i}:a]aformat=channel_layouts=stereo,volume=0.056,"
        f"afade=t=in:st={scene3_start:.2f}:d=14.0,afade=t=out:st={fade_out:.2f}:d=4.2[warm]"
    )
    fc.append(
        f"[{air_i}:a]aformat=channel_layouts=stereo,highpass=f=240,lowpass=f=4200,"
        f"volume=0.13,afade=t=in:d=1.5,afade=t=out:st={fade_out:.2f}:d=3.5[air]"
    )
    fc.append(
        f"[{pulse_i}:a]aformat=channel_layouts=stereo,tremolo=f=0.72:d=0.82,"
        f"volume=0.028,afade=t=in:st=18.0:d=10.0,afade=t=out:st={fade_out:.2f}:d=3.0[pulse]"
    )
    delay_ms = int(scene3_start * 1000)
    fc.append(
        f"[{hit_i}:a]aformat=channel_layouts=stereo,afade=t=out:st=0.22:d=1.8,"
        f"volume=0.16,adelay={delay_ms}|{delay_ms}[hit]"
    )
    fc.append("[drone][sub][warm][air][pulse][hit]amix=inputs=6:duration=longest:normalize=0[score]")
    fc.append("[amb][score]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.88,loudnorm=I=-15:TP=-1.5[afilm]")

    output = OUT / "FILM-sovereign-ai-story-long-1080x1920.mp4"
    subprocess.run(
        [
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
        ],
        check=True,
    )
    print(f"built {output} ({total:.2f}s)")
    return output


def main() -> None:
    RUNS.mkdir(parents=True, exist_ok=True)
    wait_for_api()
    files: list[str] = []
    prev_tail: str | None = None
    for idx, scene in enumerate(SCENES, start=1):
        job_id = submit(scene, prev_tail)
        file = wait(job_id, scene.slug)
        files.append(file)
        prev_tail = f"svai3-tail-{idx:02d}.png"
        extract_tail(file, prev_tail)

    run_path = RUNS / f"{time.strftime('%Y%m%d-%H%M%S')}-sovereign-story.json"
    run_path.write_text(json.dumps({"files": files}, indent=2), encoding="utf-8")
    build_film(files)


if __name__ == "__main__":
    main()
