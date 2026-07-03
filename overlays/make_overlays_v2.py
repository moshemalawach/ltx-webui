#!/usr/bin/env python3
"""V2 overlay system: separate scrim plate + type-only plates (slidable) +
cold-open cards. All 1080x1920 PNG with alpha."""

import subprocess
from pathlib import Path

HERE = Path(__file__).parent

SCRIM = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <defs><linearGradient id="s" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#0c0c16" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#0c0c16" stop-opacity="0.30"/>
    <stop offset="1" stop-color="#0c0c16" stop-opacity="0.74"/>
  </linearGradient></defs>
  <rect x="0" y="1060" width="1080" height="860" fill="url(#s)"/>
</svg>"""

TYPE_TPL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <rect x="84" y="1216" width="72" height="5" fill="{accent}"/>
  <text x="84" y="1278" font-family="{font}" font-weight="700" font-size="27"
        letter-spacing="5.5" fill="{muted}">{eyebrow}</text>
  <text x="80" y="1382" font-family="{font}" font-weight="700" font-size="96"
        letter-spacing="-1" fill="#f9f4ff">{l1}</text>
  <text x="80" y="1486" font-family="{font}" font-weight="700" font-size="96"
        letter-spacing="-1" fill="{accent}">{l2}</text>
</svg>"""

COLD_TPL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <text x="540" y="944" text-anchor="middle" font-family="Source Code Pro"
        font-size="34" letter-spacing="6" fill="{color}">{line1}</text>
  <text x="540" y="1000" text-anchor="middle" font-family="Source Code Pro"
        font-size="34" letter-spacing="6" fill="{color}">{line2}</text>
</svg>"""

ALEPH = dict(font="Titillium Web", accent="#d4ff00", muted="#c8adf0")
LIB = dict(font="Inter", accent="#c084fc", muted="#b9b9c9")

PLATES = [
    ("t2-arrive", ALEPH, "ALEPH CLOUD", "Decentralized", "by design."),
    ("t2-machine", ALEPH, "CONFIDENTIAL COMPUTE", "Encrypted.", "Even while it runs."),
    ("t2-out", ALEPH, "TOKEN MECHANICS", "Usage becomes", "buy pressure."),
    ("t2-terminal", LIB, "LIBERTAI", "Your terminal.", ""),
    ("t2-engine", LIB, "OPEN MODELS", "Our engine,", "open weights."),
    ("t2-response", LIB, "NO MIDDLEMAN READING ALONG", "Private,", "end to end."),
]

COLDS = [
    ("cold-aleph", "#c8adf0", "FOLLOW A WORKLOAD", "THROUGH A SOVEREIGN CLOUD"),
    ("cold-libertai", "#b9b9c9", "WHERE DOES YOUR AI", "ACTUALLY RUN?"),
]


def render(name: str, svg: str) -> None:
    p = HERE / f"{name}.svg"
    p.write_text(svg)
    subprocess.run(["inkscape", str(p), "--export-width=1080",
                    "--export-height=1920",
                    f"--export-filename={HERE / (name + '.png')}"],
                   check=True, capture_output=True)
    print("wrote", name + ".png")


render("scrim", SCRIM)
for name, b, eyebrow, l1, l2 in PLATES:
    render(name, TYPE_TPL.format(font=b["font"], accent=b["accent"],
                                 muted=b["muted"], eyebrow=eyebrow, l1=l1, l2=l2))
for name, color, line1, line2 in COLDS:
    render(name, COLD_TPL.format(color=color, line1=line1, line2=line2))
