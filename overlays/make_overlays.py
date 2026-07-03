#!/usr/bin/env python3
"""Generate branded overlay plates (1080x1920 PNG with alpha) for the reels.

One SVG template, six configs. Aleph clips use Titillium Web + lime accent;
LibertAI clips use Inter + violet accent. Everything sits inside IG Reels
safe zones (nothing above y=300 except the small mark, nothing below y=1530).
"""

import subprocess
from pathlib import Path

HERE = Path(__file__).parent
HERE.mkdir(exist_ok=True)

ALEPH_MARK = """<g transform="translate({x},{y}) scale({s})" fill="{fill}">
<path d="M170.448 76.895c21.371 0 38.552-17.181 38.552-38.447C209 17.18 191.714 0 170.448 0c-21.372 0-38.552 17.181-38.552 38.448 0 21.266 17.18 38.447 38.552 38.447Z"/>
<path d="M38.553 208.057c21.371 0 38.552-17.181 38.552-38.448 0-21.267-17.286-38.448-38.552-38.448C17.181 131.161 0 148.342 0 169.609c-.104 21.267 17.182 38.448 38.553 38.448Z"/>
<path d="M143.106 11.314C106.544-3.772 62.858 3.457 33.106 33 3.353 62.647-3.875 106.019 11.21 142.476L143.106 11.314Z"/>
<path d="M65.792 196.847c36.562 15.086 80.247 7.857 110-21.686 29.752-29.647 36.98-73.018 21.895-109.475L65.792 196.847Z"/>
</g>"""

LIBERTAI_MARK = """<g transform="translate({x},{y}) scale({s})" fill="{fill}">
<path d="M111.245 0H59.3768V44.2796H111.245V96.1105H155.553V44.2796V0H111.245Z"/>
<path d="M103.687 110.722L59.3768 155H111.245L155.553 110.722H103.687Z"/>
<path d="M85.311 110.722H44.757V0L0.447266 44.2796V155H41.0012L85.311 110.722Z"/>
</g>"""

CONFIGS = [
    dict(name="core", brand="libertai", eyebrow="LIBERTAI",
         l1="Open models.", l2="Your machine.", footer="libertai.io"),
    dict(name="furnace", brand="libertai", eyebrow="LIBERTAI",
         l1="AI that doesn't", l2="phone home.", footer="libertai.io"),
    dict(name="monolith", brand="aleph", eyebrow="ALEPH CLOUD · CONFIDENTIAL COMPUTE",
         l1="Encrypted.", l2="Even while it runs.", footer="docs.aleph.cloud"),
    dict(name="prism", brand="aleph", eyebrow="ALEPH CLOUD · TOKEN MECHANICS",
         l1="Usage becomes", l2="buy pressure.", footer="tokenomics.aleph.cloud"),
    dict(name="gpu", brand="libertai", eyebrow="MADE WITH OPEN MODELS",
         l1="One GPU.", l2="Open weights.", footer="libertai.io"),
    dict(name="hall", brand="aleph", eyebrow="ALEPH CLOUD",
         l1="Sovereign by", l2="architecture.", footer="aleph.cloud"),
]

BRAND = {
    "aleph": dict(font="Titillium Web", accent="#d4ff00", muted="#c8adf0",
                  mark=ALEPH_MARK, mark_w=209, mark_h=209),
    "libertai": dict(font="Inter", accent="#c084fc", muted="#b9b9c9",
                     mark=LIBERTAI_MARK, mark_w=156, mark_h=155),
}

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <defs>
    <linearGradient id="scrim" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0c0c16" stop-opacity="0"/>
      <stop offset="0.45" stop-color="#0c0c16" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#0c0c16" stop-opacity="0.78"/>
    </linearGradient>
  </defs>
  <rect x="0" y="1020" width="1080" height="900" fill="url(#scrim)"/>
  {mark}
  <rect x="84" y="1196" width="72" height="5" fill="{accent}"/>
  <text x="84" y="1258" font-family="{font}" font-weight="700" font-size="27"
        letter-spacing="5.5" fill="{muted}">{eyebrow}</text>
  <text x="80" y="1360" font-family="{font}" font-weight="700" font-size="92"
        letter-spacing="-1" fill="#f9f4ff">{l1}</text>
  <text x="80" y="1462" font-family="{font}" font-weight="700" font-size="92"
        letter-spacing="-1" fill="{accent}">{l2}</text>
  <text x="84" y="1530" font-family="Source Code Pro" font-size="31"
        fill="{muted}">{footer}</text>
</svg>"""


def build() -> None:
    for cfg in CONFIGS:
        b = BRAND[cfg["brand"]]
        scale = 60 / b["mark_h"]
        mark = b["mark"].format(
            x=(1080 - b["mark_w"] * scale) / 2, y=310, s=scale,
            fill="#f9f4ff" if cfg["brand"] == "aleph" else "#e6dcff")
        svg = TEMPLATE.format(mark=mark, accent=b["accent"], muted=b["muted"],
                              font=b["font"], eyebrow=cfg["eyebrow"],
                              l1=cfg["l1"], l2=cfg["l2"], footer=cfg["footer"])
        svg_path = HERE / f"overlay-{cfg['name']}.svg"
        png_path = HERE / f"overlay-{cfg['name']}.png"
        svg_path.write_text(svg)
        subprocess.run(
            ["inkscape", str(svg_path), "--export-width=1080",
             "--export-height=1920", f"--export-filename={png_path}"],
            check=True, capture_output=True)
        print(f"wrote {png_path.name}")


if __name__ == "__main__":
    build()
