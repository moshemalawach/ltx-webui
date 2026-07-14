#!/usr/bin/env python3
"""Shot-lab runner for the rebooted sovereign-AI film.

This script prints or runs reproducible LTX-2.3 HQ two-stage commands for the
new shot plan. It is intentionally shot-based: render candidates, inspect them,
retake failures, then assemble accepted material.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "reboot"
DOC = BASE / "docs" / "sovereign-ai-reboot-treatment.md"
HF_HUB = Path.home() / ".cache" / "huggingface" / "hub"
LTX_REPO = Path(os.environ.get("LTX_REPO_DIR", str(Path.home() / "repos" / "LTX-2")))
LTX_PY = LTX_REPO / ".venv" / "bin" / "python"

NEGATIVE_PROMPT = (
    "readable text, subtitles, captions, title cards, logos, watermarks, UI labels, "
    "blurry, low quality, still image, frozen camera, bad anatomy, deformed hands, "
    "inconsistent face, duplicate people, cartoon, CGI plastic, oversaturated, "
    "glitch, compression artifacts, wrong perspective, mismatched lighting, "
    "robotic voice, incorrect dialogue, random speech"
)


@dataclass(frozen=True)
class ImageRef:
    path: str
    frame: int
    strength: float
    crf: int = 0


@dataclass(frozen=True)
class Shot:
    shot_id: str
    seed: int
    duration: str
    purpose: str
    prompt: str
    images: tuple[ImageRef, ...] = ()


SHOTS: list[Shot] = [
    Shot(
        "s01-dependency",
        7101,
        "8s",
        "Establish dependency on one central AI tower.",
        (
            "Night rain in a small apartment workshop above a dense city. Mara, a practical middle aged "
            "infrastructure engineer with short silver black hair and an amber rain jacket, stands at the "
            "window facing a huge black glass civic AI tower. Thin cold blue data filaments rise from family "
            "photos, tools, and a medical bracelet on the workbench toward the tower outside. She sees the "
            "filaments, turns from stunned to focused, and reaches below the table for a small dark cube. "
            "The camera begins very close on the personal objects, pushes to her reflected face in the rain "
            "streaked glass, then racks focus to the tower. Cinematic natural motion, no readable text, no "
            "logos, no UI labels."
        ),
        (
            ImageRef("keyframes/reboot/mara-apartment-tower.png", 0, 0.95),
        ),
    ),
    Shot(
        "s02-single-point",
        7102,
        "8s",
        "Make the one-cable failure visible.",
        (
            "Inside the same apartment workshop during the storm, Mara opens a wall service panel and reveals "
            "one thick cold blue uplink cable bundled with many smaller civic service wires. She hesitates for "
            "half a second, then pulls the blue cable free. The room lights die, the distant AI tower visible "
            "through the window changes from cold blue to red emergency pulses, and the small cube on the table "
            "emits a faint amber glow. The action is physical and clear: hand on cable, connector leaving the "
            "port, darkness, red tower response, amber cube awakening. Handheld close camera, shallow depth of "
            "field, no readable text, no logos, no UI labels."
        ),
        (
            ImageRef("keyframes/reboot/mara-service-panel.png", 0, 0.95),
            ImageRef("keyframes/reboot/mara-apartment-tower.png", 96, 0.45),
        ),
    ),
    Shot(
        "s03-cost",
        7103,
        "8s",
        "Show the human cost at the clinic.",
        (
            "A small neighborhood clinic during the same storm outage, no readable signs. A medicine fridge "
            "loses its cold blue power light and goes dark. Tomas, a practical clinic technician in a soaked "
            "jacket, grabs the fridge handle and tries to keep it closed while checking a small battery pack. "
            "A child and caregiver wait in the background, anxious but quiet. Red pulses from the distant AI "
            "tower flash through the rain covered clinic window. The camera tracks low along the fridge base, "
            "rises to Tomas's hands, then finds the child in soft focus behind him. Realistic human tension, "
            "no text, no logos, no UI labels."
        ),
        (
            ImageRef("keyframes/reboot/clinic-fridge-tomas.png", 0, 0.95),
        ),
    ),
    Shot(
        "s04-local-first",
        7104,
        "8s",
        "Activate the local node and restore the clinic fridge.",
        (
            "Mara runs into a bare concrete clinic utility corridor with plain blank walls and no signs anywhere, "
            "carrying the small amber local compute cube in both hands. Tomas meets her with two tablets and a "
            "compact battery pack. They kneel on the wet floor and connect the cube with short cables to the "
            "tablets and battery. The amber light grows, travels through the cables, and a nearby medicine fridge "
            "light comes back in warm amber instead of cold blue. Tomas looks from the fridge to Mara and "
            "understands. The camera follows her from behind, drops to hand level, then circles the connected "
            "devices. Clear practical action, blank walls, no readable text, no exit sign, no logos, no UI labels."
        ),
        (
            ImageRef("keyframes/reboot/local-activation-clinic.png", 0, 0.95),
            ImageRef("keyframes/reboot/clinic-fridge-tomas.png", 96, 0.45),
        ),
    ),
    Shot(
        "s05-mesh",
        7105,
        "8s",
        "Turn the local node into a neighborhood mesh.",
        (
            "Rainy apartment courtyard at night. Neighbors emerge from doorways and pass small transparent "
            "amber compute nodes hand to hand across balconies, windows, and the wet courtyard. Each node links "
            "to the next with short warm light paths that stay low and human scale. Mara directs quietly from "
            "the center while Tomas carries a node toward the clinic entrance. The huge red AI tower is visible "
            "far away but no longer fills the frame. The camera starts low in wet pavement reflections, follows "
            "running feet, then rises to reveal the courtyard becoming a mesh. No readable signs, no logos, "
            "no UI labels."
        ),
        (
            ImageRef("keyframes/reboot/courtyard-mesh.png", 0, 0.95),
        ),
    ),
    Shot(
        "s06-consent",
        7106,
        "8s",
        "Show consent and exit as physical governance.",
        (
            "Dawn inside a civic workshop after the storm. Neighbors stand around a long table covered with "
            "independent amber local compute nodes. Each person places a small plain physical token beside their "
            "own node before it joins the mesh. One elderly resident calmly removes their token; their node fades "
            "to standby while all other nodes continue glowing. Mara watches and nods, relieved because exit works. "
            "The camera moves laterally at table height across hands, faces, tokens, and separate nodes, showing "
            "that no single machine controls the room. Warm morning light, no readable text, no logos, no UI labels."
        ),
        (
            ImageRef("keyframes/reboot/dawn-governance-room.png", 0, 0.95),
        ),
    ),
    Shot(
        "s07-city-still-here",
        7107,
        "8s",
        "Resolve with a living city and a dark central tower.",
        (
            "Dawn city after the storm. The camera starts close on the workshop table where many separate amber "
            "local nodes pulse softly, then moves past Mara's shoulder to the window and out to a wide vertical "
            "view of the neighborhood. Warm amber points glow from ordinary apartments, the clinic, rooftops, and "
            "street corners. The central black AI tower is far away, completely dark and inactive, with no red "
            "lights and no blue data lanes, no longer dominating the skyline. Mara stands with neighbors, one "
            "person among many, quietly watching the city function without a central master. Gentle natural "
            "movement, warm sunrise, no readable text, no logos, no UI labels."
        ),
        (
            ImageRef("keyframes/reboot/dawn-governance-room.png", 0, 0.70),
            ImageRef("keyframes/reboot/dawn-city-mesh.png", 96, 0.82),
        ),
    ),
]


def find_model(repo: str, pattern: str) -> Path:
    hits = sorted(HF_HUB.glob(f"models--{repo}/snapshots/*/{pattern}"))
    if not hits:
        raise SystemExit(f"missing model: {repo}/{pattern}")
    return hits[-1]


def model_paths() -> dict[str, Path]:
    gemma_config = find_model("google--gemma-3-12b-it-qat-q4_0-unquantized", "config.json")
    return {
        "checkpoint": find_model("Lightricks--LTX-2.3", "ltx-2.3-22b-dev.safetensors"),
        "distilled_lora": find_model("Lightricks--LTX-2.3", "ltx-2.3-22b-distilled-lora-384-1.1.safetensors"),
        "spatial_upsampler": find_model("Lightricks--LTX-2.3", "ltx-2.3-spatial-upscaler-x2-1.1.safetensors"),
        "gemma": gemma_config.parent,
    }


def get_shot(shot_id: str) -> Shot:
    for shot in SHOTS:
        if shot.shot_id == shot_id:
            return shot
    raise SystemExit(f"unknown shot id {shot_id!r}; choose one of: {', '.join(s.shot_id for s in SHOTS)}")


def hq_command(
    shot: Shot,
    *,
    height: int,
    width: int,
    num_frames: int,
    frame_rate: float,
    steps: int,
    seed_offset: int,
    quantization: bool,
    output_path: Path,
) -> list[str]:
    paths = model_paths()
    cmd = [
        str(LTX_PY),
        "-m",
        "ltx_pipelines.ti2vid_two_stages_hq",
        "--checkpoint-path",
        str(paths["checkpoint"]),
        "--distilled-lora",
        str(paths["distilled_lora"]),
        "0.8",
        "--distilled-lora-strength-stage-1",
        "0.25",
        "--distilled-lora-strength-stage-2",
        "0.5",
        "--spatial-upsampler-path",
        str(paths["spatial_upsampler"]),
        "--gemma-root",
        str(paths["gemma"]),
        "--offload",
        "cpu",
        "--max-batch-size",
        "1",
        "--height",
        str(height),
        "--width",
        str(width),
        "--num-frames",
        str(num_frames),
        "--frame-rate",
        str(frame_rate),
        "--num-inference-steps",
        str(steps),
        "--seed",
        str(shot.seed + seed_offset),
        "--prompt",
        shot.prompt,
        "--negative-prompt",
        NEGATIVE_PROMPT,
        "--output-path",
        str(output_path),
    ]
    if quantization:
        cmd += ["--quantization", "fp8-cast"]
    for image in shot.images:
        if image.frame < num_frames:
            cmd += [
                "--image",
                str((BASE / image.path).resolve()),
                str(image.frame),
                str(image.strength),
                str(image.crf),
            ]
    return cmd


def run(cmd: list[str]) -> None:
    env = dict(os.environ)
    env.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")
    subprocess.run(cmd, cwd=LTX_REPO, env=env, check=True)


def ffprobe(path: Path) -> None:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of",
        "json",
        str(path),
    ]
    print(subprocess.check_output(cmd, text=True))


def contact_sheet(video: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        str(video),
        "-vf",
        "fps=1,scale=360:-1,tile=4x2",
        "-frames:v",
        "1",
        str(output),
    ]
    subprocess.run(cmd, check=True)
    print(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("plan")

    dry = sub.add_parser("dry-run")
    dry.add_argument("--height", type=int, default=1472)
    dry.add_argument("--width", type=int, default=832)
    dry.add_argument("--num-frames", type=int, default=129)
    dry.add_argument("--frame-rate", type=float, default=16.0)
    dry.add_argument("--steps", type=int, default=15)
    dry.add_argument("--seed-offset", type=int, default=0)
    dry.add_argument("--no-quantization", action="store_true")

    render = sub.add_parser("render-shot")
    render.add_argument("shot_id")
    render.add_argument("--height", type=int, default=1472)
    render.add_argument("--width", type=int, default=832)
    render.add_argument("--num-frames", type=int, default=129)
    render.add_argument("--frame-rate", type=float, default=16.0)
    render.add_argument("--steps", type=int, default=15)
    render.add_argument("--seed-offset", type=int, default=0)
    render.add_argument("--no-quantization", action="store_true")

    probe = sub.add_parser("render-probe")
    probe.add_argument("--shot-id", default="s01-dependency")
    probe.add_argument("--height", type=int, default=768)
    probe.add_argument("--width", type=int, default=448)
    probe.add_argument("--num-frames", type=int, default=33)
    probe.add_argument("--frame-rate", type=float, default=16.0)
    probe.add_argument("--steps", type=int, default=8)
    probe.add_argument("--seed-offset", type=int, default=900)
    probe.add_argument("--no-quantization", action="store_true")

    audit = sub.add_parser("audit")
    audit.add_argument("video")

    sheet = sub.add_parser("contact-sheet")
    sheet.add_argument("video")
    sheet.add_argument("--output")

    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    if args.cmd == "plan":
        print(json.dumps({"doc": str(DOC), "shots": [asdict(s) for s in SHOTS]}, indent=2))
        return

    if args.cmd == "dry-run":
        for shot in SHOTS:
            output = OUT / f"{shot.shot_id}-seed{shot.seed + args.seed_offset}.mp4"
            cmd = hq_command(
                shot,
                height=args.height,
                width=args.width,
                num_frames=args.num_frames,
                frame_rate=args.frame_rate,
                steps=args.steps,
                seed_offset=args.seed_offset,
                quantization=not args.no_quantization,
                output_path=output,
            )
            print(" ".join(shlex.quote(part) for part in cmd))
        return

    if args.cmd in {"render-shot", "render-probe"}:
        shot = get_shot(args.shot_id if args.cmd == "render-probe" else args.shot_id)
        output = OUT / f"{shot.shot_id}-seed{shot.seed + args.seed_offset}-{args.width}x{args.height}-{args.num_frames}f.mp4"
        cmd = hq_command(
            shot,
            height=args.height,
            width=args.width,
            num_frames=args.num_frames,
            frame_rate=args.frame_rate,
            steps=args.steps,
            seed_offset=args.seed_offset,
            quantization=not args.no_quantization,
            output_path=output,
        )
        print(" ".join(shlex.quote(part) for part in cmd))
        run(cmd)
        ffprobe(output)
        contact_sheet(output, output.with_suffix(".sheet.jpg"))
        return

    if args.cmd == "audit":
        video = Path(args.video)
        ffprobe(video)
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)
        return

    if args.cmd == "contact-sheet":
        video = Path(args.video)
        output = Path(args.output) if args.output else video.with_suffix(".sheet.jpg")
        contact_sheet(video, output)
        return

    raise AssertionError(args.cmd)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
