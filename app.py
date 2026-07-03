"""Local web UI for LTX-2.3 video generation.

Wraps the LTX-2 distilled pipeline (CPU offload recipe) behind a single-page
UI with a serial job queue, so the GPU only ever runs one generation at a
time. Supports optional first-frame image conditioning from uploaded
keyframes. Bind: 127.0.0.1:7860.

Configuration is via environment variables, with auto-discovery of model
files in the Hugging Face cache as fallback:

  LTX_REPO_DIR      path to the cloned Lightricks/LTX-2 repo (with .venv)
  LTX_CHECKPOINT    path to ltx-2.3-*-distilled-*.safetensors
  LTX_UPSAMPLER     path to the spatial upscaler .safetensors
  LTX_GEMMA_ROOT    path to the Gemma 3 text encoder directory
"""

import os
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path
from queue import Queue

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE = Path(__file__).parent
OUTPUTS = BASE / "outputs"
LOGS = BASE / "logs"
KEYFRAMES = BASE / "keyframes"
for d in (OUTPUTS, LOGS, KEYFRAMES):
    d.mkdir(exist_ok=True)

HF_HUB = Path.home() / ".cache" / "huggingface" / "hub"


def _find(repo: str, pattern: str) -> str:
    hits = sorted(HF_HUB.glob(f"models--{repo}/snapshots/*/{pattern}"))
    if not hits:
        raise RuntimeError(
            f"Cannot find {pattern} in {HF_HUB}/models--{repo}. "
            f"Download it first (see README) or set the env var."
        )
    return str(hits[-1])


LTX_REPO = Path(os.environ.get("LTX_REPO_DIR", str(Path.home() / "repos" / "LTX-2")))
LTX_PY = str(LTX_REPO / ".venv" / "bin" / "python")
CHECKPOINT = os.environ.get("LTX_CHECKPOINT") or _find(
    "Lightricks--LTX-2.3", "ltx-2.3-*distilled-[0-9]*.safetensors")
UPSAMPLER = os.environ.get("LTX_UPSAMPLER") or _find(
    "Lightricks--LTX-2.3", "ltx-2.3-spatial-upscaler-x2*.safetensors")
GEMMA = os.environ.get("LTX_GEMMA_ROOT") or str(Path(_find(
    "google--gemma-3-12b-it-qat-q4_0-unquantized", "config.json")).parent)

app = FastAPI(title="LTX video studio")

jobs: dict[str, dict] = {}
job_order: list[str] = []
queue: Queue = Queue()

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


class GenRequest(BaseModel):
    prompt: str = Field(min_length=10, max_length=4000)
    width: int = 1920
    height: int = 1088
    num_frames: int = 193
    frame_rate: float = 25.0
    seed: int | None = None
    keyframe: str | None = None          # filename inside keyframes/
    keyframe_strength: float = Field(default=0.9, ge=0.1, le=1.0)


def slugify(text: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s[:maxlen].rstrip("-") or "video"


def safe_keyframe(name: str) -> Path:
    p = (KEYFRAMES / Path(name).name).resolve()
    if p.parent != KEYFRAMES.resolve() or not p.exists():
        raise HTTPException(400, f"unknown keyframe: {name}")
    return p


def worker() -> None:
    while True:
        job_id = queue.get()
        job = jobs[job_id]
        job["status"] = "running"
        job["started"] = time.time()
        log_path = LOGS / f"{job_id}.log"
        cmd = [
            LTX_PY, "-m", "ltx_pipelines.distilled",
            "--distilled-checkpoint-path", CHECKPOINT,
            "--spatial-upsampler-path", UPSAMPLER,
            "--gemma-root", GEMMA,
            "--offload", "cpu", "--max-batch-size", "4",
            "--width", str(job["width"]), "--height", str(job["height"]),
            "--num-frames", str(job["num_frames"]),
            "--frame-rate", str(job["frame_rate"]),
            "--seed", str(job["seed"]),
            "--prompt", job["prompt"],
            "--output-path", job["outfile"],
        ]
        if job.get("keyframe"):
            cmd += ["--image", str(KEYFRAMES / job["keyframe"]), "0",
                    str(job["keyframe_strength"])]
        try:
            with open(log_path, "wb") as log:
                proc = subprocess.run(
                    cmd, stdout=log, stderr=subprocess.STDOUT,
                    cwd=str(LTX_REPO),
                    env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home()),
                         "PYTORCH_ALLOC_CONF": "expandable_segments:True"},
                    timeout=3600,
                )
            ok = proc.returncode == 0 and Path(job["outfile"]).exists()
            job["status"] = "done" if ok else "failed"
            if not ok:
                job["error"] = tail_log(job_id, 4)
        except Exception as exc:  # noqa: BLE001
            job["status"] = "failed"
            job["error"] = str(exc)
        job["finished"] = time.time()
        queue.task_done()


