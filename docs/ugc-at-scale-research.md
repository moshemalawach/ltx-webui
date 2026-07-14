# Generating UGC-Style Video at Scale with AI — Research Report

**Date:** 2026-07-14
**Method:** Deep-research workflow — 5 search angles, 24 sources fetched, 120 claims extracted, top 25 adversarially verified (3-vote refute panels per claim). 11 claims confirmed, 14 refuted, merged into 7 findings.
**Context:** We already run LTX-2.3 locally (own GPU, web UI, ffmpeg post pipeline). Research covered open-weight/local models and hosted APIs.

---

## Executive summary

Convincing AI UGC is primarily a **prompting and pipeline discipline layered on top of capable models**, not a model-selection problem:

1. **The UGC look is a prompt template.** Explicitly prompt *against* the models' polished defaults: handheld micro-shake, off-center framing, uneven natural light, visible pores, cluttered backgrounds, plus 3–7 inline negatives ("no studio lighting, no warped hands"). 9:16 vertical, ~5–8 s clips.
2. **Character consistency requires a visual anchor.** Text prompts alone cannot lock a face. Generate a hero still first, then use reference-image / first-frame conditioning (native in LTX-2.3). A verbatim-repeated character-description block is a complement, not the mechanism.
3. **Two verified single-pass talking-head pipelines exist.** Hosted: Seedance 2.0 lip-syncs quoted dialogue natively. Local: **LTX-2.3 + Fish Audio S2 Pro in ComfyUI** — portrait + voice-reference clip + script in, lip-synced cloned-voice avatar out, no external API. We already own half of this.
4. **Faces are the weakest point of local models.** Practitioner heuristic: Wan 2.2 for face-heavy shots, clips ≤5 s, slow head movement; LTX-2.3's audio-conditioned avatar mode partially mitigates.
5. **Scale = hook-differentiated variant testing.** 3–5 (up to 5–7) variants per product angle across hook categories (problem / curiosity / result / demo-first / faceless); scale only the winner.
6. **Every comparative benchmark, pricing, and cost-breakeven claim failed verification.** Model rankings and local-vs-hosted economics found online are marketing; run our own bake-off.

---

## 1. Verified findings

### 1.1 The UGC aesthetic is achieved by prompting for phone-camera imperfection
**Confidence: medium · votes 9–0 across three merged claims**

Explicitly prompt for:

- Handheld footage with **tiny wobble / micro-shake**, slightly **off-center or imperfect framing**
- **Natural indoor/window light with uneven exposure** (never studio lighting)
- **Natural skin texture, visible pores**
- **Cluttered everyday backgrounds**
- Friendly casual tone, **product visible early**, short captions
- Inline negative directives — **3–7 of them** (very long negative lists backfire): *no studio lighting, no model-perfect skin, no warped hands, no floating product, no music*

Concrete working spec: **9:16 vertical, ~7 s at 30 fps** with realistic phone-camera sharpness and compression. The template is verified to work on Seedance 2.0 and Kling via fal.ai; fal.ai's own Seedance prompting guide endorses the same approach.

Example verified template:

> "Ultra-realistic vertical 9:16 video that looks like a real person filmed it on their phone... Handheld phone camera with tiny wobble, slightly imperfect framing, subject off-center. Natural skin texture and visible pores... No music, no voiceover, no studio lighting, no model-perfect skin, no warped hands, no floating product."

Caveats: all sources are vendor/practitioner blogs; guides also add natural pauses and non-robotic motion; "7 s @ 30 fps" and "captions under 8 words" are single-source conventions, not standards.

Sources: ugcmaker.org (12 copy-paste UGC templates), mateostarcevicfilipovic.medium.com, magichour.ai realistic-prompting guide; corroborated by fal.ai's Seedance guide, adlibrary.com, imagine.art, retiplex.com.

### 1.2 Character consistency requires a visual anchor, not text alone
**Confidence: high · votes 6–0 across two merged claims**

- Text prompts can *describe* a character but cannot *hold the model to a face*.
- Generate a **reference/hero still before video work begins**; condition every clip on it.
- **First-frame / end-frame conditioning** pins the opening and closing frames and "reduces identity drift, flicker, and composition shifts" (Seedance docs). **Natively supported in LTX-2.3** — directly usable in our existing setup (documented LTX-2.3 first/last-frame ComfyUI workflow on runcomfy.com).
- Every 2026 frontier model ships a visual-reference mechanism: Seedance Character Reference, Kling 3.0 Character ID, Veo ingredients, Sora cameos. Quoted consistency rates apply only *with* references.
- Seed locking is only a mitigation; LoRA training is itself a visual anchor encoded in weights.
- Qualifier: mid-clip identity drift can still occur on complex motion.

