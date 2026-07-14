#!/usr/bin/env python3
"""Assemble "The Off Switch" — LibertAI brand film (1920x1080, 24 fps).

Data-driven edit: reads actual VO line durations, computes the timeline,
then builds one ffmpeg graph: letterboxed graded picture with grain,
native shot audio as low SFX bed, VO placed at absolute times, tension /
resolve score beds with a hard cut at the blackout, sidechain-ducked
under the VO, end-card sting, loudnorm master.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "offswitch"
AUDIO = OUT / "audio"
W, H = 1920, 1080
FPS = 24
SHOT_W, SHOT_H = 1920, 832

FILM = OUT / "FILM-the-off-switch-libertai-1920x1080.mp4"


def clip(shot_id: str, seed: int) -> Path:
    return OUT / f"{shot_id}-seed{seed}-{SHOT_W}x{SHOT_H}-121f.mp4"


def vo(line_id: str) -> Path:
    """Silence-trimmed VO line (t2a pads fixed frame counts with silence)."""
    src = AUDIO / f"vo-{line_id}.wav"
    trimmed_dir = AUDIO / "trimmed"
    trimmed_dir.mkdir(parents=True, exist_ok=True)
    dst = trimmed_dir / src.name
    if src.exists() and (not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime):
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af",
             "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.15,"
             "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.3,areverse",
             str(dst)],
            check=True,
        )
    return dst


def dur(path: Path) -> float:
    raw = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True,
    ).strip()
    return float(raw)


# act: 1 = cold grade, 2 = warm grade, 0 = no grade (end card)
@dataclass
class Seg:
    path: Path
    start: float  # trim-in within source clip
    seconds: float
    act: int
    fade_from_black: float = 0.0
    fade_to_black: float = 0.0


@dataclass
class VoEvent:
    path: Path
    at: float


def build() -> None:
    # --- durations of VO lines drive the cut ---
    d = {k: dur(vo(k)) for k in [
        "v01-leaving", "v02-building", "v03-oneswitch", "v04-flips", "v05-anotherway",
        "v06-livewhere", "v07-ownedby", "v08-noswitch", "v09-golocal", "v10-brand",
    ]}

    segs: list[Seg] = []
    events: list[VoEvent] = []
    t = 0.0

    def add(path: Path, seconds: float, act: int, start: float = 0.0, **kw) -> None:
        nonlocal t
        segs.append(Seg(path, start, seconds, act, **kw))
        t += seconds

    # ---- Act 1: the tower ----
    v01_at = 0.8
    b1 = max(d["v01-leaving"] + 1.6, 9.6)  # S01+S02+S03
    s02_len = min(round(b1 * 0.30, 2), 2.5)  # camera drifts off the window after ~2.5s
    add(clip("s01-fiber", 8101), round(b1 * 0.34, 2), 1, fade_from_black=0.6)
    add(clip("s02-window", 8102), s02_len, 1)
    add(clip("s03-threads", 8103), round(b1 - b1 * 0.34 - s02_len, 2), 1)
    events.append(VoEvent(vo("v01-leaving"), v01_at))

    v02_at = t + 0.3
    b2 = max(d["v02-building"] + 1.0, 8.4)  # S04+S05
    add(clip("s04-monolith", 8104), round(b2 * 0.55, 2), 1)
    add(clip("s05-hall", 8105), round(b2 * 0.45, 2), 1)
    events.append(VoEvent(vo("v02-building"), v02_at))

    v03_at = t + 0.3
    b3 = 4.4  # S06 — hand slips off the lever after ~4.4s
    add(clip("s06-switch", 8186), b3, 1)
    events.append(VoEvent(vo("v03-oneswitch"), v03_at))

    # ---- The turn: blackout (no VO, SFX carries it) ----
    blackout_at = t
    add(clip("s07-shutdown", 8147), 4.4, 1)
    add(clip("s08-citydies", 8108), 3.6, 1)

    v04_at = t + 0.5
    add(clip("s09-darkroom", 8109), max(d["v04-flips"] + 1.4, 3.4), 1, fade_to_black=0.7)

    # ---- Act 2: the mesh ----
    v05_at = t + 0.5  # over the ember waking out of black
    add(clip("s10-ember", 8110), max(d["v05-anotherway"] + 1.6, 4.6), 2, fade_from_black=0.7)
    events.append(VoEvent(vo("v04-flips"), v04_at))
    events.append(VoEvent(vo("v05-anotherway"), v05_at))
    resolve_at = v05_at - 0.4

    v06_at = t + 0.2
    b6 = max(d["v06-livewhere"] + 1.2, 8.6)  # S11+S12
    add(clip("s11-circuit", 8111), round(b6 * 0.46, 2), 2)
    add(clip("s12-block", 8112), round(b6 * 0.54, 2), 2)
    events.append(VoEvent(vo("v06-livewhere"), v06_at))

    v07_at = t + 0.3
    add(clip("s13-mesh", 8113), max(d["v07-ownedby"] + 1.0, 4.6), 2)
    events.append(VoEvent(vo("v07-ownedby"), v07_at))

    v08_at = t - 0.6  # starts over the tail of s13; s14 capped before the bird swarm
    add(clip("s14-dawn", 8114), 4.6, 2, fade_to_black=0.8)
    events.append(VoEvent(vo("v08-noswitch"), v08_at))

    # ---- End card ----
    endcard_at = t
    endcard = OUT / "endcard-libertai-1920x1080.mp4"
    end_len = dur(endcard)
    add(endcard, end_len, 0)
    events.append(VoEvent(vo("v09-golocal"), endcard_at + 0.7))
    events.append(VoEvent(vo("v10-brand"), endcard_at + 0.7 + d["v09-golocal"] + 0.7))

    total = t
    print(f"total {total:.2f}s  blackout@{blackout_at:.2f}  resolve@{resolve_at:.2f}  endcard@{endcard_at:.2f}")

    missing = [str(s.path) for s in segs if not s.path.exists()]
    missing += [str(e.path) for e in events if not e.path.exists()]
    for bed in ["bed-tension", "bed-resolve", "sting-logo"]:
        if not (AUDIO / f"{bed}.wav").exists():
            missing.append(str(AUDIO / f"{bed}.wav"))
    if missing:
        raise SystemExit("missing inputs:\n" + "\n".join(sorted(set(missing))))

    # ---------- build ffmpeg graph ----------
    inputs: list[str] = []
    for s in segs:
        inputs += ["-i", str(s.path)]
    n_seg = len(segs)
    for e in events:
        inputs += ["-i", str(e.path)]
    i_tension = n_seg + len(events)
    i_resolve = i_tension + 1
    i_sting = i_tension + 2
    inputs += ["-i", str(AUDIO / "bed-tension.wav")]
    inputs += ["-i", str(AUDIO / "bed-resolve.wav")]
    inputs += ["-i", str(AUDIO / "sting-logo.wav")]

    parts: list[str] = []
    # video segments
    for idx, s in enumerate(segs):
        grade = {
            1: "eq=contrast=1.07:saturation=1.04:brightness=-0.015,colorbalance=bs=0.06:bm=0.02:rh=-0.02,",
            2: "eq=contrast=1.05:saturation=1.08:brightness=0.0,colorbalance=rm=0.03:bm=-0.02:bh=-0.04,",
            0: "",
        }[s.act]
        grain = "noise=alls=5:allf=t+u," if s.act else ""
        pad = f"scale={W}:{SHOT_H},pad={W}:{H}:0:{(H - SHOT_H) // 2}:black," if s.act else f"scale={W}:{H},"
        fades = ""
        if s.fade_from_black:
            fades += f"fade=t=in:st=0:d={s.fade_from_black},"
        if s.fade_to_black:
            fades += f"fade=t=out:st={s.seconds - s.fade_to_black:.3f}:d={s.fade_to_black},"
        parts.append(
            f"[{idx}:v]trim=start={s.start:.3f}:duration={s.seconds:.3f},setpts=PTS-STARTPTS,"
            f"fps={FPS},{pad}{grade}{grain}{fades}"
            f"setsar=1,format=yuv420p[v{idx}]"
        )
    concat_v = "".join(f"[v{i}]" for i in range(n_seg))
    parts.append(f"{concat_v}concat=n={n_seg}:v=1:a=0[vout]")

    # native shot audio as low sfx bed (concat, quiet, band-limited)
    cursor = 0.0
    sfx_labels = []
    for idx, s in enumerate(segs):
        if s.act == 0:
            parts.append(
                f"aevalsrc=0:d={s.seconds:.3f}:s=48000,aformat=channel_layouts=stereo[sa{idx}]"
            )
        else:
            parts.append(
                f"[{idx}:a]atrim=start={s.start:.3f}:duration={s.seconds:.3f},asetpts=PTS-STARTPTS,"
                f"aresample=48000,aformat=channel_layouts=stereo,"
                f"afade=t=in:st=0:d=0.25,afade=t=out:st={max(s.seconds - 0.3, 0):.3f}:d=0.3[sa{idx}]"
            )
        cursor += s.seconds
        sfx_labels.append(f"[sa{idx}]")
    parts.append(f"{''.join(sfx_labels)}concat=n={n_seg}:v=0:a=1,volume=0.5[sfx]")

    # VO events at absolute times -> one VO bus
    vo_labels = []
    for j, e in enumerate(events):
        idx = n_seg + j
        delay_ms = int(e.at * 1000)
        parts.append(
            f"[{idx}:a]aresample=48000,aformat=channel_layouts=stereo,"
            f"adelay={delay_ms}|{delay_ms}[vo{j}]"
        )
        vo_labels.append(f"[vo{j}]")
    parts.append(
        f"{''.join(vo_labels)}amix=inputs={len(events)}:normalize=0,"
        f"dynaudnorm=f=250:g=15:p=0.9,volume=1.0[vobus]"
    )

    # score: tension bed 0 -> blackout (hard fade at shutdown), resolve bed from ember
    tension_end = blackout_at + 2.2  # dies during the shutdown whoosh
    parts.append(
        f"[{i_tension}:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"atrim=0:{tension_end:.3f},afade=t=in:st=0:d=1.0,"
        f"afade=t=out:st={tension_end - 1.6:.3f}:d=1.6,apad=whole_dur={total:.3f}[bedA]"
    )
    resolve_len = min(dur(AUDIO / 'bed-resolve.wav'), total - resolve_at)
    parts.append(
        f"[{i_resolve}:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"atrim=0:{resolve_len:.3f},afade=t=in:st=0:d=1.8,"
        f"afade=t=out:st={resolve_len - 2.5:.3f}:d=2.5,"
        f"adelay={int(resolve_at * 1000)}|{int(resolve_at * 1000)},apad=whole_dur={total:.3f}[bedB]"
    )
    sting_at = endcard_at + 0.3
    parts.append(
        f"[{i_sting}:a]aresample=48000,aformat=channel_layouts=stereo,"
        f"volume=0.9,adelay={int(sting_at * 1000)}|{int(sting_at * 1000)},"
        f"apad=whole_dur={total:.3f}[sting]"
    )
    parts.append(f"[bedA][bedB]amix=inputs=2:normalize=0[score0]")
    parts.append(f"[score0][sting]amix=inputs=2:normalize=0,volume=0.85[score]")

    # duck score + sfx under VO
    parts.append(f"[vobus]asplit=2[voduck][vomix]")
    parts.append(
        f"[score][voduck]sidechaincompress=threshold=0.02:ratio=8:attack=25:release=500:makeup=1[scoreducked]"
    )
    parts.append(
        f"[scoreducked][sfx][vomix]amix=inputs=3:normalize=0:weights=1 0.45 1.6,"
        f"loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=0.92,"
        f"aformat=sample_rates=48000:channel_layouts=stereo,"
        f"afade=t=out:st={total - 1.0:.3f}:d=1.0[aout]"
    )

    filter_complex = ";".join(parts)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-c:a", "aac", "-b:a", "256k",
        "-movflags", "+faststart",
        "-t", f"{total:.3f}",
        str(FILM),
    ]
    subprocess.run(cmd, check=True)

    # QC
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(FILM), "-f", "null", "-"], check=True)
    sheet = FILM.with_suffix(".sheet.jpg")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(FILM),
         "-vf", "fps=1/2.5,scale=420:-1,tile=4x7", "-frames:v", "1", str(sheet)],
        check=True,
    )
    print(FILM)
    print(sheet)
    cursor = 0.0
    for s in segs:
        print(f"{cursor:05.2f}-{cursor + s.seconds:05.2f}  {s.path.name}")
        cursor += s.seconds
    for e in sorted(events, key=lambda e: e.at):
        print(f"VO @{e.at:05.2f}  {e.path.name}")


if __name__ == "__main__":
    build()
