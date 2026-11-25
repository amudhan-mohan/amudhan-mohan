"""Generate daily hero header SVGs with Tamil festival & cultural calendar variants."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TA_OUT = ROOT / "assets" / "ta" / "header.svg"
EN_OUT = ROOT / "assets" / "en" / "header.svg"
TA_CREST = ROOT / "assets" / "ta" / "tv-crest.svg"
EN_CREST = ROOT / "assets" / "en" / "tv-crest.svg"
PORTRAIT_PATH = ROOT / ".github" / "data" / "thiruvalluvar-portrait.svg"

IST = timezone(timedelta(hours=5, minutes=30))

# Verified lunar festival dates (Tiruvannamalai Maha Deepam & Deepavali, 2026-2028)
KARTHIGAI_DEEPAM_DATES = {date(2026, 11, 24), date(2027, 12, 12), date(2028, 12, 1)}
DEEPAVALI_DATES = {date(2026, 11, 8), date(2027, 10, 29), date(2028, 10, 17)}


def thiruvalluvar_year(day: date) -> int:
    """Compute Thiruvalluvar Year (Thai 1 / Jan 15 boundary: +31 from Jan 15, +30 before)."""
    return day.year + 30 if (day.month == 1 and day.day < 15) else day.year + 31


def detect_occasion(day: date) -> str | None:
    """Return festival key for a given date, or None on regular days."""
    if day in KARTHIGAI_DEEPAM_DATES:
        return "karthigai"
    if day in DEEPAVALI_DATES:
        return "deepavali"
    md = (day.month, day.day)
    fixed = {
        (1, 1): "new_year",
        (1, 14): "pongal",
        (1, 15): "thiruvalluvar",
        (4, 14): "puthandu",
        (9, 15): "engineers",
    }
    return fixed.get(md)


def festival_decor(occasion: str | None) -> str:
    """Return subtle hand-drawn SVG festival motif matching header.svg's art style."""
    if occasion in ("karthigai", "deepavali"):
        # Glowing clay agal vilakku lamps along the hill edge
        lamps = []
        for lx, ly in ((690, 368), (748, 366), (806, 364)):
            lamps.append(
                f'<g transform="translate({lx} {ly})" filter="url(#wob2)">'
                '<path d="M-13 0 Q0 10 13 0 L9 7 Q0 11 -9 7 Z" fill="#b5653a"/>'
                '<path d="M0 -13 C4 -7 5 -3 0 0 C-5 -3 -4 -7 0 -13Z" fill="#e8a621">'
                '<animateTransform attributeName="transform" type="scale" values="1 1;1.08 0.92;1 1" '
                'dur="1.8s" repeatCount="indefinite"/>'
                "</path>"
                '<circle cx="0" cy="-6" r="2.2" fill="#fffaf0" opacity="0.85"/>'
                "</g>"
            )
        return "".join(lamps)

    if occasion == "pongal":
        # Overflowing Pongal pot & twin sugarcane stalks beside the gopuram
        return (
            '<g transform="translate(808 358)" filter="url(#wob2)">'
            '<path d="M-24 14 L-16 -24 M-20 4 L-28 -2 M24 14 L18 -24 M20 2 L28 -4" '
            'stroke="#2f6a42" stroke-width="4" stroke-linecap="round" fill="none"/>'
            '<ellipse cx="0" cy="4" rx="16" ry="13" fill="#b5653a"/>'
            '<rect x="-11" y="-11" width="22" height="5" rx="2" fill="#9c522d"/>'
            '<path d="M-12 -11 Q-6 -20 0 -13 Q6 -21 12 -11 Q15 -5 10 -6 Q0 -10 -10 -6 Z" fill="#fffaf0"/>'
            "</g>"
        )

    if occasion == "puthandu":
        # Festive mango-leaf thoranam garland over top-right corner
        return (
            '<g transform="translate(760 22)" filter="url(#wob2)">'
            '<path d="M0 0 Q180 34 360 0" fill="none" stroke="#c4372c" stroke-width="2.6" stroke-linecap="round"/>'
            '<path d="M70 11 C82 14 82 32 70 40 C58 32 58 14 70 11Z" fill="#2f6a42"/>'
            '<path d="M140 17 C152 20 152 38 140 46 C128 38 128 20 140 17Z" fill="#3f7d4e"/>'
            '<path d="M210 17 C222 20 222 38 210 46 C198 38 198 20 210 17Z" fill="#2f6a42"/>'
            '<path d="M280 11 C292 14 292 32 280 40 C268 32 268 14 280 11Z" fill="#3f7d4e"/>'
            "</g>"
        )

    if occasion == "thiruvalluvar":
        # Golden palm-leaf scroll & stylus motif
        return (
            '<g transform="translate(778 342)" filter="url(#wob2)">'
            '<path d="M-36 -8 Q0 -14 36 -8 L38 10 Q0 16 -38 10 Z" fill="#dccb94" stroke="#8a7340" stroke-width="1.8"/>'
            '<line x1="-26" y1="0" x2="26" y2="0" stroke="#6b5226" stroke-width="1.6"/>'
            '<line x1="-22" y1="6" x2="18" y2="6" stroke="#6b5226" stroke-width="1.4"/>'
            "</g>"
        )

    if occasion in ("new_year", "engineers"):
        # Gentle gold sparkles in sky
        return (
            '<g fill="#e8a621" filter="url(#wob2)">'
            '<path d="M740 58 L743 66 L751 69 L743 72 L740 80 L737 72 L729 69 L737 66 Z"/>'
            '<path d="M810 42 L812 47 L817 49 L812 51 L810 56 L808 51 L803 49 L808 47 Z"/>'
            '<path d="M690 88 L692 93 L697 95 L692 97 L690 102 L688 97 L683 95 L688 93 Z"/>'
            "</g>"
        )

    return ""


