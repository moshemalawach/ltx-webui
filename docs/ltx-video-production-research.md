# LTX Video Production Research

This is the new baseline for making good local LTX videos in this repo. The
previous sovereign-AI attempts failed for structural reasons: we generated
loose images and clips first, then tried to recover story, continuity, and
sound in post. The better workflow is the reverse: write the film, lock the
visual references, render short controlled shots, reject bad shots, retake
only the failed pieces, then assemble.

## Sources Checked

- Lightricks LTX-2 README: https://github.com/Lightricks/LTX-2
- LTX pipeline README: https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/README.md
- LTX-2.3 model card: https://huggingface.co/Lightricks/LTX-2.3
- Aurel Manea long-video workflow: https://aurelm.com/2026/03/09/ltx-2-3-long-video-for-low-vram-ram-workflow/
- Linked Aurel ComfyUI workflow JSON: https://aurelm.com/upload/ComfyWorkflows/LTX23_1080p_I2V_with_upscale_introactors_previous_movie.json

## Findings

1. Use the right pipeline for final shots.

The local web UI currently wraps `ltx_pipelines.distilled`, which is the fast
path. It is useful for scratch tests, not the best default for final footage.
The upstream docs call the two-stage pipelines the production-quality path:
`ti2vid_two_stages` or `ti2vid_two_stages_hq`, with the full dev checkpoint,
the distilled LoRA, and the spatial upscaler.

2. Do not ask one prompt to be a movie.

The official prompt guidance is per-shot: chronological action, concrete
movement, appearance, camera, environment, light, changes, and sound. It should
read like a cinematographer describing one shot, not like a synopsis.

3. Long videos need chained short segments.

The Aurel workflow cuts a long scene into roughly 10 second passes. Each pass
uses character/environment reference images, plus previous-segment context:
a low-FPS version for visual continuity and the final second at normal speed
for motion continuity. The overlap is then blended in edit.

The local CLI does not expose that exact ComfyUI previous-video graph through
`ti2vid_two_stages_hq`; it exposes image conditioning. So the practical local
version is:

- final renders through `ti2vid_two_stages_hq`;
- 7-10 second shots;
- 2-3 locked reference images per character/setting;
- previous-shot tail frame as weak frame-0 conditioning;
- explicit one-second overlap in the edit;
- retake bad windows with `retake` when possible.

If we need the full Aurel workflow exactly, use ComfyUI-LTXVideo or add a
separate IC-LoRA/video-conditioning path. The local cache currently has the
main LTX-2.3 dev checkpoint, distilled checkpoint, distilled LoRA, spatial
upscaler, and Gemma; it does not show the IC-LoRA control weights.

4. Dialogue should be source-first.

LTX T2A is useful for generated sound, speech texture, ambience, and music, but
it is not a deterministic exact-dialogue engine. For exact spoken lines, create
or record the dialogue first, audit/transcribe it, then use `a2vid_two_stage`
because that pipeline preserves the original input audio and generates matching
video. If exact dialogue is not available, make the film mostly visual and add
score/sound design after.

5. QC must be part of the workflow.

Every rendered shot gets:

- `ffprobe` duration/resolution/audio check;
- decode pass with `ffmpeg -v error`;
- contact sheet at 1 fps;
- reject criteria: bad face continuity, unreadable action, camera frozen when
  motion is required, unwanted text/logos, incoherent hands, broken audio,
  story beat not visible without explanation.

## Practical Recipe

1. Treatment

Write a 5-8 beat story where every beat can be shown physically. Avoid abstract
concepts unless they become objects, gestures, lights, doors, cables, hands,
faces, weather, and spaces.

2. Reference Bible

Generate or curate vertical stills before rendering:

- protagonist full body, close face, hands with key prop;
- antagonist/institution visual symbol;
- key prop closeup;
- each major location;
- final color/light target.

References matter more than clever prompts.

3. Shot Cards

For each shot, define:

- story purpose;
- duration;
- exact visible action;
- camera move;
- start and end frame intention;
- sound intention;
- LTX prompt under about 200 words;
- negative prompt;
- references and frame indices.

4. Render

Use `overlays/sovereign_ai_reboot_lab.py` for reproducible commands. Start
with low-resolution probes, then render accepted shots at production size.

Recommended starting settings:

- final pipeline: `ltx_pipelines.ti2vid_two_stages_hq`;
- production frame size: 832x1472 vertical, or 1088x1920 only if memory allows;
- duration: 129 frames at 16 fps, about 8 seconds;
- overlap: 1 second between shots;
- offload: CPU;
- quantization: `fp8-cast` unless a specific run fails;
- generate two seed candidates per shot before editing.

5. Edit

Assemble accepted shots only. Use one-second overlap/crossfade when a shot
continues the previous action. Do not cover broken story with text overlays.
If a beat does not read silently, rewrite and retake the shot.

6. Sound

Make sound after picture lock unless using `a2vid_two_stage`. For exact
dialogue, build the dialogue track first and use it as conditioning. For a
wordless film, create a continuous score/sound bed with T2A or conventional
audio tools, then mix under the cut.

