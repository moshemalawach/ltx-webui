#!/usr/bin/env python3
"""V5 overlay plates: cinematic cold opens, lower thirds, and transparent
end lockups for footage-backed brand films."""

from __future__ import annotations

import html
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent

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

BRANDS = {
    "aleph": {
        "font": "Titillium Web",
        "mono": "Source Code Pro",
        "accent": "#d4ff00",
        "accent2": "#8b5cf6",
        "muted": "#c8adf0",
        "white": "#fbf8ff",
        "dark": "#070812",
        "mark": ALEPH_MARK,
        "mark_w": 209,
        "mark_h": 209,
        "mark_fill": "#d4ff00",
    },
    "libertai": {
        "font": "Inter",
        "mono": "Source Code Pro",
        "accent": "#c084fc",
        "accent2": "#f59e0b",
        "muted": "#cfc6df",
        "white": "#fbf8ff",
        "dark": "#08070d",
        "mark": LIBERTAI_MARK,
        "mark_w": 156,
        "mark_h": 155,
        "mark_fill": "#c084fc",
    },
}

SCRIM = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <defs>
    <linearGradient id="bottom" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#02030a" stop-opacity="0"/>
      <stop offset="0.34" stop-color="#02030a" stop-opacity="0.34"/>
      <stop offset="1" stop-color="#02030a" stop-opacity="0.84"/>
    </linearGradient>
    <linearGradient id="left" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#02030a" stop-opacity="0.48"/>
      <stop offset="0.58" stop-color="#02030a" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="0" y="980" width="1080" height="940" fill="url(#bottom)"/>
  <rect x="0" y="0" width="740" height="1920" fill="url(#left)"/>
</svg>"""

PLATES = [
    ("t5-arrive", "aleph", "INTAKE", "A workload", "enters the network.", "Routes before it reveals."),
    ("t5-machine", "aleph", "CONFIDENTIAL COMPUTE", "Encrypted", "while it runs.", "The machine sees work, not secrets."),
    ("t5-seam", "aleph", "SECURE BOUNDARY", "Plaintext", "stays out.", "The seam is policy made visible."),
    ("t5-out", "aleph", "TOKEN MECHANICS", "Usage becomes", "buy pressure.", "Demand returns to the network."),
    ("t5-channels", "aleph", "NETWORK FLOW", "Value routes", "back through.", "Compute, settlement, and signal in motion."),
    ("t5-terminal", "libertai", "LOCAL CONTROL", "Your terminal", "stays yours.", "Private prompts start on your machine."),
    ("t5-engine", "libertai", "OPEN MODELS", "Open weights.", "Real hardware.", "Inspect the stack you depend on."),
    ("t5-embers", "libertai", "MODEL FREEDOM", "No black box", "in the middle.", "Inference without the extra reader."),
    ("t5-response", "libertai", "PRIVATE BY DEFAULT", "No middleman", "reading along.", "The answer comes back clean."),
    ("t5-fan", "libertai", "LOCAL SPEED", "Fast enough", "to stay private.", "Keep the loop close."),
]

COLD_CARDS = [
    ("cold-aleph-v5", "aleph", "ALEPH CLOUD", "A workload enters", "a sovereign cloud.", "No single platform owns the path."),
    ("cold-libertai-v5", "libertai", "LIBERTAI", "Your AI should not", "phone home.", "Run open models with private local control."),
]

LOCKUPS = [
    ("lockup-aleph-v5", "aleph", "ALEPH CLOUD", "Sovereign compute for real workloads.", "aleph.cloud"),
    ("lockup-libertai-v5", "libertai", "LIBERTAI", "Private AI. Open models. Local control.", "libertai.io"),
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def brand_mark(brand: dict[str, str], x: float, y: float, height: float) -> str:
    scale = height / brand["mark_h"]
    return brand["mark"].format(x=x, y=y, s=scale, fill=brand["mark_fill"])


def render(name: str, svg: str) -> None:
    svg_path = HERE / f"{name}.svg"
    png_path = HERE / f"{name}.png"
    svg_path.write_text(svg, encoding="utf-8")
    subprocess.run(
        [
            "inkscape",
            str(svg_path),
            "--export-width=1080",
            "--export-height=1920",
            f"--export-filename={png_path}",
        ],
        check=True,
        capture_output=True,
    )
    print(f"wrote {png_path.name}")


def type_plate(name: str, brand_name: str, eyebrow: str, line1: str, line2: str, sub: str) -> None:
    b = BRANDS[brand_name]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <defs>
    <linearGradient id="plate" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{b['dark']}" stop-opacity="0"/>
      <stop offset="0.28" stop-color="{b['dark']}" stop-opacity="0.30"/>
      <stop offset="1" stop-color="{b['dark']}" stop-opacity="0.78"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">
      <feDropShadow dx="0" dy="12" stdDeviation="10" flood-color="#000000" flood-opacity="0.52"/>
    </filter>
  </defs>
  <rect x="0" y="1060" width="1080" height="620" fill="url(#plate)"/>
  <rect x="80" y="1166" width="78" height="5" fill="{b['accent']}"/>
  <text x="80" y="1230" font-family="{b['mono']}" font-weight="700" font-size="24"
        letter-spacing="4.5" fill="{b['muted']}" paint-order="stroke"
        stroke="#000000" stroke-opacity="0.55" stroke-width="3">{esc(eyebrow)}</text>
  <text x="78" y="1336" font-family="{b['font']}" font-weight="800" font-size="82"
        fill="{b['white']}" paint-order="stroke" stroke="#000000"
        stroke-opacity="0.58" stroke-width="7">{esc(line1)}</text>
  <text x="78" y="1432" font-family="{b['font']}" font-weight="800" font-size="82"
        fill="{b['accent']}" paint-order="stroke" stroke="#000000"
        stroke-opacity="0.58" stroke-width="7">{esc(line2)}</text>
  <text x="82" y="1506" font-family="{b['font']}" font-weight="500" font-size="31"
        fill="{b['muted']}" paint-order="stroke" stroke="#000000"
        stroke-opacity="0.52" stroke-width="4">{esc(sub)}</text>
</svg>"""
    render(name, svg)


