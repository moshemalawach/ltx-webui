#!/usr/bin/env python3
"""Generate dialogue audio with LTX-2.3 text-to-audio."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
LTX_REPO = Path.home() / "repos" / "LTX-2"
LTX_PY = LTX_REPO / ".venv" / "bin" / "python"
OUT_AUDIO = BASE / "outputs" / "audio"

CHECKPOINT = (
    Path.home()
    / ".cache/huggingface/hub/models--Lightricks--LTX-2.3/"
    / "snapshots/76730e634e70a28f4e8d51f5e29c08e40e2d8e74/ltx-2.3-22b-dev.safetensors"
)
GEMMA = (
    Path.home()
    / ".cache/huggingface/hub/models--google--gemma-3-12b-it-qat-q4_0-unquantized/"
    / "snapshots/68f7ee4fbd59087436ada77ed2d62f373fdd4482"
)

SCRIPT = BASE / "docs" / "sovereign-ai-dialogue-script.md"


def dialogue_from_markdown() -> str:
    text = SCRIPT.read_text(encoding="utf-8")
    block = text.split("## Dialogue Track", 1)[1]
    lines = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("Clean radio-play"):
            continue
        if re.match(r"^[A-Z][A-Z]+:", line):
            speaker, words = line.split(":", 1)
            lines.append(f"{speaker.title()} says, \"{words.strip()}\"")
    return " ".join(lines)


def prompt(mode: str) -> str:
    dialogue = dialogue_from_markdown()
    if mode == "test":
        dialogue = " ".join(dialogue.split()[:85])
    return (
        "Clean spoken radio drama dialogue only, no music, no ambience, no sound effects. "
        "Four distinct voices: Mara is a calm middle-aged woman, Eli is a worried teenage boy, "
        "Tomas is a practical adult man, CivicCore is a controlled synthetic institutional voice. "
        "Perform the dialogue naturally with short pauses. Do not read punctuation, speaker labels, "
        "stage directions, or the words quote or says. Use only the spoken lines. "
        f"{dialogue}"
    )


def run(mode: str) -> Path:
    OUT_AUDIO.mkdir(parents=True, exist_ok=True)
    if mode == "test":
        output = OUT_AUDIO / "svai-t2a-dialogue-test.wav"
        num_frames = "81"
        frame_rate = "8"
        seed = "4201"
    else:
        output = OUT_AUDIO / "svai-t2a-dialogue-full.wav"
        num_frames = "601"
        frame_rate = "8"
        seed = "4202"

    cmd = [
        str(LTX_PY),
        "-m",
        "ltx_pipelines.t2a_one_stage",
        "--checkpoint-path",
        str(CHECKPOINT),
        "--gemma-root",
        str(GEMMA),
        "--offload",
        "cpu",
        "--max-batch-size",
        "1",
        "--num-inference-steps",
        "30",
        "--num-frames",
        num_frames,
        "--frame-rate",
        frame_rate,
        "--seed",
        seed,
        "--prompt",
        prompt(mode),
        "--negative-prompt",
        (
            "music, score, ambience, rain, room tone, sound effects, noise, echo, reverb, "
            "distortion, robotic artifacts, labels, narrator, subtitles, silence, wrong words, "
            "repeated words, stuttering, laughter"
        ),
        "--output-path",
        str(output),
    ]
    subprocess.run(cmd, cwd=LTX_REPO, check=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["test", "full"], default="test")
    args = parser.parse_args()
    output = run(args.mode)
    print(output)


if __name__ == "__main__":
    main()
