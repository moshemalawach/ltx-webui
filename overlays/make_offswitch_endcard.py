#!/usr/bin/env python3
"""Build the animated LibertAI end card for The Off Switch (1920x1080).

Renders layered SVGs to PNG with Inkscape, then animates bloom-in with
ffmpeg fades and a slow settle-zoom. Video only; the sting is mixed in
assembly.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs" / "offswitch"
WORK = OUT / "endcard"
W, H = 1920, 1080
FPS = 24
DUR = 8.0

MARK = """
    <path d="M111.245 0H59.3768V44.2796H111.245V96.1105H155.553V44.2796V0H111.245Z"/>
    <path d="M103.687 110.722L59.3768 155H111.245L155.553 110.722H103.687Z"/>
    <path d="M85.311 110.722H44.757V0L0.447266 44.2796V155H41.0012L85.311 110.722Z"/>
"""

LOGO_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="22"/>
    </filter>
    <radialGradient id="halo" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#7c3aed" stop-opacity="0.28"/>
      <stop offset="60%" stop-color="#7c3aed" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="#7c3aed" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="black"/>
  <ellipse cx="960" cy="470" rx="640" ry="420" fill="url(#halo)"/>
  <g transform="translate(843,330) scale(1.5)" fill="#c084fc" opacity="0.75" filter="url(#glow)">
    {MARK}
  </g>
  <g transform="translate(843,330) scale(1.5)" fill="#c084fc">
    {MARK}
  </g>
  <text x="960" y="700" text-anchor="middle" font-family="Inter, Montserrat, Arial, sans-serif"
        font-weight="800" font-size="86" letter-spacing="10" fill="#f9f4ff">LIBERTAI</text>
</svg>
"""

TAG_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="black" fill-opacity="0"/>
  <text x="960" y="800" text-anchor="middle" font-family="Inter, Montserrat, Arial, sans-serif"
        font-weight="500" font-size="40" letter-spacing="6" fill="#cbb8e8">GO LOCAL. GO DECENTRALIZED.</text>
</svg>
"""


def render_svg(svg: str, name: str) -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    src = WORK / f"{name}.svg"
    dst = WORK / f"{name}.png"
    src.write_text(svg)
    subprocess.run(
        ["inkscape", str(src), "--export-type=png", f"--export-filename={dst}",
         f"--export-width={W}", f"--export-height={H}"],
        check=True, capture_output=True,
    )
    return dst


def main() -> None:
    logo = render_svg(LOGO_SVG, "logo-layer")
    tag = render_svg(TAG_SVG, "tag-layer")
    out = OUT / "endcard-libertai-1920x1080.mp4"
    frames = int(DUR * FPS)
    filter_complex = (
        f"color=black:s={W}x{H}:r={FPS}:d={DUR}[bg];"
        f"[1:v]format=rgba,fade=t=in:st=0.5:d=1.4:alpha=1[logo];"
        f"[2:v]format=rgba,fade=t=in:st=2.1:d=0.9:alpha=1[tag];"
        f"[bg][logo]overlay=0:0[a];"
        f"[a][tag]overlay=0:0[b];"
        f"[b]zoompan=z='1.045-0.045*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":d=1:s={W}x{H}:fps={FPS},"
        f"fade=t=out:st={DUR-1.2}:d=1.2,format=yuv420p[v]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "lavfi", "-i", f"color=black:s={W}x{H}:r={FPS}:d={DUR}",
         "-loop", "1", "-t", str(DUR), "-i", str(logo),
         "-loop", "1", "-t", str(DUR), "-i", str(tag),
         "-filter_complex", filter_complex,
         "-map", "[v]", "-r", str(FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "17",
         str(out)],
        check=True,
    )
    print(out)


if __name__ == "__main__":
    main()