def cold_card(name: str, brand_name: str, kicker: str, line1: str, line2: str, sub: str) -> None:
    b = BRANDS[brand_name]
    mark = brand_mark(b, 80, 326, 54)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <defs>
    <linearGradient id="shade" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{b['dark']}" stop-opacity="0.92"/>
      <stop offset="0.52" stop-color="{b['dark']}" stop-opacity="0.58"/>
      <stop offset="1" stop-color="{b['dark']}" stop-opacity="0.24"/>
    </linearGradient>
    <radialGradient id="halo" cx="0.22" cy="0.46" r="0.62">
      <stop offset="0" stop-color="{b['accent']}" stop-opacity="0.22"/>
      <stop offset="0.38" stop-color="{b['accent2']}" stop-opacity="0.10"/>
      <stop offset="1" stop-color="{b['accent']}" stop-opacity="0"/>
    </radialGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">
      <feDropShadow dx="0" dy="14" stdDeviation="12" flood-color="#000000" flood-opacity="0.64"/>
    </filter>
  </defs>
  <rect width="1080" height="1920" fill="url(#shade)"/>
  <rect width="1080" height="1920" fill="url(#halo)"/>
  {mark}
  <text x="154" y="368" font-family="{b['mono']}" font-weight="700" font-size="27"
        letter-spacing="5" fill="{b['muted']}" paint-order="stroke"
        stroke="#000000" stroke-opacity="0.56" stroke-width="3">{esc(kicker)}</text>
  <rect x="80" y="642" width="92" height="6" fill="{b['accent']}"/>
  <text x="76" y="764" font-family="{b['font']}" font-weight="800" font-size="98"
        fill="{b['white']}" paint-order="stroke" stroke="#000000"
        stroke-opacity="0.60" stroke-width="8">{esc(line1)}</text>
  <text x="76" y="878" font-family="{b['font']}" font-weight="800" font-size="98"
        fill="{b['accent']}" paint-order="stroke" stroke="#000000"
        stroke-opacity="0.60" stroke-width="8">{esc(line2)}</text>
  <text x="82" y="972" font-family="{b['font']}" font-weight="500" font-size="34"
        fill="{b['muted']}" paint-order="stroke" stroke="#000000"
        stroke-opacity="0.56" stroke-width="4">{esc(sub)}</text>
</svg>"""
    render(name, svg)


def lockup(name: str, brand_name: str, title: str, tagline: str, url: str) -> None:
    b = BRANDS[brand_name]
    mark_height = 120 if brand_name == "aleph" else 116
    mark_x = (1080 - b["mark_w"] * mark_height / b["mark_h"]) / 2
    mark = brand_mark(b, mark_x, 650, mark_height)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920">
  <defs>
    <radialGradient id="halo" cx="0.5" cy="0.46" r="0.50">
      <stop offset="0" stop-color="{b['accent']}" stop-opacity="0.34"/>
      <stop offset="0.46" stop-color="{b['accent2']}" stop-opacity="0.11"/>
      <stop offset="1" stop-color="{b['accent']}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{b['dark']}" stop-opacity="0.22"/>
      <stop offset="0.50" stop-color="{b['dark']}" stop-opacity="0.50"/>
      <stop offset="1" stop-color="{b['dark']}" stop-opacity="0.76"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="150%">
      <feDropShadow dx="0" dy="16" stdDeviation="14" flood-color="#000000" flood-opacity="0.72"/>
    </filter>
  </defs>
  <rect width="1080" height="1920" fill="url(#shade)"/>
  <rect width="1080" height="1920" fill="url(#halo)"/>
  {mark}
  <text x="540" y="890" text-anchor="middle" font-family="{b['font']}" font-weight="800"
        font-size="72" letter-spacing="7" fill="{b['white']}" paint-order="stroke"
        stroke="#000000" stroke-opacity="0.62" stroke-width="7">{esc(title)}</text>
  <text x="540" y="986" text-anchor="middle" font-family="{b['font']}" font-weight="500"
        font-size="38" fill="{b['muted']}" paint-order="stroke"
        stroke="#000000" stroke-opacity="0.56" stroke-width="4">{esc(tagline)}</text>
  <text x="540" y="1084" text-anchor="middle" font-family="{b['mono']}" font-weight="700"
        font-size="34" fill="{b['accent']}" paint-order="stroke"
        stroke="#000000" stroke-opacity="0.56" stroke-width="4">{esc(url)}</text>
</svg>"""
    render(name, svg)


def main() -> None:
    render("scrim-v5", SCRIM)
    for args in COLD_CARDS:
        cold_card(*args)
    for args in PLATES:
        type_plate(*args)
    for args in LOCKUPS:
        lockup(*args)


if __name__ == "__main__":
    main()