Sources: kittl.com, magichour.ai; corroborated by Kling's own guide, getimg.ai, Seedance docs.

### 1.3 Complement: verbatim-repeated character description block
**Confidence: medium · votes 5–1 across two merged claims**

Keep a stable character block (hair, face shape, distinguishing marks, wardrobe) **repeated verbatim in every clip prompt**, varying only scene/lighting/camera. Give wardrobe items one canonical name and never paraphrase ("cropped red denim jacket" must not become "red coat"). Sources call this a "character DNA" block.

Scoping from verifiers: strictly a **complement** to reference-image/first-frame conditioning, not the primary mechanism (both primary sources say text-only is insufficient).

Sources: magichour.ai, kittl.com; corroborated by getimg.ai, Kling, artlist.io, elser.ai, hailuoai.video.

### 1.4 Hosted single-pass talking heads: Seedance 2.0
**Confidence: high · vote 3–0**

Seedance 2.0 (ByteDance; on fal.ai) generates **lip-synced spoken audio and video in a single pass**: put the dialogue in quotation marks in the prompt (convention: `looks at camera, says "..."`). No separate TTS or lip-sync stage. Confirmed by ByteDance's official launch post ("unified multimodal audio-video joint generation architecture" with "synchronized dialogue with accurate lip-sync") and hands-on agency use (Sidekick Studios).

Qualifiers: quoted dialogue is the actual trigger (the "looks at camera, says" phrasing is just convention); lip-sync drifts beyond ~1 minute and weakens with multiple speakers — fine for <30 s ad formats.

Sources: videoai.me, seed.bytedance.com launch post.

### 1.5 Fully local talking-avatar pipeline: LTX-2.3 + Fish Audio S2 Pro
**Confidence: high · vote 3–0**

A single ComfyUI workflow pass produces a lip-synced talking avatar (video + cloned-voice audio) from three inputs — **portrait image, 5–30 s voice reference clip, text script** — with no external TTS API and no manual audio alignment:

