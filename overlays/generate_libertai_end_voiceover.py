#!/usr/bin/env python3
"""Generate the LibertAI end-card voiceover with LTX-2.3 text-to-audio."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT_AUDIO = BASE / "outputs" / "reboot" / "audio"
HF_HUB = Path.home() / ".cache" / "huggingface" / "hub"
LTX_REPO = Path(os.environ.get("LTX_REPO_DIR", str(Path.home() / "repos" / "LTX-2")))
LTX_PY = LTX_REPO / ".venv" / "bin" / "python"
OUTPUT = OUT_AUDIO / "libertai-end-voiceover-t2a.wav"


def find_model(repo: str, pattern: str) -> Path:
    hits = sorted(HF_HUB.glob(f"models--{repo}/snapshots/*/{pattern}"))
    if not hits:
        raise SystemExit(f"missing model: {repo}/{pattern}")
    return hits[-1]


def model_paths() -> dict[str, Path]:
    gemma_config = find_model("google--gemma-3-12b-it-qat-q4_0-unquantized", "config.json")
    return {
        "checkpoint": find_model("Lightricks--LTX-2.3", "ltx-2.3-22b-dev.safetensors"),
        "gemma": gemma_config.parent,
    }


def voice_prompt() -> str:
    return (
        "A single smooth, warm, engaging brand narrator voice speaks clearly and naturally, "
        "with confident calm energy and a slight cinematic smile. Clean voiceover only, no music, "
        "no ambience, no sound effects. The narrator says exactly once: "
        "Share your AI. Go local. Go decentralized with LibertAI. "
        "Natural pauses between the three short phrases. Polished product film closing line."
    )


def generate(steps: int, seed: int) -> Path:
    OUT_AUDIO.mkdir(parents=True, exist_ok=True)
    paths = model_paths()
    cmd = [
        str(LTX_PY),
        "-m",
        "ltx_pipelines.t2a_one_stage",
        "--checkpoint-path",
        str(paths["checkpoint"]),
        "--gemma-root",
        str(paths["gemma"]),
        "--offload",
        "cpu",
        "--max-batch-size",
        "1",
        "--num-inference-steps",
        str(steps),
        "--num-frames",
        "65",
        "--frame-rate",
        "8",
        "--seed",
        str(seed),
        "--prompt",
        voice_prompt(),
        "--negative-prompt",
        (
            "music, score, ambience, sound effects, crowd, multiple speakers, duet, singing, lyrics, "
            "robotic voice, harsh announcer, shouting, whispering, distorted audio, clipping, reverb, "
            "echo, stutter, repeated words, wrong words, subtitles, labels, silence gap"
        ),
        "--output-path",
        str(OUTPUT),
    ]
    env = dict(os.environ)
    env.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")
    subprocess.run(cmd, cwd=LTX_REPO, env=env, check=True)
    return OUTPUT


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=36)
    parser.add_argument("--seed", type=int, default=9107)
    args = parser.parse_args()
    print(generate(args.steps, args.seed))


if __name__ == "__main__":
    main()