def tail_log(job_id: str, lines: int = 1) -> str:
    log_path = LOGS / f"{job_id}.log"
    if not log_path.exists():
        return ""
    raw = log_path.read_bytes()[-6000:].decode("utf-8", errors="replace")
    # tqdm uses \r; keep only the freshest fragment of each line
    parts = [seg.split("\r")[-1].strip() for seg in raw.splitlines() if seg.strip()]
    return "\n".join(parts[-lines:])


threading.Thread(target=worker, daemon=True).start()


@app.post("/api/generate")
def generate(req: GenRequest) -> dict:
    if req.width % 64 or req.height % 64:
        raise HTTPException(400, "width and height must be divisible by 64")
    if (req.num_frames - 1) % 8:
        raise HTTPException(400, "num_frames must be 8k+1 (e.g. 97, 193, 249)")
    if req.num_frames > 377:
        raise HTTPException(400, "num_frames capped at 377 (~15s)")
    if req.width * req.height > 1920 * 1088:
        raise HTTPException(400, "resolution capped at 1920x1088 pixels")
    if req.keyframe:
        safe_keyframe(req.keyframe)
    job_id = uuid.uuid4().hex[:10]
    seed = req.seed if req.seed is not None else int(time.time()) % 1_000_000
    name = f"{time.strftime('%Y%m%d-%H%M%S')}-{slugify(req.prompt)}-s{seed}.mp4"
    jobs[job_id] = {
        "id": job_id, "prompt": req.prompt, "width": req.width,
        "height": req.height, "num_frames": req.num_frames,
        "frame_rate": req.frame_rate, "seed": seed,
        "keyframe": Path(req.keyframe).name if req.keyframe else None,
        "keyframe_strength": req.keyframe_strength,
        "status": "queued", "created": time.time(),
        "outfile": str(OUTPUTS / name), "file": name, "error": None,
    }
    job_order.append(job_id)
    queue.put(job_id)
    return {"id": job_id}


@app.get("/api/jobs")
def list_jobs() -> list[dict]:
    out = []
    for jid in reversed(job_order[-30:]):
        j = dict(jobs[jid])
        j.pop("outfile", None)
        if j["status"] == "running":
            j["log"] = tail_log(jid)
            j["elapsed"] = round(time.time() - j["started"])
        out.append(j)
    return out


@app.get("/api/gallery")
def gallery() -> list[dict]:
    vids = sorted(OUTPUTS.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {"file": v.name, "size_mb": round(v.stat().st_size / 1e6, 1),
         "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(v.stat().st_mtime))}
        for v in vids[:100]
    ]


@app.get("/api/keyframes")
def list_keyframes() -> list[str]:
    return sorted(
        p.name for p in KEYFRAMES.iterdir()
        if p.suffix.lower() in IMAGE_EXTS
    )


@app.post("/api/keyframes")
async def upload_keyframe(file: UploadFile) -> dict:
    suffix = Path(file.filename or "kf.png").suffix.lower()
    if suffix not in IMAGE_EXTS:
        raise HTTPException(400, "keyframe must be png/jpg/webp")
    name = Path(file.filename).name
    dest = KEYFRAMES / name
    dest.write_bytes(await file.read())
    return {"name": name}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE / "static" / "index.html")


app.mount("/videos", StaticFiles(directory=OUTPUTS), name="videos")
app.mount("/keyframes", StaticFiles(directory=KEYFRAMES), name="keyframes")