- Fish Audio S2 Pro synthesizes speech locally (Saganaki22/ComfyUI-FishAudioS2 nodes; weights on HuggingFace; 16–24 GB VRAM variants). Fish Audio's own blog confirms S2 was open-sourced.
- LTX-2.3's **audio-conditioned image-to-video** generates lip-synced video from that audio. Lip sync is generated *inside* the pass (video and audio latents together, separate VIDEO/AUDIO guidance paths in the multimodal guider), not post-applied.
- The Kijai LTX2.3 HuggingFace discussion (#42) documents exactly this combined single-graph workflow; the official comfy.org `video_ltx2_3_ia2v` workflow confirms audio-conditioned i2v.

Caveats directly relevant to ad production:

- **Fish S2 Pro weights carry commercial-use restrictions — must be resolved before running paid ads.**
- Output is dialog-only (no ambience/SFX) — add in our existing ffmpeg post pipeline.
- Hardware bar ~RTX 4090-class for LTX-2.3 22B FP8.

Sources: nextdiffusion.ai tutorial, huggingface.co/Kijai/LTX2.3_comfy discussion #42, fish.audio blog.

### 1.6 Faces are the weakest area of local models — mitigations
**Confidence: medium · vote 3–0 (evidence rated high, but core recommendation rests on one blog)**

The "warped-face problem" practitioner mitigations:

- **Prefer Wan 2.2 over LTX for face-heavy shots** — LTX photoreal faces reportedly "hold for 2–3 seconds, then drift"; Wan 2.2 retains micro-texture better under motion (corroborated by wavespeed.ai, vast.ai, nemovideo.com comparisons).
- Keep clips at **≤5 seconds**.
- **Avoid prompting fast head movement.**
- Dedicated audio-driven talking-head modes (Wan 2.2 S2V, LTX-2.3 native audio-conditioned video) partially mitigate.

Important: the separate numeric claim ranking Wan 2.2 at "9/10 on faces" was **refuted 0–3** — treat "Wan for faces" as a heuristic worth testing, not benchmark fact.

Source: localaimaster.com (updated 2026-06-19).

### 1.7 Scale workflow: hook-differentiated variant testing before spend
**Confidence: medium · vote 3–0**

Generate **3–5 (some sources 5–7) variants per product angle spanning distinct hook categories** — problem hook, curiosity hook, result hook, demo-first, faceless — review outputs, then scale only the winning category. Corroborated as standard 2026 practice by Alici.AI, Influencers Time, Influee, Pixis. Exact counts/categories vary; common practice, not a precise standard.

Maps directly onto an LLM-scripted batch pipeline: one character anchor + one product angle → N hook scripts → N generations through the local LTX/ffmpeg pipeline.

Source: ugcmaker.org.

---

## 2. Refuted claims — do not rely on these

All 14 killed by the adversarial panel. Essentially **everything quantitative or comparative failed**:

| Refuted claim | Vote |
|---|---|
| I2V models (Kling/Luma/Pika/Runway/Hailuo) are the production tier; T2V (Sora 2, Veo 3) only for storyboards | 0–3 |
| Arcads: 300+ licensed AI actors, $299/mo unlimited, Meta Ads Manager integration | 0–3 |
| Hedra: photorealistic talking head from photo+MP3, $29/mo / 60 min cap | 0–3 |
| LTX-2.3 first open model with single-pass 4K+audio, 3840×2160@50fps/20 s, 32 GB VRAM official | 0–3 |
| Only LTX-2.3 has native audio among open models; others cap at ~5 s with quality cliff | 0–3 |
| Wan 2.2 scores 9/10 on faces vs Hunyuan 8/10 vs LTX 7/10 | 0–3 |
| LTX 13B is 2–3× faster than Wan/Hunyuan; 5 s 720p in 1–2 min on 4090 | 0–3 |
| Local beats hosted above ~500 videos/month; hosted LTX at $0.05–0.20/clip | 0–3 |
| UGC prompts perform better when describing creator behavior vs product | 1–2 |
| "Plastic look" has six specific failure modes and prompting matters more than model choice | 0–3 |
| Opening Seedance prompts with "UGC creator, iPhone handheld, harsh midday sun" as magic lead | 0–3 |
| Frame chaining (last frame of clip N → reference for clip N+1) significantly reduces drift | 1–2 |
| Kling 3.0 leads motion / Veo 3.1 best native audio / Runway Gen-4.5 best consistency | 1–2 |
| Effective prompts average 150–200 words in a "10-pillar framework" | 0–3 |

Consequence: research sub-questions on **cost/throughput economics** and **platform compliance** are unanswered by verified evidence. Do not cite any specific pricing, VRAM figure, or model ranking from the sources above.

---

## 3. Unverified but useful leads

Extracted from fetched sources but **not put through the verification panel** (or outside the top-25 cut). Treat as leads to check, clearly weaker than Section 1.

### 3.1 Local LTX-2.3 pipeline details (practitioner tutorials)

From nextdiffusion.ai, ltxworkflow.com, mickmumpitz.ai — all single-source:

- **Distilled 22B v1.1 runs 8 sampling steps at CFG=1 (euler)** vs 20–30 steps at CFG=3.5 for the dev model — large throughput win for batch generation. FP8-scaled checkpoint (`ltx-2.3-22b-distilled-1.1_transformer_only_fp8_scaled.safetensors`) reportedly fits 16 GB VRAM; BF16 needs 32 GB. GGUF quants (QuantStack Q4/Q5/Q8 + GGUF Gemma 3 12B text encoder) for lower VRAM.
- **Dimension rules for scripted pipelines:** width/height divisible by 32, frame count divisible by 8 plus 1; invalid values are *silently rounded*, which matters for batch scripts expecting exact sizes. Recommended vertical default: **736×1280 @ 24 fps**; 1088×1920 for 5090-class.
- **Talking-avatar mode:** TTS script length sets final video duration (frame count acts as a minimum). Animation prompt should describe only visuals/motion/lighting/camera — not speech content. Lock the camera; prompted camera moves degrade lip-sync. Source portrait: sharp, front-facing or mild three-quarter, mouth visible. Keep avatar clips **under ~5 s** for sync quality; feed clean mono speech (one guide says 16 kHz). A MelBand Roformer node can isolate the vocal stem from music beds.
- **Fish Audio TTS** supports inline expression tags: `[excited]`, `[pause]`, `[chuckling]`; voice cloning works best with 5–15 s of clean single-speaker reference audio.
- **i2v conditioning strength:** start-frame strength 1.0 = tight adherence to the input image; 0.7–0.9 allows more creative motion.
- Writing "talking"/"speaking" in the positive prompt biases toward speech motion independent of audio conditioning.
- **Mickmumpitz lip-sync-on-existing-video workflow:** re-animates only the mouth to match supplied audio (dubbing/localization); uses DWPose mouth masking + a custom AudioTimestepOverride node (without it, no lip movement); ~30 GB LTX FP8 checkpoint + ~13 GB Gemma 3 12B FP8 text encoder.

### 3.2 Automation blueprints (n8n templates, agency guides)

- **n8n + HeyGen factory (self-reported production use):** Google Sheets as content source → GPT-4.1-mini writes 75–90-word scripts (~30 s speech) with persona prompt → HeyGen v2 talking-photo API (720×1280) → daily auto-post via upload-post.com. ~5–15 min per video end-to-end; variant diversity via day-of-year rotation over 14 avatars. Author claims a live Instagram account runs fully hands-off.
- **n8n + Gemini + Veo 3:** Gemini 2.5 Pro role-prompted as "Creative Director" turns a product image into a cinematic 8 s video prompt → Veo 3 preview API → Postiz posts to Instagram; a second Gemini agent writes captions in parallel. Pattern: **LLM writes the video prompt from a product image** rather than hand-writing prompts.
- **admove.ai script structure:** Hook (0–3 s), Problem (3–8 s), Solution/demo (8–20 s), CTA (3–5 s); batch-test hooks in isolation while holding the script body constant. Their "90/10 rule": ~90% B-roll/product footage, ~10% talking-head avatar, to keep synthetic faces from dominating.
- **magichour.ai API roundup:** effective scale production mixes multiple engines (HeyGen for avatar+voice-clone API; Synthesia = stable API but "corporate" look; Runway for cinematic hooks, not testimonials; Pika fast for short variants).

### 3.3 Economics (all unverified; the one breakeven claim tested was refuted)

- spheron.network (March 2026): LTX-2.3 720p fits 12–24 GB VRAM fp8; native 4K claimed to need 48 GB+. Rented RTX 5090 ≈ $0.06–0.10 per 5 s clip at 5–8 min/generation. Wan 2.1 720p claimed to need 65–80 GB (H100, ~$0.40–0.48/clip); Hunyuan needs H200-class (~$0.74–1.11/clip on-demand).
- fluxnote.io (May 2026): Kling ~$0.07/s, Sora ~$0.10/s, Veo $0.10–0.40/s; Sora gated behind ChatGPT Pro ($200/mo); hidden per-video costs (TTS, captions, music) ≈ $1.27/video modular vs $0.27 all-in-one; predicts ~60% price drop within a year.
- pose.ai (vendor, self-interested): AI UGC ≈ $0.50/video vs $100–500 for real creators; 50 AI videos < 2 h vs 4–6 weeks; cited head-to-head: real UGC converted 18% better per asset, but the best AI hook variant hit 4.2% CTR vs 1.1% average — i.e. **AI wins on breadth of hook testing, not per-asset quality**.

### 3.4 Compliance leads (none verified — check primary sources before running paid ads)

- **Platforms:** all four majors (Meta, Google, TikTok, YouTube) reportedly require disclosure of AI-generated ad creative as of 2026. TikTok enforces strictest (AIGC label on avatars/digital personas that could pass as real; strikes; claimed 51,618 synthetic videos removed H2 2025, +340% YoY). Meta auto-labels ads made with its own genAI tools; requires disclosure on political/social ads with realistic AI people.
- **AI likenesses of real identifiable people** are effectively banned across all four platforms without documented consent; even consented content must be labeled — directly constrains cloned-face/voice pipelines.
- **EU AI Act Article 50** transparency obligations effective 2026-08-02; fines up to €15 M or 3% of global turnover; advertisers share "deployer" liability.
- **New York Synthetic Performer Law (S.8420-A/A.8887-B)**, signed 2025-12-11, effective 2026-06-09: conspicuous disclosure when ads shown to NY consumers use AI-generated humans, any channel, $1,000 first / $5,000 subsequent violations, brand+agency liable. Audio-only/TTS exempt; AI avatar video triggers it. California AI Transparency Act (2026-01-01): visible + invisible metadata disclosures.
- **FTC:** Consumer Reviews Rule penalties up to ~$51,744 per violation for fake AI reviews; Impersonation Rule covers voice cloning/deepfakes — relevant to testimonial-style AI UGC.
- **Actionable for our pipeline:** embedding **C2PA provenance metadata at render time** (ffmpeg stage) is reportedly read (or planned) by all four platforms — a cross-platform compliance mechanism we can automate.

---

## 4. Caveats on evidence quality

- **Source quality is the biggest weakness.** Every surviving claim traces to vendor marketing blogs or practitioner Medium/SEO posts. Only two findings have primary vendor documentation: Seedance 2.0 (ByteDance launch post) and LTX+Fish (Kijai HF discussion + official comfy.org workflow). No peer-reviewed or benchmark-grade evidence exists for any finding.
- **All comparative and quantitative claims failed verification** (14 refuted): model rankings, face scores, speed multipliers, LTX-2.3 spec claims, tool pricing, breakeven volumes.
- **Time-sensitivity is severe.** The video-model landscape turns over quarterly (Seedance 2.0 launched Feb 2026; LTX-2.3 is weeks-to-months old). Model-specific findings have a short shelf life; **prompting/anchoring techniques are the durable part**.
- **Fish Audio S2 Pro commercial-use restrictions flagged but not resolved** — blocking check before paid-ad use of the local avatar pipeline.

## 5. Open questions

1. **Real local-vs-hosted economics** at our volumes (LTX-2.3/Wan 2.2 on owned GPU vs fal.ai Seedance/Kling, Veo, Sora) — the ~500 videos/month breakeven was refuted; no verified figure exists.
2. **Platform compliance specifics** for AI-generated UGC ads — Meta/TikTok/YouTube disclosure rules, synthetic-actor labeling, likeness/voice-clone licensing (incl. Fish S2 Pro license) — no surviving claims; needs primary-source checks.
3. **Which hosted model actually leads** for photorealistic talking heads + native audio — all ranking claims refuted; a hands-on bake-off on our own scripts is the only reliable path.
4. **Does LTX-2.3's audio-conditioned avatar mode close the face-quality gap** with Wan 2.2 beyond 5 s, or is a hybrid local architecture (Wan for faces, LTX for everything else) better?

---

## 6. Recommended implementation plan (this repo)

1. **UGC prompt preset** in the web UI: the imperfection template (§1.1) with the 3–7 negatives baked in; 736×1280 @ 24 fps vertical default; clip length capped ~5–8 s.
2. **Character-anchor loop:** hero-still generation step → first-frame conditioning on every clip (native LTX-2.3), plus a stored verbatim "character DNA" block injected into every prompt (§1.2–1.3).
3. **Local avatar pipeline:** stand up LTX-2.3 + Fish Audio S2 Pro ComfyUI workflow (§1.5, §3.1). Respect dimension/frame rules in batch scripts; script-length-driven duration; camera locked in avatar prompts. **Resolve the Fish S2 Pro commercial license first.**
4. **Hook-variant batcher:** LLM generates N scripts per product angle across the five hook categories (§1.7, §3.2 script structure); batch through LTX + ffmpeg; the distilled 8-step model is the throughput path.
5. **Face bake-off:** pull Wan 2.2 alongside LTX-2.3; identical scripts, ≤5 s, slow head motion; judge by eye (§1.6, open question 4).
6. **Compliance stage in ffmpeg post:** C2PA metadata injection + optional on-screen AI-disclosure label (§3.4), pending primary-source verification of platform rules.

## 7. Source list

**Verified findings drew on:** ugcmaker.org · mateostarcevicfilipovic.medium.com · magichour.ai (3 articles) · kittl.com · videoai.me · seed.bytedance.com (primary) · nextdiffusion.ai · huggingface.co/Kijai/LTX2.3_comfy #42 (primary) · fish.audio (primary) · localaimaster.com

**Additional fetched sources (unverified leads):** ltxworkflow.com · mickmumpitz.ai · n8n.io (2 templates) · admove.ai · adlibrary.com · aimagicx.com · virvid.ai · auditsocials.com · webtopia.co · fluxnote.io · spheron.network · pose.ai · tech-insider.org (rated unreliable)

**Raw workflow output:** run `wf_53c1ffad-155`; full result at `tasks/w42sb0khi.output`, per-agent journal at `subagents/workflows/wf_53c1ffad-155/journal.jsonl` (session dir).
