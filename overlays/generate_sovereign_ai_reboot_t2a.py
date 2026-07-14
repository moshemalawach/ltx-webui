#!/usr/bin/env python3
"""Generate a continuous LTX-2.3 text-to-audio score for the reboot cut."""

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


def score_prompt(mode: str) -> str:
    if mode == "test":
        return (
            "Ten second continuous cinematic sound design test for a wordless film about a centralized AI "
            "failure becoming a local neighborhood mesh. Sparse rain texture, low cold electrical drone, "
            "then a small warm amber pulse. Smooth, restrained, no speech, no lyrics."
        )
    return (
        "Create one continuous fifty six second cinematic soundtrack and sound design cue for a wordless "
        "vertical short film. The story: a city depends on one centralized AI tower during a rain storm; "
        "one uplink cable fails; a clinic medicine fridge loses power; neighbors activate a small local "
        "compute cube; the block forms a sovereign mesh of independent nodes; at dawn the city is still "
        "alive and the central tower is dark. The cue should evolve in four connected movements without "
        "hard cuts: first sixteen seconds cold rain, sub bass, distant transformer hum, fragile blue "
        "electrical tension; next sixteen seconds lower and emptier clinic tension, compressor stop, cable "
        "clicks, then an amber restart pulse; next sixteen seconds rain and hand level node pulses spreading "
        "between people, quiet urgency, no heroic trailer drums; final eight seconds warm restrained analog "
        "chord, softened rain, city waking, hope without triumph. Seamless mix, physical, cinematic, "
        "minimal, no vocals, no dialogue, no narrator, no lyrics, no readable words."
    )


def run(mode: str, steps: int, seed: int) -> Path:
    OUT_AUDIO.mkdir(parents=True, exist_ok=True)
    paths = model_paths()
    if mode == "test":
        output = OUT_AUDIO / "svai-reboot-t2a-score-test.wav"
        num_frames = 81
        frame_rate = 8
    else:
        output = OUT_AUDIO / "svai-reboot-t2a-score.wav"
        num_frames = 453
        frame_rate = 8

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
        str(num_frames),
        "--frame-rate",
        str(frame_rate),
        "--seed",
        str(seed),
        "--prompt",
        score_prompt(mode),
        "--negative-prompt",
        (
            "speech, dialogue, vocals, lyrics, singing, narrator, spoken words, radio host, crowd chatter, "
            "subtitles, labels, abrupt cuts, silence gaps, stock trailer drums, comedy music, distortion, "
            "clipping, stutter, repeated phrases, low quality, glitches"
        ),
        "--output-path",
        str(output),
    ]
    env = dict(os.environ)
    env.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")
    subprocess.run(cmd, cwd=LTX_REPO, env=env, check=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["test", "full"], default="full")
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=8801)
    args = parser.parse_args()
    print(run(args.mode, args.steps, args.seed))


if __name__ == "__main__":
    main()
