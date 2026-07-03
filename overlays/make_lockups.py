#!/usr/bin/env python3
"""End-lockup plates (full-bleed 1080x1920) for the two brand films."""
import subprocess
from pathlib import Path

HERE = Path(__file__).parent

ALEPH_MARK = open("aleph_mark.frag").read() if Path("aleph_mark.frag").exists() else None

TPL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="0.9" y2="1">
      <stop offset="0" stop-color="{bg0}"/>
      <stop offset="1" stop-color="{bg1}"/>
    </linearGradient>
    <radialGradient id="halo" cx="0.5" cy="0.42" r="0.5">
      <stop offset="0" stop-color="{halo}" stop-opacity="0.30"/>
      <stop offset="1" stop-color="{halo}" stop-opacity="0"/>
    </radialGradient>
    <filter id="noise" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3"/>
      <feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.04 0"/>
    </filter>
  </defs>
  <rect width="1080" height="1920" fill="url(#g)"/>
  <rect width="1080" height="1920" fill="url(#halo)"/>
  <rect width="1080" height="1920" filter="url(#noise)" opacity="0.5"/>
  {mark}
  <text x="540" y="1010" text-anchor="middle" font-family="{font}" font-weight="700"
        font-size="58" letter-spacing="10" fill="#f9f4ff">{name}</text>
  <text x="540" y="1092" text-anchor="middle" font-family="{font}" font-weight="600"
        font-size="37" fill="{muted}">{tagline}</text>
  <text x="540" y="1180" text-anchor="middle" font-family="Source Code Pro"
        font-size="33" fill="{accent}">{url}</text>
</svg>"""

ALEPH = """<g transform="translate(468,760) scale(0.6890)" fill="#d4ff00">
<path d="M170.448 76.895c21.371 0 38.552-17.181 38.552-38.447C209 17.18 191.714 0 170.448 0c-21.372 0-38.552 17.181-38.552 38.448 0 21.266 17.18 38.447 38.552 38.447Z"/>
<path d="M38.553 208.057c21.371 0 38.552-17.181 38.552-38.448 0-21.267-17.286-38.448-38.552-38.448C17.181 131.161 0 148.342 0 169.609c-.104 21.267 17.182 38.448 38.553 38.448Z"/>
<path d="M143.106 11.314C106.544-3.772 62.858 3.457 33.106 33 3.353 62.647-3.875 106.019 11.21 142.476L143.106 11.314Z"/>
<path d="M65.792 196.847c36.562 15.086 80.247 7.857 110-21.686 29.752-29.647 36.98-73.018 21.895-109.475L65.792 196.847Z"/>
</g>"""

LIB = """<g transform="translate(468,762) scale(0.9226)" fill="#c084fc">
<path d="M111.245 0H59.3768V44.2796H111.245V96.1105H155.553V44.2796V0H111.245Z"/>
<path d="M103.687 110.722L59.3768 155H111.245L155.553 110.722H103.687Z"/>
<path d="M85.311 110.722H44.757V0L0.447266 44.2796V155H41.0012L85.311 110.722Z"/>
</g>"""

for cfg in [
    dict(out="lockup-aleph", bg0="#141421", bg1="#3a0b8f", halo="#5100cd",
         mark=ALEPH, font="Titillium Web", name="ALEPH CLOUD",
         tagline="Sovereign by architecture.", url="aleph.cloud",
         muted="#c8adf0", accent="#d4ff00"),
    dict(out="lockup-libertai", bg0="#0d0b14", bg1="#2c1150", halo="#8b5cf6",
         mark=LIB, font="Inter", name="LIBERTAI",
         tagline="Your terminal. Our engine.", url="libertai.io",
         muted="#b9b9c9", accent="#c084fc"),
]:
    svg = HERE / f"{cfg['out']}.svg"
    png = HERE / f"{cfg['out']}.png"
    svg.write_text(TPL.format(**cfg))
    subprocess.run(["inkscape", str(svg), "--export-width=1080",
                    "--export-height=1920", f"--export-filename={png}"],
                   check=True, capture_output=True)
    print("wrote", png.name)
