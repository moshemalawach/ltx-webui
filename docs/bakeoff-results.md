# Phase 0 Bake-off Results (2026-07-14)

Cheap probes: 121 frames @ 24 fps, 704×1280, `ltx_pipelines.distilled`, seeds 4242/9107.
Clips + contact sheets in `scripts/bakeoff/out/` (git-ignored). Runner: `scripts/bakeoff/run_probes.py`.

## Gate verdicts

| Probe | Verdict |
|---|---|
| 1. Z-Image-Turbo hero stills | **PASS** — 8 steps ≈ 6 s/still on the 5090; output matched the character DNA exactly (freckles, beauty mark, cardigan, cluttered kitchen). In-app persona still generation is GO. |
| 2. UGC template A/B/C | **Arm B (imperfection template) wins decisively.** Arm A (old template) renders a polished salon-look creator; B renders messy hair, real skin texture, cluttered counters, harsh window light — reads as genuine UGC on both seeds. Arm C (literal "no X" negatives) ≈ B, no visible benefit, and one violation (lettering on the shirt); at CFG=1 the negations are inert at best. **Adopt B's positive-phrased language; skip literal negatives on the distilled pipeline.** |
| 3. Consistency ladder | **First-frame @ 0.95 + verbatim DNA wins.** Identity locked to the hero still across the whole clip with free natural motion. DNA-only produced a *different* woman (right archetype, wrong face) — text cannot lock identity, exactly as the research said. 0.8 strength also holds; image-only (no DNA) drifts slightly by the last frame. **Persona defaults: first-frame 0.95 + DNA in every prompt.** |
| 4. ia2v talking avatar | See below (retried after an OOM caused by a stray test-spawned render; t2a VO itself passed: 36 s for a 5 s line). |

## Unexpected findings (important)

1. **Burned-in captions**: every clip whose prompt contains quoted dialogue rendered garbled subtitles, despite the anti-text guard paragraph — on all three template arms. The distilled pipeline has no `--negative-prompt`, so the guard text alone cannot suppress them.
2. **First-frame conditioning suppresses captions**: the consistency clips conditioned on a clean photographic still rendered **no** captions, while the unconditioned DNA-only clip burned in captions *even with no speech in the prompt*. → Keyframe conditioning is not just an identity lock, it is the practical anti-subtitle lever on the distilled pipeline.
3. **Product labels garble** on all arms (known behavior) — the product-reference keyframe remains the mitigation.

## Implications applied to the app

- `UGC_STYLE_BLOCK` (app.py) and `UGC_STYLE` (index.html) use Arm B's language: micro-shake, off-center framing, uneven exposure, visible pores, clutter, phone compression. No literal negations.
- Persona flow defaults: hero still as first-frame @ 0.95 + DNA block verbatim in every variant.
- Recommended practice: always render dialogue clips with a persona or product first-frame reference to suppress captions. For text-free masters, the HQ two-stage pipeline (`ti2vid_two_stages_hq`, supports true `--negative-prompt`) is the follow-up experiment (backlog).

## t2a voice note
LTX `t2a_one_stage` produced the 5 s UGC female VO line in 36 s (dev checkpoint, 36 steps). Whisper-QC scoring not yet wired into the probe (Phase 4 ports the proven overlays loop).

## ia2v (a2vid_two_stage) — **PASS**
- First attempt died to the kernel OOM killer: a leftover test-enqueued `distilled` render loaded a second 22B model alongside a2vid. After killing the orphan, ~48 GB RAM was available.
- Retry: **152 s** for a 5 s 704×1280 talking head (dev ckpt + distilled-lora 0.8, fp8-cast, cpu offload). Maya's identity matches the hero still exactly; mouth articulates the line; synced AAC audio in the container. Full local avatar chain = t2a (36 s) + a2vid (152 s) ≈ **3 min per 5 s talking-head clip**.
- Caveat: a faint garbled caption still creeps in on some frames even with first-frame conditioning. Unlike `distilled`, this pipeline takes `--negative-prompt` — Phase 4 must pass "subtitles, captions, on-screen text, watermark" there.

**Gate verdict: Phase 4 avatar pipeline is GO (t2a → a2vid, no ComfyUI, no external TTS).**

## In-app E2E results (after implementation, same day)

- **5-hook campaign** (Sola × Maya persona, GLM-refined, 1088×1920 8 s): 5/5 cells rendered
  (two needed re-render after a RAM contention incident caused by a since-fixed
  import side effect). Identity locked across all hooks via first-frame 0.95 + DNA.
- **Avatar take** (8 s, 21-word script): whisper QC scored **1.00 on the first VO
  attempt**; a2vid lip-synced render completed; total job ≈ 5 min including QC.
- **Residual issue:** faint garbled captions can still appear on dialogue clips.
  The distilled pipeline takes no negative prompt, and a2vid's distilled-lora runs
  near-CFG-free so its negative prompt has limited pull. First-frame conditioning
  strongly reduces it. Future options: raise a2v CFG params, HQ two-stage masters,
  or a crop/inpaint post-step.