GREETINGS = {
    None: ("Hello!", 34, "வணக்கம்!", 34),
    "new_year": ("Happy New Year!", 30, "புத்தாண்டு நல்வாழ்த்துக்கள்!", 24),
    "pongal": ("Happy Pongal!", 32, "இனிய பொங்கல் நல்வாழ்த்துக்கள்!", 24),
    "thiruvalluvar": ("Thiruvalluvar Day!", 30, "திருவள்ளுவர் தின வாழ்த்துக்கள்!", 23),
    "puthandu": ("Happy Tamil New Year!", 28, "தமிழ் புத்தாண்டு நல்வாழ்த்துக்கள்!", 23),
    "engineers": ("Happy Engineer’s Day!", 28, "பொறியாளர் தின நல்வாழ்த்துக்கள்!", 23),
    "deepavali": ("Happy Deepavali!", 31, "இனிய தீபாவளி நல்வாழ்த்துக்கள்!", 24),
    "karthigai": ("Happy Karthigai Deepam!", 28, "கார்த்திகை தீப நல்வாழ்த்துக்கள்!", 23),
}

# Precomputed landscape SVG layers (sky, animated sun, birds, hills, gopuram, palm trees, kolam border)
BASE_SCENE = (
    '<defs>'
    '<filter id="wob" x="-4%" y="-4%" width="108%" height="108%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="4" result="n"/>'
    '<feDisplacementMap in="SourceGraphic" in2="n" scale="4" xChannelSelector="R" yChannelSelector="G"/>'
    '</filter>'
    '<filter id="wob2" x="-4%" y="-4%" width="108%" height="108%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
    '<feDisplacementMap in="SourceGraphic" in2="n" scale="2.4" xChannelSelector="R" yChannelSelector="G"/>'
    '</filter>'
    '<filter id="grain" x="0" y="0" width="100%" height="100%">'
    '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8"/>'
    '<feColorMatrix type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.27  0 0 0 0 0.18  0.35 0 0 0 -0.09"/>'
    '</filter>'
    '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#f6cf9a"/><stop offset="0.55" stop-color="#fbe9cd"/><stop offset="1" stop-color="#f7f0df"/>'
    '</linearGradient>'
    '</defs>\n'
    '<rect width="1200" height="430" rx="22" fill="url(#sky)"/>'
    '<rect width="1200" height="430" rx="22" filter="url(#grain)"/>\n'
    '<g><animateTransform attributeName="transform" type="translate" from="0 90" to="0 0" dur="4s" fill="freeze"/>'
    '<circle cx="880" cy="262" r="62" fill="#e8a621" filter="url(#wob)"/>'
    '<g filter="url(#wob2)">'
    '<line x1="956.0" y1="262.0" x2="980.0" y2="262.0" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="950.2" y1="291.1" x2="972.4" y2="300.3" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="933.7" y1="315.7" x2="950.7" y2="332.7" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="909.1" y1="332.2" x2="918.3" y2="354.4" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="880.0" y1="338.0" x2="880.0" y2="362.0" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="850.9" y1="332.2" x2="841.7" y2="354.4" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="826.3" y1="315.7" x2="809.3" y2="332.7" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="809.8" y1="291.1" x2="787.6" y2="300.3" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="804.0" y1="262.0" x2="780.0" y2="262.0" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="809.8" y1="232.9" x2="787.6" y2="223.7" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="826.3" y1="208.3" x2="809.3" y2="191.3" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="850.9" y1="191.8" x2="841.7" y2="169.6" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="880.0" y1="186.0" x2="880.0" y2="162.0" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="909.1" y1="191.8" x2="918.3" y2="169.6" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="933.7" y1="208.3" x2="950.7" y2="191.3" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<line x1="950.2" y1="232.9" x2="972.4" y2="223.7" stroke="#e8a621" stroke-width="4" stroke-linecap="round"/>'
    '<animateTransform attributeName="transform" type="rotate" from="0 880 262" to="360 880 262" dur="120s" repeatCount="indefinite"/>'
    '</g></g>\n'
    '<path d="M0 0 q9 -9 18 0 q9 -9 18 0" fill="none" stroke="#3a2d28" stroke-width="2.6" stroke-linecap="round" opacity="0.7">'
    '<animateTransform attributeName="transform" type="translate" values="640 70;1180 36" dur="22s" begin="0s" repeatCount="indefinite"/></path>'
    '<path d="M0 0 q9 -9 18 0 q9 -9 18 0" fill="none" stroke="#3a2d28" stroke-width="2.6" stroke-linecap="round" opacity="0.7">'
    '<animateTransform attributeName="transform" type="translate" values="640 96;1180 62" dur="22s" begin="2.2s" repeatCount="indefinite"/></path>\n'
    '<path d="M0 372 Q260 330 560 362 T1200 350 L1200 430 L0 430Z" fill="#9cc07a" opacity="0.85" filter="url(#wob)"/>\n'
    '<path d="M0 392 Q300 362 640 388 T1200 376 L1200 430 L0 430Z" fill="#3f7d4e" filter="url(#wob)"/>\n'
    '<g fill="#4b3a52" filter="url(#wob2)">'
    '<rect x="910" y="348" width="200" height="44"/><path d="M996 392 V370 Q1010 354 1024 370 V392Z" fill="#f7f0df" opacity="0.92"/>'
    '<rect x="922.0" y="322" width="176" height="26"/><rect x="915.0" y="343" width="190" height="5"/>'
    '<rect x="935.6" y="328" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="970.8" y="328" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="1006.0" y="328" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="1041.2" y="328" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="1076.4" y="328" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="933.0" y="296" width="154" height="26"/><rect x="926.0" y="317" width="168" height="5"/>'
    '<rect x="948.25" y="302" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="986.75" y="302" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="1025.25" y="302" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="1063.75" y="302" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="944.0" y="270" width="132" height="26"/><rect x="937.0" y="291" width="146" height="5"/>'
    '<rect x="962.0" y="276" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="1006.0" y="276" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="1050.0" y="276" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="955.0" y="244" width="110" height="26"/><rect x="948.0" y="265" width="124" height="5"/>'
    '<rect x="969.3" y="250" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="1006.0" y="250" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="1042.7" y="250" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="966.0" y="218" width="88" height="26"/><rect x="959.0" y="239" width="102" height="5"/>'
    '<rect x="984.0" y="224" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="1028.0" y="224" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="977.0" y="192" width="66" height="26"/><rect x="970.0" y="213" width="80" height="5"/>'
    '<rect x="989.5" y="198" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="1022.5" y="198" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<rect x="988.0" y="166" width="44" height="26"/><rect x="981.0" y="187" width="58" height="5"/>'
    '<rect x="995.0" y="172" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/><rect x="1017.0" y="172" width="8" height="12" rx="4" fill="#f7f0df" opacity="0.28"/>'
    '<path d="M984 166 Q1010 130 1036 166Z"/>'
    '<ellipse cx="996" cy="140" rx="4.5" ry="9"/><ellipse cx="1010" cy="132" rx="4.5" ry="9"/><ellipse cx="1024" cy="140" rx="4.5" ry="9"/>'
    '</g>\n'
    '<g filter="url(#wob2)">'
    '<path d="M1118 396 Q1113.6 291.5 1096 206" fill="none" stroke="#5b4636" stroke-width="9.0" stroke-linecap="round"/>'
    '<path d="M1096 206 Q1060.3 180.2 1030.2 218.3" fill="none" stroke="#2f6a42" stroke-width="5.0" stroke-linecap="round"/>'
    '<path d="M1096 206 Q1071.6 155.6 1051.0 201.4" fill="none" stroke="#2f6a42" stroke-width="5.0" stroke-linecap="round"/>'
    '<path d="M1096 206 Q1089.4 142.9 1083.8 192.6" fill="none" stroke="#2f6a42" stroke-width="5.0" stroke-linecap="round"/>'
    '<path d="M1096 206 Q1109.0 145.5 1119.9 194.4" fill="none" stroke="#2f6a42" stroke-width="5.0" stroke-linecap="round"/>'
    '<path d="M1096 206 Q1125.1 162.7 1149.6 206.3" fill="none" stroke="#2f6a42" stroke-width="5.0" stroke-linecap="round"/>'
    '<path d="M1096 206 Q1132.7 185.0 1163.6 221.6" fill="none" stroke="#2f6a42" stroke-width="5.0" stroke-linecap="round"/>'
    '<path d="M1096 206 Q1133.4 210.1 1164.9 238.9" fill="none" stroke="#2f6a42" stroke-width="5.0" stroke-linecap="round"/>'
    '<circle cx="1092" cy="214" r="5" fill="#6a4a2a"/><circle cx="1101" cy="216" r="5" fill="#6a4a2a"/>'
    '</g>'
    '<g filter="url(#wob2)">'
    '<path d="M1166 400 Q1164.0 328.5 1156 270" fill="none" stroke="#5b4636" stroke-width="7.2" stroke-linecap="round"/>'
    '<path d="M1156 270 Q1127.4 248.1 1103.4 279.9" fill="none" stroke="#2f6a42" stroke-width="4.0" stroke-linecap="round"/>'
    '<path d="M1156 270 Q1136.5 228.5 1120.0 266.3" fill="none" stroke="#2f6a42" stroke-width="4.0" stroke-linecap="round"/>'
    '<path d="M1156 270 Q1150.7 218.3 1146.3 259.3" fill="none" stroke="#2f6a42" stroke-width="4.0" stroke-linecap="round"/>'
    '<path d="M1156 270 Q1166.4 220.4 1175.2 260.7" fill="none" stroke="#2f6a42" stroke-width="4.0" stroke-linecap="round"/>'
    '<path d="M1156 270 Q1179.3 234.2 1198.9 270.2" fill="none" stroke="#2f6a42" stroke-width="4.0" stroke-linecap="round"/>'
    '<path d="M1156 270 Q1185.4 252.0 1210.1 282.5" fill="none" stroke="#2f6a42" stroke-width="4.0" stroke-linecap="round"/>'
    '<path d="M1156 270 Q1185.9 272.1 1211.1 296.4" fill="none" stroke="#2f6a42" stroke-width="4.0" stroke-linecap="round"/>'
    '<circle cx="1152" cy="278" r="5" fill="#6a4a2a"/><circle cx="1161" cy="280" r="5" fill="#6a4a2a"/>'
    '</g>\n'
    + "".join(
        f'<path d="M{x:.1f} 394.0 Q{x + 20:.1f} 394.0 {x + 20:.1f} 414 Q{x + 20:.1f} 434.0 {x:.1f} 434.0 '
        f'Q{x - 20:.1f} 434.0 {x - 20:.1f} 414 Q{x - 20:.1f} 394.0 {x:.1f} 394.0Z" '
        'fill="none" stroke="#f7f0df" stroke-width="2.4" stroke-linejoin="round"/>'
        f'<path d="M{x:.1f} 406.0 L{x + 8:.1f} 414 L{x:.1f} 422.0 L{x - 8:.1f} 414Z" fill="none" stroke="#e8a621" stroke-width="2"/>'
        f'<circle cx="{x:.1f}" cy="414" r="2.4" fill="#e8a621"/>'
        f'<circle cx="{x + 38:.1f}" cy="414" r="3" fill="#e8a621"/>'
        for x in range(38, 1200, 76)
    )
)


