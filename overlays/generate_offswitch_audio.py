#!/usr/bin/env python3
"""Generate all audio for "The Off Switch": VO lines, score beds, end sting.

VO uses LTX-2.3 t2a per line (proven approach), with faster-whisper
transcription QC and seed retries. Score is two beds (tension / resolve)
butt-spliced at the blackout in the edit, plus a short logo sting.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "offswitch" / "audio"
HF_HUB = Path.home() / ".cache" / "huggingface" / "hub"
LTX_REPO = Path(os.environ.get("LTX_REPO_DIR", str(Path.home() / "repos" / "LTX-2")))
LTX_PY = LTX_REPO / ".venv" / "bin" / "python"
QC_PY = Path(os.environ.get("QC_PY", "/tmp/claude-1000/-home-jon-repos-ltx-webui/7ee8bcd4-3982-48b4-a1dc-ac2ddaad7885/scratchpad/qcenv/bin/python"))

VOICE = (
    "A single deep male brand narrator voice, low, warm and cinematic like a prestige "
    "film trailer, speaks slowly and clearly with gravity and calm confidence. Clean "
    "studio voiceover only, no music, no ambience, no sound effects."
)

VO_NEGATIVE = (
    "music, score, ambience, sound effects, crowd, multiple speakers, duet, singing, lyrics, "
    "robotic voice, harsh announcer, shouting, whispering, distorted audio, clipping, reverb, "
    "echo, stutter, repeated words, wrong words, extra words, subtitles, labels, silence gap"
)

MUSIC_NEGATIVE = (
    "voice, vocals, singing, lyrics, speech, narration, crowd, clipping, distortion, "
    "harsh noise, abrupt ending, silence gap, low quality audio"
)


@dataclass(frozen=True)
class Line:
    line_id: str
    text: str
    frames: int  # at 8 fps, use 8k+1
    seed: int
    tone: str = "steady"


LINES: list[Line] = [
    Line("v01-leaving", "Right now. Your questions. Your ideas. Your secrets. Are leaving home.", 65, 9201),
    Line("v02-building", "They travel to a building you will never see. Owned by a company you will never meet.", 65, 9202),
    Line("v03-oneswitch", "One company. One building. One switch.", 41, 9203, tone="ominous, measured"),
    Line("v04-flips", "What happens when it flips?", 33, 9204, tone="quiet, almost a whisper of dread"),
    Line("v05-anotherway", "It doesn't have to be this way.", 33, 9205, tone="turning point, gentle hope"),
    Line("v06-livewhere", "Intelligence can live where you live. On your machine. In your neighborhood.", 65, 9206, tone="warm, rising"),
    Line("v07-ownedby", "Owned by no one. Shared by everyone.", 41, 9207, tone="warm, assured"),
    Line("v08-noswitch", "No gatekeepers. No landlords. No off switch, but yours.", 49, 9208, tone="strong, resolute"),
    Line("v09-golocal", "Go local. Go decentralized.", 33, 9209, tone="confident call to action"),
    Line("v10-brand", "LibertAI. Intelligence, set free.", 41, 9210, tone="final brand line, warm smile"),
]


@dataclass(frozen=True)
class Bed:
    bed_id: str
    prompt: str
    frames: int
    seed: int


BEDS: list[Bed] = [
    Bed(
        "bed-tension",
        (
            "A dark minimal electronic film score builds slowly and steadily: a cold pulsing "
            "sub bass heartbeat, tense staccato synth ticks like data pulses, rising string-like "
            "pads gaining pressure and dread, accelerating toward a climax. Instrumental only, "
            "no voice, no drums drop, continuous build, modern prestige ad score."
        ),
        241,  # ~30 s
        9301,
    ),
    Bed(
        "bed-resolve",
        (
            "A warm hopeful modern film score begins from near silence: a single soft piano note, "
            "then gentle glowing synth pads, a slow swelling harmonic progression growing brighter "
            "and more confident, adding soft strings and a subtle steady pulse, resolving into a "
            "wide warm uplifting final chord. Instrumental only, no voice, emotional prestige ad score."
        ),
        273,  # ~34 s
        9302,
    ),
    Bed(
        "sting-logo",
        (
            "A short warm cinematic brand sting: a soft deep whoosh blooming into a single warm "
            "resonant synth chord with a gentle bell-like shimmer on top, holding and fading "
            "slowly to silence. Instrumental only, elegant, premium, quiet ending."
        ),
        65,  # ~8 s
        9303,
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
        "gemma": gemma_config.parent,
    }


def t2a(prompt: str, negative: str, frames: int, seed: int, steps: int, output: Path) -> None:
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
        str(frames),
        "--frame-rate",
        "8",
        "--seed",
        str(seed),
        "--prompt",
        prompt,
        "--negative-prompt",
        negative,
        "--output-path",
        str(output),
    ]
    env = dict(os.environ)
    env.setdefault("PYTORCH_ALLOC_CONF", "expandable_segments:True")
    subprocess.run(cmd, cwd=LTX_REPO, env=env, check=True)


def normalize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"libert\s*a\.?\s*i\.?|liberty\s*a\.?\s*i\.?|libertai|liberte", "libertai", text)
    text = re.sub(r"[^a-z0-9' ]+", " ", text)
    return [w for w in text.split() if w]


def transcribe(path: Path) -> str:
    script = (
        "import sys\n"
        "from faster_whisper import WhisperModel\n"
        "model = WhisperModel('small.en', device='cpu', compute_type='int8')\n"
        "segments, _ = model.transcribe(sys.argv[1], beam_size=5)\n"
        "print(' '.join(s.text.strip() for s in segments))\n"
    )
    return subprocess.check_output([str(QC_PY), "-c", script, str(path)], text=True).strip()


def word_match(expected: str, actual: str) -> float:
    exp, act = normalize(expected), normalize(actual)
    if not exp:
        return 0.0
    from difflib import SequenceMatcher

    return SequenceMatcher(None, exp, act).ratio()


def vo_prompt(line: Line) -> str:
    return (
        f"{VOICE} Tone for this line: {line.tone}. "
        f"The narrator says exactly once, then stays silent: {line.text}"
    )


def gen_vo(line: Line, steps: int, max_tries: int, threshold: float) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    best: dict = {"score": -1.0}
    for attempt in range(max_tries):
        seed = line.seed + attempt * 17
        candidate = OUT / f"{line.line_id}-seed{seed}.wav"
        if not candidate.exists():
            t2a(vo_prompt(line), VO_NEGATIVE, line.frames, seed, steps, candidate)
        text = transcribe(candidate)
        score = word_match(line.text, text)
        print(f"[{line.line_id}] seed={seed} score={score:.2f} heard={text!r}", flush=True)
        if score > best["score"]:
            best = {"line_id": line.line_id, "seed": seed, "score": score, "heard": text, "path": str(candidate)}
        if score >= threshold:
            break
    final = OUT / f"vo-{line.line_id}.wav"
    subprocess.run(["cp", "-f", best["path"], str(final)], check=True)
    best["final"] = str(final)
    return best


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=["vo", "beds", "all"])
    parser.add_argument("--only", help="comma-separated line/bed ids")
    parser.add_argument("--steps", type=int, default=36)
    parser.add_argument("--max-tries", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.88)
    args = parser.parse_args()

    only = set(args.only.split(",")) if args.only else None
    report = []

    if args.what in {"vo", "all"}:
        for line in LINES:
            if only and line.line_id not in only:
                continue
            report.append(gen_vo(line, args.steps, args.max_tries, args.threshold))

    if args.what in {"beds", "all"}:
        for bed in BEDS:
            if only and bed.bed_id not in only:
                continue
            output = OUT / f"{bed.bed_id}.wav"
            if not output.exists():
                t2a(bed.prompt, MUSIC_NEGATIVE, bed.frames, bed.seed, args.steps, output)
            print(f"[{bed.bed_id}] -> {output}", flush=True)
            report.append({"bed_id": bed.bed_id, "path": str(output)})

    report_path = OUT / "report.json"
    existing = []
    if report_path.exists():
        existing = json.loads(report_path.read_text())
    merged = {item.get("line_id") or item.get("bed_id"): item for item in existing}
    for item in report:
        merged[item.get("line_id") or item.get("bed_id")] = item
    report_path.write_text(json.dumps(list(merged.values()), indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
