"""Generate signboard SVGs with live job & freelance availability badge."""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / ".github" / "profile-config.json"
EN_OUT = ROOT / "assets" / "en" / "signboard.svg"
TA_OUT = ROOT / "assets" / "ta" / "signboard.svg"

AVAILABILITY_STATES = {
    "open": {
        "dot": "#9cc07a",
        "pill_fill": "#2f6a42",
        "pill_stroke": "#9cc07a",
        "en": ("Open to SDE / Full-Stack roles & client sites", 368),
        "ta": ("மென்பொருள் பணி & இணையதளங்களுக்குத் தயார்", 444),
    },
    "freelance": {
        "dot": "#9cc07a",
        "pill_fill": "#2f6a42",
        "pill_stroke": "#9cc07a",
        "en": ("Available for client websites", 268),
        "ta": ("வாடிக்கையாளர் இணையதளங்களுக்குத் தயார்", 398),
    },
    "busy": {
        "dot": "#f6cf9a",
        "pill_fill": "#5b4636",
        "pill_stroke": "#e8a621",
        "en": ("Currently booked — replies in 2–3 days", 338),
        "ta": ("தற்போது பணியில் — 2–3 நாட்களில் பதில்", 394),
    },
}


def build_signboard(lang: str, status: str) -> str:
    """Build English or Tamil signboard SVG with availability pill."""
    cfg = AVAILABILITY_STATES[status]
    badge_text, badge_w = cfg[lang]
    dot_color = cfg["dot"]
    pill_fill = cfg["pill_fill"]
    pill_stroke = cfg["pill_stroke"]

    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"
    font_ta = "'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN','Noto Sans',sans-serif"
    font_ui = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"

    pill_svg = (
        f'<g transform="translate(108 66)">'
        f'<rect width="{badge_w}" height="28" rx="14" fill="{pill_fill}" stroke="{pill_stroke}" stroke-width="1.6" filter="url(#wob2)"/>'
        f'<circle cx="16" cy="14" r="4.5" fill="{dot_color}">'
        '<animate attributeName="opacity" values="1;0.4;1" dur="2.8s" repeatCount="indefinite"/>'
        "</circle>"
        f'<text x="29" y="18.5" font-family="{font_ui if lang == "en" else font_ta}" font-size="13" font-weight="600" '
        f'fill="#fffaf0" text-anchor="start">{escape(badge_text)}</text>'
        "</g>"
    )

    if lang == "en":
        aria = f"Need a website? {badge_text}. I build custom sites for clients, from the first sketch to the live URL. Let’s talk."
        body = (
            f'<text x="108" y="148" font-family="{font_serif}" font-size="42" font-weight="bold" font-style="italic" '
            'fill="#e8a621" text-anchor="start">Need a website?</text>\n'
            f'<text x="108" y="188" font-family="{font_serif}" font-size="19" font-style="italic" '
            'fill="#f3e9d2" text-anchor="start">I build custom sites for clients, from the first sketch to the live URL.</text>\n'
            '<g transform="translate(940 144) rotate(-8)"><g>'
            '<animateTransform attributeName="transform" type="scale" values="1.7;1;1" keyTimes="0;0.25;1" dur="6s" begin="0.8s" repeatCount="indefinite"/>'
            '<circle r="62" fill="none" stroke="#c4372c" stroke-width="6" filter="url(#wob)"/>'
            '<circle r="51" fill="none" stroke="#c4372c" stroke-width="2" stroke-dasharray="3 6"/>'
            '<circle r="62" fill="#c4372c" opacity="0.14"/>'
            f'<text x="0" y="8" font-family="{font_serif}" font-size="24" font-weight="bold" font-style="italic" '
            'fill="#ff8a7d" text-anchor="middle">Let’s talk</text></g></g>\n'
        )
    else:
        aria = f"இணையதளம் வேண்டுமா? {badge_text}. முதல் வரைபடம் முதல் இணையத்தில் வெளியிடும் வரை உருவாக்குகிறேன். பேசலாம்."
        body = (
            f'<text x="108" y="140" font-family="{font_ta}" font-size="37" font-weight="bold" '
            'fill="#e8a621" text-anchor="start">இணையதளம் வேண்டுமா?</text>\n'
            f'<text x="108" y="176" font-family="{font_ta}" font-size="16" '
            'fill="#f3e9d2" text-anchor="start">முதல் வரைபடம் முதல் இணையத்தில் வெளியிடும் வரை,</text>\n'
            f'<text x="108" y="201" font-family="{font_ta}" font-size="16" '
            'fill="#e9d8a6" text-anchor="start">வாடிக்கையாளர்களுக்கான இணையதளங்களை உருவாக்குகிறேன்.</text>\n'
            '<g transform="translate(940 144) rotate(-8)"><g>'
            '<animateTransform attributeName="transform" type="scale" values="1.7;1;1" keyTimes="0;0.25;1" dur="6s" begin="0.8s" repeatCount="indefinite"/>'
            '<circle r="62" fill="none" stroke="#c4372c" stroke-width="6" filter="url(#wob)"/>'
            '<circle r="51" fill="none" stroke="#c4372c" stroke-width="2" stroke-dasharray="3 6"/>'
            '<circle r="62" fill="#c4372c" opacity="0.14"/>'
            f'<text x="0" y="8" font-family="{font_ta}" font-size="22" font-weight="bold" '
            'fill="#ff8a7d" text-anchor="middle">பேசலாம்</text></g></g>\n'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 286" width="1160" height="286" '
        f'role="img" aria-label="{escape(aria, quote=True)}">\n'
        "<defs>"
        '<filter id="wob" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="4" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="4" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>"
        '<filter id="wob2" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="2.4" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>"
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.27  0 0 0 0 0.18  0.35 0 0 0 -0.09"/>'
        "</filter>"
        '<filter id="soft" x="-10%" y="-10%" width="120%" height="130%">'
        '<feGaussianBlur stdDeviation="5"/>'
        "</filter>"
        "</defs>\n"
        '<path d="M150 0 L170 40 M1010 0 L990 40" stroke="#8a6a4a" stroke-width="5" stroke-linecap="round" fill="none" filter="url(#wob2)"/>\n'
        '<rect x="56" y="36" width="1048" height="226" rx="12" fill="#00000030" filter="url(#soft)"/>\n'
        '<rect x="60" y="34" width="1040" height="220" rx="10" fill="#2d3b6b" filter="url(#wob)"/>\n'
        '<rect x="60" y="34" width="1040" height="220" rx="10" filter="url(#grain)"/>\n'
        '<rect x="78" y="52" width="1004" height="184" rx="6" fill="none" stroke="#e8a621" stroke-width="3" stroke-dasharray="14 7" filter="url(#wob2)"/>\n'
        f"{pill_svg}\n"
        f"{body}"
        "</svg>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Update signboard SVGs with availability status.")
    parser.add_argument("--status", choices=sorted(AVAILABILITY_STATES), default=None)
    args = parser.parse_args()

    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    status = args.status or cfg.get("availability", "open")
    if status not in AVAILABILITY_STATES:
        raise ValueError(f"Unsupported availability status: {status}")

    EN_OUT.write_text(build_signboard("en", status), encoding="utf-8")
    TA_OUT.write_text(build_signboard("ta", status), encoding="utf-8")
    print(f"Updated signboard.svg (availability={status})")


if __name__ == "__main__":
    main()