def load_portrait_svg() -> tuple[str, str]:
    """Extract gradient <defs> and artwork <g> layers from the Thiruvalluvar portrait SVG."""
    raw = PORTRAIT_PATH.read_text(encoding="utf-8")
    m_defs = re.search(r"<defs>(.*?)</defs>", raw, re.DOTALL)
    defs_inner = m_defs.group(1).strip() if m_defs else ""
    after_defs = raw.split("</defs>", 1)[1] if "</defs>" in raw else raw
    body_inner = re.sub(r"</svg>\s*$", "", after_defs).strip()
    return defs_inner, body_inner


def build_tv_crest(lang: str, tv_year: int) -> str:
    """Build top-left Thiruvalluvar portrait statue + Thiruvalluvar Year crest SVG."""
    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"
    font_ta = "'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN','Noto Sans',sans-serif"
    font_ui = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"

    if lang == "ta":
        eyebrow = "தமிழ் நாட்காட்டி"
        title = f"திருவள்ளுவர் ஆண்டு {tv_year}"
        aria = f"திருவள்ளுவர் சிலை — திருவள்ளுவர் ஆண்டு {tv_year}"
        eyebrow_font, title_font, title_size = font_ta, font_ta, 14.5
    else:
        eyebrow = "TAMIL CALENDAR"
        title = f"Thiruvalluvar Year {tv_year}"
        aria = f"Thiruvalluvar Statue — Thiruvalluvar Year {tv_year}"
        eyebrow_font, title_font, title_size = font_ui, font_serif, 17.0

    portrait_defs, portrait_body = load_portrait_svg()

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 322 62" width="322" height="62" '
        f'role="img" aria-label="{escape(aria, quote=True)}">\n'
        "<defs>\n"
        '<filter id="wob2" x="-4%" y="-6%" width="108%" height="112%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="1.5" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>\n"
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.27  0 0 0 0 0.18  0.35 0 0 0 -0.09"/>'
        "</filter>\n"
        f"{portrait_defs}\n"
        "</defs>\n"
        '<rect x="2" y="2" width="318" height="58" rx="29" fill="#f7f0df" stroke="#8a7340" stroke-width="2.2" filter="url(#wob2)"/>\n'
        '<rect x="2" y="2" width="318" height="58" rx="29" filter="url(#grain)"/>\n'
        '<circle cx="33" cy="31" r="23.5" fill="#fbe9cd" stroke="#e8a621" stroke-opacity="0.7" stroke-width="1.4"/>\n'
        '<g transform="translate(10 6) scale(0.058)">\n'
        f"{portrait_body}\n"
        "</g>\n"
        f'<text x="66" y="23.5" font-family="{eyebrow_font}" font-size="10" font-weight="600" letter-spacing="0.5" fill="#7a6a5c" text-anchor="start">{escape(eyebrow)}</text>\n'
        f'<text x="66" y="44.5" font-family="{title_font}" font-size="{title_size}" font-weight="bold" fill="#4a3416" text-anchor="start">{escape(title)}</text>\n'
        "</svg>"
    )


