#!/usr/bin/env python3
"""Phase 0 quick probes for the UGC Factory upgrade.

Sequential, one GPU job at a time. Cheap settings: 121 frames @ 24 fps,
736x1280 vertical. Writes clips + manifest.json into scripts/bakeoff/out/.

Probes:
  templates    A/B/C UGC-look template arms x 2 seeds (6 clips, distilled)
  consistency  persona first-frame/DNA ladder (4 clips, distilled)
  ia2v         t2a VO line -> a2vid_two_stage talking head (1 clip)
  all          everything above in order

Usage: python scripts/bakeoff/run_probes.py all
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
OUT = BASE / "scripts" / "bakeoff" / "out"
HF_HUB = Path.home() / ".cache" / "huggingface" / "hub"
LTX_REPO = Path(os.environ.get("LTX_REPO_DIR", str(Path.home() / "repos" / "LTX-2")))
LTX_PY = LTX_REPO / ".venv" / "bin" / "python"

WIDTH, HEIGHT = 704, 1280  # both divisible by 64 (two-stage requirement)
FRAMES, FPS = 121, 24  # ~5.0 s
SEEDS = [4242, 9107]

# ---------------------------------------------------------------- model paths

def find_model(repo: str, pattern: str) -> Path:
    hits = sorted(HF_HUB.glob(f"models--{repo}/snapshots/*/{pattern}"))
    if not hits:
        raise SystemExit(f"missing model: {repo}/{pattern}")
    return hits[-1]


def model_paths() -> dict[str, Path]:
    return {
        "distilled": find_model("Lightricks--LTX-2.3", "ltx-2.3-*distilled-[0-9]*.safetensors"),
        "checkpoint": find_model("Lightricks--LTX-2.3", "ltx-2.3-22b-dev.safetensors"),
        "distilled_lora": find_model("Lightricks--LTX-2.3", "ltx-2.3-22b-distilled-lora-384-1.1.safetensors"),
        "spatial_upsampler": find_model("Lightricks--LTX-2.3", "ltx-2.3-spatial-upscaler-x2*.safetensors"),
        "gemma": find_model("google--gemma-3-12b-it-qat-q4_0-unquantized", "config.json").parent,
    }

# ---------------------------------------------------------------- prompts

SPOKEN = "Sola made my routine feel easier than I expected."

GUARD = (
    "Spoken words are audio only and never appear visually. The frame contains no "
    "subtitles, captions, title cards, watermarks, interface elements, or generated "
    "readable text. Clothing and the set are plain and unbranded with no lettering."
)

# Arm A: what the app's buildPrompt() produces today for the default Sola brief.
ARM_A = (
    "Authentic creator-style social video in vertical smartphone framing, captured on a "
    "modern smartphone as one continuous take. a relatable customer in their late twenties "
    "demonstrates the product in one simple continuous action. A bright lived-in bathroom "
    "in the morning. Handheld front-facing phone camera at arm's length, natural window "
    "light, casual neutral clothes. The creator holds the serum close to camera, dispenses "
    "one drop, applies it to one cheek, then looks back into the lens. The framing has "
    "subtle natural hand movement and one gentle push closer when the product is shown. "
    "The product is Sola Barrier Serum, Daily ceramide face serum; its shape, packaging, "
    "and color remain consistent throughout the shot. The performance is candid, "
    "conversational, and slightly imperfect, with direct eye contact, natural gestures, "
    f"realistic pauses, and accurate lip sync. The creator says exactly: \"{SPOKEN}\" "
    "The spoken line and one simple primary product action finish by 4.2 seconds, followed "
    "by a natural silent hold through the end of the 5-second take. Natural room tone and "
    f"clear close-recorded speech. {GUARD} Photorealistic skin texture, believable hands, "
    "everyday lighting, real UGC rather than a polished commercial."
)

# Arm B: research imperfection template, negatives phrased positively.
ARM_B = (
    "Ultra-realistic vertical 9:16 video that looks like a real person filmed it on their "
    "phone in one continuous take. A relatable woman in her late twenties films herself at "
    "arm's length with the front camera in her real, slightly cluttered bathroom in the "
    "morning: toothbrush cup, hair ties, and everyday products visible on the counter. "
    "Handheld phone camera with tiny natural wobble and micro-shake, slightly imperfect "
    "framing with the subject a little off-center. Natural window light with uneven "
    "exposure, one side of the face brighter than the other. Natural skin texture with "
    "visible pores and small imperfections, plain everyday clothes with slightly messy "
    "hair. She holds up Sola Barrier Serum, a daily ceramide face serum, dispenses one "
    "drop and applies it to one cheek while keeping casual eye contact; the bottle's "
    "shape, packaging, and color remain consistent throughout. She speaks casually with "
    f"realistic pauses and accurate lip sync, saying exactly: \"{SPOKEN}\" The line and "
    "the single product action finish by 4.2 seconds with a natural silent hold to the end. "
    "Natural room tone and close phone-mic speech with slight room echo. The image has "
    "realistic smartphone sharpness and mild phone-camera compression, like real UGC "
    f"footage rather than a commercial. {GUARD}"
)

# Arm C: Arm B + literal inline negations (research finding, may be inert at CFG=1).
ARM_C = (
    ARM_B
    + " No studio lighting, no model-perfect skin, no warped hands, no floating product, "
    "no music, no color grading, no cinematic depth of field."
)

# Persona for the consistency ladder.
DNA = (
    "Maya, a woman in her late twenties with shoulder-length wavy dark brown hair parted "
    "in the middle, warm brown eyes, light freckles across her nose and cheeks, a small "
    "beauty mark above the left corner of her lip, wearing a sage green ribbed cardigan "
    "over a plain white tee."
)

CONSISTENCY_ACTION = (
    "films herself at arm's length with her phone's front camera in a bright, slightly "
    "cluttered kitchen, casually talking to the camera with natural gestures, then smiles "
    "and tucks her hair behind her ear. Handheld with tiny natural wobble, subject "
    "slightly off-center, natural window light with uneven exposure, visible skin texture "
    "and pores, realistic smartphone sharpness. Natural room tone, no speech. "
) + GUARD

STILL_PROMPT = (
    f"iPhone front-camera selfie photo, vertical 9:16. {DNA} She is in a bright, slightly "
    "cluttered kitchen with morning window light, uneven natural exposure, one side of her "
    "face brighter. Arm's-length selfie framing, slightly off-center, looking at the "
    "camera with a relaxed natural expression. Realistic smartphone photo with visible "
    "skin texture and pores, mild phone-camera compression, no filters, no text."
)

VO_LINE = "Honestly, this little serum changed my whole morning routine."
VO_VOICE = (
    "A single natural young female voice, casual and friendly like a creator talking to "
    "her phone, conversational pace, close phone-microphone sound with slight room tone. "
    "Speech only, no music, no ambience, no sound effects."
)
VO_NEGATIVE = (
    "music, score, ambience, sound effects, crowd, multiple speakers, singing, robotic "
    "voice, shouting, whispering, distorted audio, clipping, echo, stutter, repeated "
    "words, wrong words, extra words, silence gap"
)

AVATAR_PROMPT = (
    "A relatable woman in her late twenties films herself at arm's length with her "
    "phone's front camera in a bright, slightly cluttered kitchen, talking directly to "
    "the camera with natural gestures, direct eye contact, and accurate lip sync. The "
    "camera is locked in a steady arm's-length selfie framing with only tiny natural "
    "handheld wobble, subject slightly off-center. Natural window light with uneven "
    "exposure, visible skin texture and pores, realistic smartphone sharpness and mild "
    f"compression, real UGC footage rather than a commercial. {GUARD}"
)

# ---------------------------------------------------------------- runners

def run(cmd: list[str], log_name: str) -> float:
    env = dict(os.environ)
    env.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")
    OUT.mkdir(parents=True, exist_ok=True)
    log = OUT / f"{log_name}.log"
    started = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] {log_name} ...", flush=True)
    with log.open("w") as fh:
        subprocess.run(cmd, cwd=LTX_REPO, env=env, check=True, stdout=fh, stderr=subprocess.STDOUT)
    elapsed = time.time() - started
    print(f"[{time.strftime('%H:%M:%S')}] {log_name} done in {elapsed:.0f}s", flush=True)
    return elapsed


def distilled_cmd(prompt: str, seed: int, output: Path, image: tuple[str, int, float] | None = None) -> list[str]:
    paths = model_paths()
    cmd = [
        str(LTX_PY), "-m", "ltx_pipelines.distilled",
        "--distilled-checkpoint-path", str(paths["distilled"]),
        "--spatial-upsampler-path", str(paths["spatial_upsampler"]),
        "--gemma-root", str(paths["gemma"]),
        "--offload", "cpu", "--max-batch-size", "4",
        "--width", str(WIDTH), "--height", str(HEIGHT),
        "--num-frames", str(FRAMES), "--frame-rate", str(FPS),
        "--seed", str(seed),
        "--prompt", prompt,
        "--output-path", str(output),
    ]
    if image:
        cmd += ["--image", image[0], str(image[1]), str(image[2])]
    return cmd


def probe_templates(manifest: dict) -> None:
    arms = {"a-current": ARM_A, "b-imperfection": ARM_B, "c-literal-negatives": ARM_C}
    for arm, prompt in arms.items():
        for seed in SEEDS:
            name = f"tpl-{arm}-s{seed}"
            out = OUT / f"{name}.mp4"
            if out.exists():
                print(f"skip {name} (exists)")
                continue
            elapsed = run(distilled_cmd(prompt, seed, out), name)
            manifest.setdefault("templates", []).append(
                {"arm": arm, "seed": seed, "file": out.name, "seconds": round(elapsed)}
            )
            save_manifest(manifest)


def probe_consistency(manifest: dict) -> None:
    still = OUT / "maya-still.png"
    if not still.exists():
        raise SystemExit("maya-still.png missing — run the zimage step first")
    seed = SEEDS[0]
    conditions = [
        ("dna-only", f"{DNA} She {CONSISTENCY_ACTION}", None),
        ("frame0-095-dna", f"{DNA} She {CONSISTENCY_ACTION}", (str(still), 0, 0.95)),
        ("frame0-080-dna", f"{DNA} She {CONSISTENCY_ACTION}", (str(still), 0, 0.8)),
        ("frame0-095-noDna", f"A woman in her late twenties {CONSISTENCY_ACTION}", (str(still), 0, 0.95)),
    ]
    for cond, prompt, image in conditions:
        name = f"cons-{cond}-s{seed}"
        out = OUT / f"{name}.mp4"
        if out.exists():
            print(f"skip {name} (exists)")
            continue
        elapsed = run(distilled_cmd(prompt, seed, out, image), name)
        manifest.setdefault("consistency", []).append(
            {"condition": cond, "seed": seed, "file": out.name, "seconds": round(elapsed)}
        )
        save_manifest(manifest)


def probe_ia2v(manifest: dict) -> None:
    paths = model_paths()
    still = OUT / "maya-still.png"
    vo = OUT / "vo-line.mp4"  # t2a writes containerized audio
    if not vo.exists():
        # ~5 s at 8 fps -> 41 frames (8k+1)
        run(
            [
                str(LTX_PY), "-m", "ltx_pipelines.t2a_one_stage",
                "--checkpoint-path", str(paths["checkpoint"]),
                "--gemma-root", str(paths["gemma"]),
                "--offload", "cpu", "--max-batch-size", "1",
                "--num-inference-steps", "36",
                "--num-frames", "41", "--frame-rate", "8",
                "--seed", "7301",
                "--prompt", f'{VO_VOICE} She says: "{VO_LINE}"',
                "--negative-prompt", VO_NEGATIVE,
                "--output-path", str(vo),
            ],
            "vo-line",
        )
    out = OUT / "ia2v-maya.mp4"
    if out.exists():
        print("skip ia2v (exists)")
        return
    elapsed = run(
        [
            str(LTX_PY), "-m", "ltx_pipelines.a2vid_two_stage",
            "--checkpoint-path", str(paths["checkpoint"]),
            "--distilled-lora", str(paths["distilled_lora"]), "0.8",
            "--spatial-upsampler-path", str(paths["spatial_upsampler"]),
            "--gemma-root", str(paths["gemma"]),
            "--offload", "cpu", "--max-batch-size", "1",
            "--quantization", "fp8-cast",
            "--width", str(WIDTH), "--height", str(HEIGHT),
            "--num-frames", str(FRAMES), "--frame-rate", str(FPS),
            "--seed", "4242",
            "--prompt", AVATAR_PROMPT,
            "--image", str(still), "0", "0.95",
            "--audio-path", str(vo),
            "--output-path", str(out),
        ],
        "ia2v-maya",
    )
    manifest["ia2v"] = {"file": out.name, "vo": vo.name, "seconds": round(elapsed)}
    save_manifest(manifest)


def save_manifest(manifest: dict) -> None:
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe", choices=["templates", "consistency", "ia2v", "all"])
    args = parser.parse_args()

    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    steps = {
        "templates": [probe_templates],
        "consistency": [probe_consistency],
        "ia2v": [probe_ia2v],
        "all": [probe_templates, probe_consistency, probe_ia2v],
    }[args.probe]
    for step in steps:
        step(manifest)
    print("all probes complete")


if __name__ == "__main__":
    main()
