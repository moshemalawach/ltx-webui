#!/usr/bin/env python3
"""Render plates for the standalone sovereign AI short."""

from html import escape
from pathlib import Path
import subprocess

HERE = Path(__file__).parent

W = 1080
H = 1920

FONT = "Inter, Arial, sans-serif"
MONO = "Source Code Pro, monospace"
FG = "#f7fbff"
MUTED = "#aeb8c7"
AMBER = "#ffd166"
CYAN = "#8bd7ff"
RED = "#ff4d5f"


def render(name: str, svg: str) -> None:
    svg_path = HERE / f"{name}.svg"
    png_path = HERE / f"{name}.png"
    svg_path.write_text(svg)
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


def text(x: int, y: int, value: str, size: int, fill: str, weight: int = 700) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-weight="{weight}" '
        f'font-size="{size}" letter-spacing="0" fill="{fill}">{escape(value)}</text>'
    )


def plate(name: str, eyebrow: str, line1: str, line2: str, accent: str) -> None:
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  <rect x="78" y="1190" width="76" height="5" fill="{accent}"/>
  <text x="78" y="1254" font-family="{MONO}" font-size="28" letter-spacing="4"
        fill="{MUTED}">{escape(eyebrow)}</text>
  {text(76, 1360, line1, 88, FG)}
  {text(76, 1462, line2, 88, accent)}
</svg>"""
    render(name, svg)


SCRIM = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bottom" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#02050a" stop-opacity="0"/>
      <stop offset="0.42" stop-color="#02050a" stop-opacity="0.18"/>
      <stop offset="1" stop-color="#02050a" stop-opacity="0.76"/>
    </linearGradient>
    <linearGradient id="top" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#02050a" stop-opacity="0.42"/>
      <stop offset="1" stop-color="#02050a" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect x="0" y="0" width="{W}" height="520" fill="url(#top)"/>
  <rect x="0" y="980" width="{W}" height="940" fill="url(#bottom)"/>
</svg>"""

COLD = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" fill="#02050a"/>
  <rect x="410" y="786" width="260" height="3" fill="{CYAN}" opacity="0.72"/>
  <text x="540" y="890" text-anchor="middle" font-family="{MONO}" font-size="32"
        letter-spacing="5" fill="{MUTED}">WHO OWNS THE MODEL</text>
  <text x="540" y="970" text-anchor="middle" font-family="{FONT}" font-weight="800"
        font-size="68" letter-spacing="0" fill="{FG}">OWNS THE FUTURE</text>
  <rect x="490" y="1030" width="100" height="3" fill="{AMBER}" opacity="0.9"/>
</svg>"""

END = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">
  <defs>
    <radialGradient id="glow" cx="50%" cy="46%" r="58%">
      <stop offset="0" stop-color="#22415a" stop-opacity="0.8"/>
      <stop offset="0.42" stop-color="#06131f" stop-opacity="0.75"/>
      <stop offset="1" stop-color="#02050a" stop-opacity="1"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <g opacity="0.24" stroke="{CYAN}" stroke-width="1">
    <path d="M130 720 C300 610 430 660 540 548 C670 420 806 515 948 388"/>
    <path d="M116 980 C326 860 430 938 548 784 C690 596 816 710 958 596"/>
    <path d="M132 1218 C304 1102 442 1160 538 1040 C662 886 792 990 948 850"/>
  </g>
  <circle cx="540" cy="900" r="118" fill="none" stroke="{AMBER}" stroke-width="3" opacity="0.78"/>
  <circle cx="540" cy="900" r="54" fill="{AMBER}" opacity="0.18"/>
  <text x="540" y="1176" text-anchor="middle" font-family="{FONT}" font-weight="850"
        font-size="86" letter-spacing="0" fill="{FG}">SOVEREIGN AI</text>
  <text x="540" y="1252" text-anchor="middle" font-family="{MONO}" font-size="30"
        letter-spacing="3.5" fill="{MUTED}">RUN IT · VERIFY IT · KEEP IT CLOSE</text>
</svg>"""


def main() -> None:
    render("svai-scrim", SCRIM)
    render("svai-cold", COLD)
    render("svai-end", END)
    plate("svai-t01", "CENTRALIZED AI", "One tower.", "One choke point.", CYAN)
    plate("svai-t02", "EXTRACTION RISK", "Your memory", "becomes their map.", RED)
    plate("svai-t03", "LOCAL INTELLIGENCE", "The model can", "stay with you.", AMBER)
    plate("svai-t04", "SYSTEMIC FRAGILITY", "Centralized power", "fails centrally.", RED)
    plate("svai-t05", "SOVEREIGN MESH", "Small nodes", "route around control.", AMBER)
    plate("svai-t06", "PUBLIC COMPUTE", "Shared intelligence.", "No single owner.", CYAN)


if __name__ == "__main__":
    main()