def build_header(lang: str, occasion: str | None) -> str:
    """Build either English or Tamil header.svg with optional festival motif."""
    en_greet, en_size, ta_greet, ta_size = GREETINGS[occasion]
    decor = festival_decor(occasion)
    if lang == "en":
        font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"
        aria = f"Amudhan Mohan, B.E. CSE graduate and developer from Tamil Nadu. {en_greet}"
        text_block = (
            f'<text x="60" y="76" font-family="{font_serif}" font-size="{en_size}" font-weight="bold" font-style="italic" '
            f'fill="#c4372c" text-anchor="start" opacity="0"><animate attributeName="opacity" from="0" to="1" dur="1.4s" fill="freeze"/>{escape(en_greet)}</text>\n'
            f'<text x="60" y="150" font-family="{font_serif}" font-size="74" font-weight="bold" fill="#3a2d28" text-anchor="start">Amudhan Mohan</text>\n'
            '<g opacity="0"><animate attributeName="opacity" dur="12s" repeatCount="indefinite" keyTimes="0.000;0.040;0.293;0.333;1.000" values="0;1;1;0;0"/>'
            f'<text x="60" y="238" font-family="{font_serif}" font-size="32" font-style="italic" fill="#3a2d28" text-anchor="start">I build tools for students.</text></g>'
            '<g opacity="0"><animate attributeName="opacity" dur="12s" repeatCount="indefinite" keyTimes="0.000;0.333;0.373;0.627;0.667;1.000" values="0;0;1;1;0;0"/>'
            f'<text x="60" y="238" font-family="{font_serif}" font-size="32" font-style="italic" fill="#3a2d28" text-anchor="start">I keep sleepy servers awake.</text></g>'
            '<g opacity="0"><animate attributeName="opacity" dur="12s" repeatCount="indefinite" keyTimes="0.000;0.667;0.707;0.960;1.000" values="0;0;1;1;0"/>'
            f'<text x="60" y="238" font-family="{font_serif}" font-size="32" font-style="italic" fill="#3a2d28" text-anchor="start">I make websites for clients.</text></g>\n'
            f'<text x="60" y="296" font-family="{font_serif}" font-size="17" font-style="italic" fill="#7a6a5c" text-anchor="start">B.E. CSE graduate from Annamalai University, Tamil Nadu.</text>\n'
        )
    else:
        font_ta = "'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN','Noto Sans',sans-serif"
        font_mixed = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',sans-serif"
        aria = f"அமுதன் மோகன், தமிழ்நாட்டைச் சேர்ந்த B.E. CSE பட்டதாரி மற்றும் டெவலப்பர். {ta_greet}"
        text_block = (
            f'<text x="60" y="76" font-family="{font_ta}" font-size="{ta_size}" font-weight="bold" '
            f'fill="#c4372c" text-anchor="start" opacity="0"><animate attributeName="opacity" from="0" to="1" dur="1.4s" fill="freeze"/>{escape(ta_greet)}</text>\n'
            f'<text x="60" y="150" font-family="{font_ta}" font-size="64" font-weight="bold" fill="#3a2d28" text-anchor="start">அமுதன் மோகன்</text>\n'
            '<g opacity="0"><animate attributeName="opacity" dur="12s" repeatCount="indefinite" keyTimes="0.000;0.040;0.293;0.333;1.000" values="0;1;1;0;0"/>'
            f'<text x="60" y="238" font-family="{font_ta}" font-size="25.5" font-weight="bold" fill="#2f6a42" text-anchor="start">மாணவர்களுக்கான கருவிகளை உருவாக்குகிறேன்.</text></g>'
            '<g opacity="0"><animate attributeName="opacity" dur="12s" repeatCount="indefinite" keyTimes="0.000;0.333;0.373;0.627;0.667;1.000" values="0;0;1;1;0;0"/>'
            f'<text x="60" y="238" font-family="{font_ta}" font-size="26.5" font-weight="bold" fill="#2f6a42" text-anchor="start">உறங்கும் சர்வர்களை விழித்திருக்கச் செய்கிறேன்.</text></g>'
            '<g opacity="0"><animate attributeName="opacity" dur="12s" repeatCount="indefinite" keyTimes="0.000;0.667;0.707;0.960;1.000" values="0;0;1;1;0"/>'
            f'<text x="60" y="238" font-family="{font_ta}" font-size="21.0" font-weight="bold" fill="#2f6a42" text-anchor="start">வாடிக்கையாளர்களுக்கு இணையதளங்கள் உருவாக்குகிறேன்.</text></g>\n'
            f'<text x="60" y="296" font-family="{font_mixed}" font-size="17" fill="#7a6a5c" text-anchor="start">அண்ணாமலைப் பல்கலைக்கழக B.E. CSE பட்டதாரி, தமிழ்நாடு.</text>\n'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 430" width="1200" height="430" '
        f'role="img" aria-label="{escape(aria, quote=True)}">\n'
        f"{BASE_SCENE}\n"
        f"{decor}\n"
        f"{text_block}"
        "</svg>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Update hero header and Thiruvalluvar Year crest SVGs.")
    parser.add_argument("--date", type=date.fromisoformat, default=None, help="ISO date (YYYY-MM-DD)")
    args = parser.parse_args()

    day = args.date or datetime.now(IST).date()
    occasion = detect_occasion(day)
    tv_year = thiruvalluvar_year(day)

    EN_OUT.write_text(build_header("en", occasion), encoding="utf-8")
    TA_OUT.write_text(build_header("ta", occasion), encoding="utf-8")
    EN_CREST.write_text(build_tv_crest("en", tv_year), encoding="utf-8")
    TA_CREST.write_text(build_tv_crest("ta", tv_year), encoding="utf-8")
    print(f"Updated header.svg & tv-crest.svg for {day.isoformat()} (occasion={occasion or 'regular'}, TV {tv_year})")


if __name__ == "__main__":
    main()
