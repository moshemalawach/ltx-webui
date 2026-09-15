#!/usr/bin/env python3
"""Generate a still image with Z-Image-Turbo (local, ~8 steps).

Runs inside .zimage-venv (torch + diffusers). Used for persona hero stills
that seed LTX first-frame conditioning.

Usage:
  .zimage-venv/bin/python scripts/zimage_still.py \
      --prompt "..." --output keyframes/maya.png [--width 768 --height 1344] [--seed 7]
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--negative-prompt", default="")
    parser.add_argument("--output", required=True)
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=1344)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--guidance", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--model", default="Tongyi-MAI/Z-Image-Turbo")
    args = parser.parse_args()

    import torch
    from diffusers import DiffusionPipeline

    pipe = DiffusionPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16)
    pipe.to("cuda")

    generator = torch.Generator("cuda").manual_seed(args.seed)
    image = pipe(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt or None,
        width=args.width,
        height=args.height,
        num_inference_steps=args.steps,
        guidance_scale=args.guidance,
        generator=generator,
    ).images[0]

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
