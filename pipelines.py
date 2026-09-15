"""Talking-avatar pipeline: LTX t2a voiceover (whisper-QC'd) -> a2vid_two_stage.

Bake-off verified (docs/bakeoff-results.md): the full local chain runs in ~3 min
per 5 s clip on an RTX 5090 — t2a ~36 s, a2vid ~152 s at 704x1280 fp8-cast with
cpu offload. a2vid takes a true negative prompt, which is what suppresses the
burned-in captions the distilled pipeline cannot avoid.
"""

from __future__ import annotations

import os
import re
import subprocess
from difflib import SequenceMatcher
from pathlib import Path

BASE = Path(__file__).resolve().parent
HF_HUB = Path.home() / ".cache" / "huggingface" / "hub"
LTX_REPO = Path(os.environ.get("LTX_REPO_DIR", str(Path.home() / "repos" / "LTX-2")))
LTX_PY = str(LTX_REPO / ".venv" / "bin" / "python")
QC_PY = Path(os.environ.get("QC_PY", str(BASE / ".qc-venv" / "bin" / "python")))

AVATAR_WIDTH, AVATAR_HEIGHT = 704, 1280
AVATAR_FPS = 24.0
VO_STEPS = 36
QC_THRESHOLD = 0.85
QC_MAX_TRIES = 3

VO_VOICE_DEFAULT = (
    "A single natural voice, casual and friendly like a creator talking to their "
    "phone, conversational pace, close phone-microphone sound with slight room tone. "
    "Speech only, no music, no ambience, no sound effects."
)
VO_NEGATIVE = (
    "music, score, ambience, sound effects, crowd, multiple speakers, singing, robotic "
    "voice, shouting, whispering, distorted audio, clipping, echo, stutter, repeated "
    "words, wrong words, extra words, silence gap"
)
AVATAR_NEGATIVE = (
    "subtitles, captions, on-screen text, generated text, title cards, watermark, "
    "user interface, lower thirds, logos, lettering, studio lighting, plastic skin, "
    "airbrushed face, warped hands, extra fingers, transitions, cuts"
)


def find_model(repo: str, pattern: str) -> str:
    hits = sorted(HF_HUB.glob(f"models--{repo}/snapshots/*/{pattern}"))
    if not hits:
        raise RuntimeError(f"missing model: {repo}/{pattern}")
    return str(hits[-1])


def avatar_model_paths() -> dict[str, str]:
    return {
        "checkpoint": find_model("Lightricks--LTX-2.3", "ltx-2.3-22b-dev.safetensors"),
        "distilled_lora": find_model(
            "Lightricks--LTX-2.3", "ltx-2.3-22b-distilled-lora-384-1.1.safetensors"),
        "spatial_upsampler": find_model(
            "Lightricks--LTX-2.3", "ltx-2.3-spatial-upscaler-x2*.safetensors"),
        "gemma": str(Path(find_model(
            "google--gemma-3-12b-it-qat-q4_0-unquantized", "config.json")).parent),
    }


def subprocess_env() -> dict[str, str]:
    return {"PATH": "/usr/bin:/bin", "HOME": str(Path.home()),
            "PYTORCH_ALLOC_CONF": "expandable_segments:True"}


