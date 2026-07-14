# The Off Switch — LibertAI brand film treatment

## Why the previous films failed (diagnosis)

1. **Genre mismatch.** A silent multi-beat human drama (recurring protagonist,
   staged causal action, "consent tokens") is the single hardest genre for a
   video model: face continuity drifts, action mushes, and the argument never
   reads without narration.
2. **Murk.** Night + rain + cluttered interiors in every shot produced muddy,
   low-contrast footage that screams "AI-generated". Nothing was iconic.
3. **The message was carried by plot instead of voice.** Big ads are carried
   by voiceover and typography; pictures carry emotion and scale.
4. **Sound was an afterthought** and the VO gambled on nondeterministic T2A.

## The rethink (Super Bowl grammar)

- **The voice carries the argument.** A single narrator delivers the whole
  thesis. Pictures never have to explain anything.
- **Every shot is a standalone icon.** Zero continuity dependencies. No
  recurring characters. Humans appear once each, as silhouettes, hands, or
  crowds. This deletes the model's biggest failure mode.
- **Bold graphic light.** Every frame must read in half a second from across
  a room: one subject, one light idea, deep blacks.
- **Two color worlds.** Act 1: cold electric blue against black (the tower).
  Act 2: warm amber against dawn (the mesh). The film IS the transition.
- **Slow deliberate camera only.** Push, drift, rise. No staging, no coverage.
- **Widescreen scope.** 2.31:1 (1920x832 native), letterboxed into 1920x1080.
  Cinema, not phone.

## Format

- 16:9 delivery, 1920x1080, 24 fps, ~60 s including end card.
- Shots rendered at 1920x832, 121 frames @ 24 fps (~5 s each), trimmed in edit.
- Pipeline: `ltx_pipelines.ti2vid_two_stages_hq`, frame-0 keyframe
  conditioning at 0.95 strength, fp8-cast, cpu offload.
- Native LTX audio kept as a low SFX texture layer; score + VO on top.

## Voiceover script (the spine — the film cuts to this)

| # | Line | Plays over |
|---|------|-----------|
| V1 | "Right now — your questions… your ideas… your secrets… are leaving home." | S01–S03 |
| V2 | "They travel to a building you will never see. Owned by a company you will never meet." | S04–S05 |
| V3 | "One company. One building. One switch." | S06 |
| — | *(power-down SFX, score cuts)* | S07–S08 |
| V4 | "What happens when it flips?" *(quiet)* | S09 |
| — | *(1.5 s near-black silence)* | — |
| V5 | "It doesn't have to be this way." | S10 |
| V6 | "Intelligence can live where you live. On your machine. In your neighborhood." | S11–S12 |
| V7 | "Owned by no one. Shared by everyone." | S13 |
| V8 | "No gatekeepers. No landlords. No off switch — but yours." | S14 |
| V9 | "Go local. Go decentralized." | E01 |
| V10 | "LibertAI. Intelligence, set free." | E01 |

TTS spelling for the brand: "Libert A.I." — verify by transcription.

## Shot list

Act 1 — THE TOWER (cold blue / black, rising pulse)

- **S01 FIBER** — Extreme macro of glass fiber-optic strands in darkness,
  pulses of cold blue light streaming in one direction. Slow lateral drift,
  shallow focus.
- **S02 WINDOW** — Night exterior of one warm apartment window; a thin blue
  filament of light rises from a laptop, through the glass, up into the dark
  sky. Slow push-in.
- **S03 THREADS** — High aerial over a night city; thousands of thin blue
  light threads rise from rooftops and all bend toward one point on the
  horizon. Slow forward drift.
- **S04 MONOLITH** — A colossal black data-center monolith above a fog layer,
  blue threads pouring into its flanks. Slow rising reveal. Scale is the shot.
- **S05 HALL** — Infinite one-point-perspective server corridor, cold blue,
  perfectly clean. Slow dolly forward.
- **S06 SWITCH** — Macro of an industrial breaker lever glowing red; a gloved
  hand grips it. Slow push. (Single hand, single shot — allowed.)

The turn — BLACKOUT

- **S07 SHUTDOWN** — The monolith's blue data lanes drain to black; one red
  pulse, then nothing. Near-static camera.
- **S08 CITY DIES** — High wide of the night city; districts go dark in
  sweeping waves. Static.
- **S09 DARK ROOM** — A dark living room, a face lit only by a phone screen;
  the screen dies; silhouette in darkness. 2 s beat.

Act 2 — THE MESH (amber / dawn, score resolves)

- **S10 EMBER** — From black: on a wooden kitchen table, a palm-sized compute
  node wakes with a warm amber core. Slow push. The turn of the film.
- **S11 CIRCUIT** — Extreme macro of amber circuitry igniting, traces lighting
  up like streets seen from the air. Macro drift.
- **S12 BLOCK** — Night apartment façade; windows ignite warm amber one by
  one; soft light threads arc low between windows, human-scale. Slow rise.
- **S13 MESH AERIAL** — Aerial at first light; a web of warm light linking
  rooftops and neighborhoods, spreading outward. Forward drift.
- **S14 DAWN WIDE** — Sunrise wide of the city glowing from thousands of warm
  points; far on the horizon the monolith stands dark and dead, small. Very
  slow pull.

End card

- **E01 LOGO** — Pure black; the purple LibertAI mark blooms in with a soft
  glow, tagline type "Go local. Go decentralized." — built in post from the
  SVG assets, with a warm sonic sting. ~8 s.

## Sound plan

- **VO**: local Kokoro TTS, single deep narrator, generated per line and cut
  to picture; transcription-verified.
- **Score**: one continuous LTX T2A bed (~56 s proven): minimal pulsing dark
  electronic build → hard cut to silence at the blackout → warm hopeful
  resolve. If one pass won't obey the arc, generate tension and resolve beds
  separately and butt-splice at the blackout.
- **SFX**: native LTX shot audio mixed low (hum, rain, room tone); a
  power-down whoosh at S07/S08; sting under E01.
- **Mix**: score sidechain-ducked under VO, loudnorm I=-16, TP=-1.5.

## QC gates (unchanged from research doc, enforced per shot)

ffprobe + decode pass, contact sheet, reject on: frozen camera, garbled
geometry, readable text/logos, mushy subject, wrong color world, broken
audio. Retake with seed offset until the shot is an icon.
