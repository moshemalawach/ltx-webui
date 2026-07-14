#!/usr/bin/env python3
"""Shot-lab runner for "The Off Switch" LibertAI brand film.

Widescreen 2.31:1 (1920x832), 121 frames @ 24 fps, two-stage HQ pipeline,
frame-0 keyframe conditioning. Render candidates, QC, retake failures,
then assemble. See docs/libertai-offswitch-treatment.md.
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
OUT = BASE / "outputs" / "offswitch"
KEY = "keyframes/offswitch"
DOC = BASE / "docs" / "libertai-offswitch-treatment.md"
HF_HUB = Path.home() / ".cache" / "huggingface" / "hub"
LTX_REPO = Path(os.environ.get("LTX_REPO_DIR", str(Path.home() / "repos" / "LTX-2")))
LTX_PY = LTX_REPO / ".venv" / "bin" / "python"

NEGATIVE_PROMPT = (
    "readable text, subtitles, captions, title cards, logos, watermarks, UI labels, "
    "blurry, low quality, still image, frozen camera, bad anatomy, deformed hands, "
    "duplicate people, cartoon, CGI plastic, oversaturated, glitch, compression "
    "artifacts, wrong perspective, mismatched lighting, jump cut, scene change"
)


@dataclass(frozen=True)
class Shot:
    shot_id: str
    seed: int
    purpose: str
    prompt: str
    keyframe: str
    strength: float = 0.95


SHOTS: list[Shot] = [
    Shot(
        "s01-fiber",
        8101,
        "Act 1 open: data leaving, macro scale.",
        (
            "Extreme macro of hair-thin glass fiber optic strands in darkness. Pulses of electric blue "
            "light travel along the fibers in one direction, left to right, in rhythmic waves. The camera "
            "drifts slowly sideways while the shallow focus plane slides across the strands, making bokeh "
            "points bloom and sharpen. Deep black background, cold clinical palette. Audio: a soft cold "
            "electronic hum with faint rhythmic data pulses."
        ),
        f"{KEY}/s01-fiber.png",
    ),
    Shot(
        "s02-window",
        8102,
        "Your data leaves your home.",
        (
            "Night exterior of a single lit apartment window on a dark brick facade. Inside, a silhouetted "
            "person types at a laptop. A thin electric-blue filament of light rises steadily from the laptop, "
            "through the window glass, up into the black sky, flickering slightly with each keystroke. The "
            "camera pushes in very slowly toward the window. Fine rain drifts through frame. Audio: distant "
            "city at night, soft rain, a faint rising electrical whine."
        ),
        f"{KEY}/s02-window.png",
    ),
    Shot(
        "s03-threads",
        8103,
        "The whole city drains to one point.",
        (
            "High aerial over a dense city at night. Thousands of thin electric blue light threads rise from "
            "rooftops and windows, undulating gently, all bending toward a single bright point on the horizon. "
            "The threads pulse as data flows along them. The camera drifts slowly forward over the city. "
            "Atmospheric haze catches the blue light. Audio: vast airy wind, layered soft data pulses, a low "
            "ominous drone building."
        ),
        f"{KEY}/s03-threads.png",
    ),
    Shot(
        "s04-monolith",
        8104,
        "The tower reveal: scale and ownership.",
        (
            "A colossal featureless black data-center monolith towers above a sea of fog at night. Hundreds "
            "of thin electric blue light threads stream into its flanks from below the fog, rippling as they "
            "feed it. Slow vertical lanes of blue light climb the monolith's face. The camera rises slowly, "
            "revealing more of its impossible height. Fog rolls softly around the base. Audio: deep sub-bass "
            "presence, cold choral drone, faint electrical crackle."
        ),
        f"{KEY}/s04-monolith.png",
    ),
    Shot(
        "s05-hall",
        8105,
        "Inside: sterile infinity, no people.",
        (
            "Inside an infinite server corridor in perfect one-point perspective. Endless identical black "
            "server racks with cold blue status lights recede to a vanishing point. The camera dollies forward "
            "slowly and steadily down the exact center of the aisle. Status lights blink in slow waves that "
            "travel toward the vanishing point. Cold reflections slide across the polished dark floor. Audio: "
            "dense server-fan roar, precise rhythmic relay clicks echoing."
        ),
        f"{KEY}/s05-hall.png",
    ),
    Shot(
        "s06-switch",
        8106,
        "One company. One building. One switch.",
        (
            "Extreme macro of a massive industrial breaker lever in brushed black metal, a red warning lamp "
            "glowing beside it. A black-gloved hand is already wrapped tightly around the lever and stays "
            "locked on it for the whole shot, fingers never opening. The glove leather creases as the grip "
            "tightens, and the lever slowly tilts a few centimeters downward. The red lamp pulses faster and "
            "brighter, throwing hard red light across the metal. The camera pushes in very slowly. Hard red "
            "and cold blue rim light on black. Audio: low menacing hum swelling, electronic beeping "
            "accelerating, creak of metal under the glove."
        ),
        f"{KEY}/s06-switch.png",
    ),
    Shot(
        "s07-shutdown",
        8107,
        "The turn: the tower dies.",
        (
            "The colossal black monolith at night from mid distance against a clean empty dark night sky. "
            "Its vertical blue data lanes drain to black from the top downward, floor by floor, like liquid "
            "emptying. At the crown a single red light pulses twice, then everything goes dark. The sky stays "
            "clean and clear, no smoke, no clouds forming. Camera nearly static with a very slow subtle push. "
            "Audio: a huge power-down descending whoosh, sub-bass thud, then ringing silence with wind."
        ),
        f"{KEY}/s07-shutdown.png",
    ),
    Shot(
        "s08-citydies",
        8108,
        "The blackout cascades to everyone.",
        (
            "High wide aerial of a sprawling city at night. Entire districts of streetlights and windows go "
            "dark in sweeping waves, the blackout traveling across the grid from the horizon toward the "
            "camera, until only scattered faint lights remain. Camera holds nearly static, floating. Audio: "
            "cascading electrical shutdown thumps growing closer, city hum collapsing into silence."
        ),
        f"{KEY}/s08-citydies.png",
    ),
    Shot(
        "s09-darkroom",
        8109,
        "The human beat in the dark.",
        (
            "A dark living room at night. One person sits silhouetted on a sofa, their face faintly lit by a "
            "phone screen. The phone screen flickers and dies, and the room falls into near-total darkness, "
            "leaving only a faint silhouette against the window. The person slowly lowers the dead phone. The "
            "camera pushes in very slowly. Audio: quiet room tone, a soft electronic blip as the screen dies, "
            "a single human breath in the dark."
        ),
        f"{KEY}/s09-darkroom.png",
    ),
    Shot(
        "s10-ember",
        8110,
        "Act 2 turn: local intelligence wakes.",
        (
            "A dark kitchen. On a rough wooden table, a palm-sized translucent compute cube wakes: a warm "
            "amber core ignites inside it, breathing brighter, spilling gold light across the wood grain and "
            "a ceramic cup. Dust motes drift in the amber glow. The camera pushes in slowly at table level. "
            "Audio: a single warm rising tone, soft crackle of the core igniting, gentle silence around it."
        ),
        f"{KEY}/s10-ember.png",
    ),
    Shot(
        "s11-circuit",
        8111,
        "Intelligence on your machine.",
        (
            "Extreme macro of a dark circuit board. Warm amber light ignites at a central chip and spreads "
            "outward along the copper traces like city streets lighting up at night, junction by junction, "
            "until the whole board glows gold. The camera drifts slowly across the board at macro distance, "
            "focus following the spreading light. Audio: delicate cascading electronic sparkles over a warm "
            "swelling harmonic chord."
        ),
        f"{KEY}/s11-circuit.png",
    ),
    Shot(
        "s12-block",
        8112,
        "The neighborhood lights up.",
        (
            "Night facade of an old apartment block. Windows ignite one by one with warm amber light, "
            "spreading across the building. Thin soft threads of warm light arc gently from window to window, "
            "linking them. A wet street below reflects the growing warmth. The camera rises slowly up the "
            "facade. Audio: warm hopeful swelling score, faint neighborhood life, soft night air."
        ),
        f"{KEY}/s12-block.png",
    ),
    Shot(
        "s13-mesh",
        8113,
        "The mesh spreads city-wide.",
        (
            "Aerial over a city at first light of dawn. A delicate web of warm amber light threads links "
            "rooftops and neighborhoods, new connections lighting up one after another, spreading outward "
            "across the city like a living constellation. The indigo sky brightens slowly at the horizon. The "
            "camera drifts forward gently. Audio: uplifting airy score building, soft chimes as new links "
            "ignite, morning wind."
        ),
        f"{KEY}/s13-mesh.png",
    ),
    Shot(
        "s14-dawn",
        8114,
        "Resolution: dawn, the tower dead and small.",
        (
            "Very wide sunrise view of a city glowing with thousands of small warm amber points from "
            "apartments and rooftops. The golden sun breaks the horizon, light sweeping across the buildings. "
            "Far away a single dark monolith tower stands unlit and lifeless. Birds cross the frame. The "
            "camera pulls back very slowly and slightly rises. Audio: warm resolved chord, morning city "
            "waking, birdsong."
        ),
        f"{KEY}/s14-dawn.png",
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
    keyframe = (BASE / shot.keyframe).resolve()
    if keyframe.exists():
        cmd += ["--image", str(keyframe), "0", str(shot.strength), "0"]
    else:
        print(f"warning: keyframe missing, rendering unconditioned: {keyframe}", file=sys.stderr)
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
        "fps=2,scale=480:-1,tile=3x4",
        "-frames:v",
        "1",
        str(output),
    ]
    subprocess.run(cmd, check=True)
    print(output)


def render(shot: Shot, args: argparse.Namespace) -> None:
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


def add_render_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--height", type=int, default=832)
    p.add_argument("--width", type=int, default=1920)
    p.add_argument("--num-frames", type=int, default=121)
    p.add_argument("--frame-rate", type=float, default=24.0)
    p.add_argument("--steps", type=int, default=15)
    p.add_argument("--seed-offset", type=int, default=0)
    p.add_argument("--no-quantization", action="store_true")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("plan")

    render_p = sub.add_parser("render-shot")
    render_p.add_argument("shot_id")
    add_render_args(render_p)

    render_all = sub.add_parser("render-all")
    render_all.add_argument("--skip-existing", action="store_true")
    add_render_args(render_all)

    probe = sub.add_parser("render-probe")
    probe.add_argument("--shot-id", default="s04-monolith")
    add_render_args(probe)
    probe.set_defaults(height=832, width=1920, num_frames=33, steps=8, seed_offset=900)

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

    if args.cmd == "render-shot":
        render(get_shot(args.shot_id), args)
        return

    if args.cmd == "render-probe":
        shot = get_shot(args.shot_id)
        render(shot, args)
        return

    if args.cmd == "render-all":
        for shot in SHOTS:
            output = OUT / f"{shot.shot_id}-seed{shot.seed + args.seed_offset}-{args.width}x{args.height}-{args.num_frames}f.mp4"
            if args.skip_existing and output.exists():
                print(f"skip existing {output.name}")
                continue
            render(shot, args)
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