def snap_frames_8k1(frames: float) -> int:
    return max(9, int(frames // 8) * 8 + 1)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        text=True, env={**subprocess_env(), "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
    )
    return float(out.strip())


def t2a_command(prompt: str, frames: int, seed: int, output: Path) -> list[str]:
    paths = avatar_model_paths()
    return [
        LTX_PY, "-m", "ltx_pipelines.t2a_one_stage",
        "--checkpoint-path", paths["checkpoint"],
        "--gemma-root", paths["gemma"],
        "--offload", "cpu", "--max-batch-size", "1",
        "--num-inference-steps", str(VO_STEPS),
        "--num-frames", str(frames), "--frame-rate", "8",
        "--seed", str(seed),
        "--prompt", prompt,
        "--negative-prompt", VO_NEGATIVE,
        "--output-path", str(output),
    ]


def a2vid_command(prompt: str, image: Path, image_strength: float, audio: Path,
                  num_frames: int, seed: int, output: Path) -> list[str]:
    paths = avatar_model_paths()
    return [
        LTX_PY, "-m", "ltx_pipelines.a2vid_two_stage",
        "--checkpoint-path", paths["checkpoint"],
        "--distilled-lora", paths["distilled_lora"], "0.8",
        "--spatial-upsampler-path", paths["spatial_upsampler"],
        "--gemma-root", paths["gemma"],
        "--offload", "cpu", "--max-batch-size", "1",
        "--quantization", "fp8-cast",
        "--width", str(AVATAR_WIDTH), "--height", str(AVATAR_HEIGHT),
        "--num-frames", str(num_frames), "--frame-rate", str(AVATAR_FPS),
        "--seed", str(seed),
        "--prompt", prompt,
        "--negative-prompt", AVATAR_NEGATIVE,
        "--image", str(image), "0", str(image_strength),
        "--audio-path", str(audio),
        "--output-path", str(output),
    ]


def normalize_words(text: str) -> list[str]:
    text = re.sub(r"[^a-z0-9' ]+", " ", text.lower())
    return [w for w in text.split() if w]


def word_match(expected: str, actual: str) -> float:
    exp, act = normalize_words(expected), normalize_words(actual)
    if not exp:
        return 0.0
    return SequenceMatcher(None, exp, act).ratio()


def transcribe(path: Path) -> str:
    script = (
        "import sys\n"
        "from faster_whisper import WhisperModel\n"
        "model = WhisperModel('small.en', device='cpu', compute_type='int8')\n"
        "segments, _ = model.transcribe(sys.argv[1], beam_size=5)\n"
        "print(' '.join(s.text.strip() for s in segments))\n"
    )
    return subprocess.check_output(
        [str(QC_PY), "-c", script, str(path)], text=True,
        env={**subprocess_env(), "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
    ).strip()


AVATAR_MAX_SECONDS = 20.0  # keeps a2vid within the bake-off-verified VRAM/time envelope


def vo_frames_for_script(script: str) -> int:
    # ~2.6 words/second spoken casually, +1.5 s headroom, at t2a's 8 fps grid.
    words = len(script.split())
    seconds = min(AVATAR_MAX_SECONDS, max(3.0, words / 2.6 + 1.5))
    return snap_frames_8k1(seconds * 8)


def run_avatar_job(job: dict, log_path: Path, timeout: int) -> dict:
    """Generate QC'd VO then an audio-conditioned talking head. Returns extras
    for the job/sidecar; raises on failure (caller marks the job failed)."""
    vo_dir = BASE / "data"
    vo_dir.mkdir(exist_ok=True)
    script = job["script"]
    voice = job.get("voice_style") or VO_VOICE_DEFAULT
    vo_prompt = f"{voice} The speaker says exactly once, then stays silent: {script}"
    frames = vo_frames_for_script(script)
    best: dict = {"score": -1.0}
    with log_path.open("ab") as log:
        for attempt in range(QC_MAX_TRIES):
            seed = job["seed"] + attempt * 17
            candidate = vo_dir / f"vo-{job['id']}-{seed}.mp4"
            subprocess.run(
                t2a_command(vo_prompt, frames, seed, candidate),
                stdout=log, stderr=subprocess.STDOUT, cwd=str(LTX_REPO),
                env=subprocess_env(), timeout=timeout, check=True,
            )
            heard = transcribe(candidate)
            score = word_match(script, heard)
            log.write(f"\n[avatar-qc] seed={seed} score={score:.2f} heard={heard!r}\n".encode())
            if score > best["score"]:
                best = {"score": score, "seed": seed, "heard": heard, "path": candidate}
            if score >= QC_THRESHOLD:
                break
        vo_seconds = ffprobe_duration(best["path"])
        # Video must not outrun the conditioning audio: snap_frames_8k1 floors,
        # so deriving from the raw VO duration keeps video <= audio on the
        # latent grid (a longer video trips a2vid's latent-shape assertion).
        num_frames = snap_frames_8k1(min(vo_seconds, AVATAR_MAX_SECONDS) * AVATAR_FPS)
        subprocess.run(
            a2vid_command(
                job["prompt"], Path(job["image"]), job.get("image_strength", 0.95),
                best["path"], num_frames, job["seed"], Path(job["outfile"]),
            ),
            stdout=log, stderr=subprocess.STDOUT, cwd=str(LTX_REPO),
            env=subprocess_env(), timeout=timeout, check=True,
        )
    for stale in vo_dir.glob(f"vo-{job['id']}-*.mp4"):
        if stale != best["path"]:
            stale.unlink(missing_ok=True)
    return {
        "vo_seed": best["seed"], "qc_score": round(best["score"], 3),
        "qc_heard": best["heard"], "vo_file": str(best["path"]),
        "num_frames": num_frames,
    }
