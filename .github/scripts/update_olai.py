"""Generate daily Thirukkural palm-leaf (olai) SVGs, toggle pills, and meaning cards."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / ".github" / "data" / "thirukkural.json"
TA_OLAI = ROOT / "assets" / "ta" / "olai.svg"
EN_OLAI = ROOT / "assets" / "en" / "olai.svg"
TA_BTN = ROOT / "assets" / "ta" / "olai-btn.svg"
EN_BTN = ROOT / "assets" / "en" / "olai-btn.svg"
TA_MEANING = ROOT / "assets" / "ta" / "olai-meaning.svg"
EN_MEANING = ROOT / "assets" / "en" / "olai-meaning.svg"

IST = timezone(timedelta(hours=5, minutes=30))
# Anchor so day-by-day progression cycles through all 1,330 kurals in order.
EPOCH = date(2026, 1, 1)


def split_couplet(text: str) -> list[str]:
    """Split an English couplet into at most two balanced lines."""
    text = " ".join(text.split())
    if ";" in text:
        first, second = text.split(";", 1)
        a, b = f"{first.strip()};", second.strip()
        if 15 < len(a) <= 78 and 15 < len(b) <= 78:
            return [a, b]
    for width in range(max(45, len(text) // 2), 82):
        lines = textwrap.wrap(text, width=width)
        if len(lines) <= 2:
            return lines
    return textwrap.wrap(text, width=74)[:2]


def wrap_lines(text: str, width: int) -> list[str]:
    """Wrap prose cleanly on word boundaries."""
    return textwrap.wrap(" ".join(text.split()), width=width) or [""]


def tamil_font_size(line1: str, line2: str) -> float:
    """Scale Tamil font size down smoothly for extra-long lines."""
    max_len = max(len(line1), len(line2))
    if max_len <= 37:
        return 28.0
    return round(max(21.0, 28.0 * 37.0 / max_len), 1)


def english_font_size(lines: list[str]) -> float:
    """Scale English font size down smoothly so lines stay inside the palm leaf."""
    max_len = max(len(line) for line in lines)
    if max_len <= 56:
        return 21.5
    return round(max(16.0, 21.5 * 56.0 / max_len), 1)


def render_shell(aria_label: str, body: str) -> str:
    """Wrap kural content in the shared palm-leaf (Olai Chuvadi) SVG template."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 256" width="1160" height="256" '
        f'role="img" aria-label="{escape(aria_label, quote=True)}">\n'
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
        "</defs>\n"
        '<rect width="1160" height="256" rx="18" fill="#f7f0df"/>'
        '<rect width="1160" height="256" rx="18" filter="url(#grain)"/>\n'
        '<path d="M0 128 H112 M1048 128 H1160" stroke="#c4372c" stroke-width="5" '
        'stroke-linecap="round" filter="url(#wob2)"/>\n'
        '<g filter="url(#wob)">'
        '<path d="M30 28 Q580 14 1130 28 L1138 40 L1138 216 L1130 228 Q580 240 30 228 L22 216 L22 40Z" '
        'fill="#dccb94"/>'
        "</g>\n"
        '<g clip-path="url(#lf)">'
        '<path d="M30 28 Q580 14 1130 28 L1138 40 L1138 216 L1130 228 Q580 240 30 228 L22 216 L22 40Z" '
        'fill="#d5c283" opacity="0.5"/>'
        '<path d="M30 56 q300 5 600 0 t 570 0" fill="none" stroke="#9a8447" stroke-opacity="0.28" stroke-width="1.6"/>'
        '<path d="M30 92 q300 -5 600 0 t 570 0" fill="none" stroke="#9a8447" stroke-opacity="0.28" stroke-width="1.6"/>'
        '<path d="M30 128 q300 5 600 0 t 570 0" fill="none" stroke="#9a8447" stroke-opacity="0.28" stroke-width="1.6"/>'
        '<path d="M30 164 q300 -5 600 0 t 570 0" fill="none" stroke="#9a8447" stroke-opacity="0.28" stroke-width="1.6"/>'
        '<path d="M30 200 q300 5 600 0 t 570 0" fill="none" stroke="#9a8447" stroke-opacity="0.28" stroke-width="1.6"/>'
        "</g>\n"
        '<clipPath id="lf"><rect x="22" y="20" width="1116" height="216"/></clipPath>\n'
        '<circle cx="112" cy="128" r="12" fill="#f7f0df" stroke="#8a7340" stroke-width="2.5"/>'
        '<circle cx="1048" cy="128" r="12" fill="#f7f0df" stroke="#8a7340" stroke-width="2.5"/>\n'
        f"{body}"
        "</svg>"
    )


def thiruvalluvar_year(day: date) -> int:
    """Compute Thiruvalluvar Year (Thai 1 / Jan 15 boundary: +31 from Jan 15, +30 before)."""
    return day.year + 30 if (day.month == 1 and day.day < 15) else day.year + 31


def build_tamil_svg(kural: dict, tv_year: int) -> str:
    """Render the Tamil palm-leaf SVG for a single kural."""
    l1, l2 = kural["l1"], kural["l2"]
    size = tamil_font_size(l1, l2)
    header = f"திருக்குறள் {kural['n']}  ·  {kural['ch_ta']}"
    meta = f"{kural['sec_ta']}  ·  தினம் ஒரு குறள்  ·  திருவள்ளுவர் ஆண்டு {tv_year}"
    aria = f"திருக்குறள் {kural['n']} ({kural['ch_ta']}, திருவள்ளுவர் ஆண்டு {tv_year}): {l1} {l2}"
    font_ta = "'Noto Serif Tamil','Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',serif"
    font_ui = "'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN','Noto Sans',sans-serif"
    body = (
        f'<text x="580" y="64" font-family="{font_ui}" font-size="13.5" font-weight="600" '
        f'fill="#6b5226" text-anchor="middle">{escape(header)}</text>\n'
        f'<text x="580" y="114" font-family="{font_ta}" font-size="{size}" font-weight="bold" '
        f'fill="#4a3416" text-anchor="middle">{escape(l1)}</text>\n'
        f'<text x="580" y="156" font-family="{font_ta}" font-size="{size}" font-weight="bold" '
        f'fill="#4a3416" text-anchor="middle">{escape(l2)}</text>\n'
        f'<text x="580" y="198" font-family="{font_ui}" font-size="13" '
        f'fill="#6b5226" text-anchor="middle">{escape(meta)}</text>\n'
    )
    return render_shell(aria, body)


def build_english_svg(kural: dict, tv_year: int) -> str:
    """Render the English palm-leaf SVG for a single kural."""
    lines = split_couplet(kural["en"])
    line1 = lines[0]
    line2 = lines[1] if len(lines) > 1 else ""
    size = english_font_size(lines)
    header = f"Thirukkural {kural['n']}  ·  {kural['ch_en']}"
    meta = f"{kural['sec_en']}  ·  Daily Thirukkural  ·  Thiruvalluvar Year {tv_year}"
    aria = f"Thirukkural {kural['n']} ({kural['ch_en']}, Thiruvalluvar Year {tv_year}): {kural['en']}"
    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"
    font_ui = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"
    body = (
        f'<text x="580" y="64" font-family="{font_ui}" font-size="13.5" font-weight="600" '
        f'fill="#6b5226" text-anchor="middle">{escape(header)}</text>\n'
        f'<text x="580" y="114" font-family="{font_serif}" font-size="{size}" font-weight="bold" font-style="italic" '
        f'fill="#4a3416" text-anchor="middle">{escape(line1)}</text>\n'
        f'<text x="580" y="152" font-family="{font_serif}" font-size="{size}" font-weight="bold" font-style="italic" '
        f'fill="#4a3416" text-anchor="middle">{escape(line2)}</text>\n'
        f'<text x="580" y="198" font-family="{font_ui}" font-size="13" '
        f'fill="#6b5226" text-anchor="middle">{escape(meta)}</text>\n'
    )
    return render_shell(aria, body)


def build_toggle_pill(kural: dict, lang: str) -> str:
    """Render the handcrafted clickable summary pill button for the Olai explanation."""
    if lang == "ta":
        label = f"குறள் {kural['n']}  ·  பொருள் & விளக்கம் காண்க"
        font = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',sans-serif"
        size = "15"
        width = 430
    else:
        label = f"Kural {kural['n']}  ·  Read explanation"
        font = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"
        size = "16"
        width = 320

    cx = width / 2
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 42" width="{width}" height="42" '
        f'role="img" aria-label="{escape(label, quote=True)}">\n'
        "<defs>"
        '<filter id="wob2" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="2.2" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>"
        "</defs>\n"
        f'<rect x="2" y="2" width="{width - 4}" height="38" rx="19" fill="#f7f0df" stroke="#8a7340" '
        'stroke-width="2.2" filter="url(#wob2)"/>'
        f'<text x="{cx:.1f}" y="26.5" font-family="{font}" font-size="{size}" font-weight="bold" '
        f'fill="#4a3416" text-anchor="middle">{escape(label)}</text>\n'
        "</svg>"
    )


def render_meaning_card(
    *,
    aria_label: str,
    header_text: str,
    header_font: str,
    sections: list[tuple[str, str, list[str], str, float, bool]],
) -> str:
    """Render a parchment commentary card matching the notebook/postcard aesthetic."""
    y = 104
    blocks: list[str] = []
    for title, title_font, lines, body_font, body_size, body_italic in sections:
        blocks.append(
            f'<text x="96" y="{y}" font-family="{escape(title_font, quote=True)}" '
            f'font-size="14.5" font-weight="bold" fill="#2f6a42" text-anchor="start">{escape(title)}</text>'
        )
        y += 30
        style_attr = ' font-style="italic"' if body_italic else ""
        for line in lines:
            blocks.append(
                f'<text x="96" y="{y}" font-family="{escape(body_font, quote=True)}" '
                f'font-size="{body_size}"{style_attr} fill="#3a2d28" text-anchor="start">{escape(line)}</text>'
            )
            y += 29
        y += 14

    card_h = max(220, y + 12)
    svg_h = card_h + 24

    # Ruled paper background lines matching notebook.svg
    rule_ys = range(94, card_h - 8, 29)
    rules_svg = "".join(
        f'<line x1="28" y1="{ry}" x2="1132" y2="{ry}" stroke="#a9c3d8" stroke-opacity="0.55" stroke-width="1.3"/>'
        for ry in rule_ys
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 {svg_h}" width="1160" height="{svg_h}" '
        f'role="img" aria-label="{escape(aria_label, quote=True)}">\n'
        "<defs>"
        '<filter id="wob2" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="2.2" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>"
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.27  0 0 0 0 0.18  0.35 0 0 0 -0.09"/>'
        "</filter>"
        '<filter id="soft" x="-10%" y="-10%" width="120%" height="130%">'
        '<feGaussianBlur stdDeviation="5"/>'
        "</filter>"
        "</defs>\n"
        f'<rect x="16" y="16" width="1128" height="{card_h}" rx="12" fill="#000" opacity="0.11" filter="url(#soft)"/>\n'
        f'<rect x="12" y="10" width="1136" height="{card_h}" rx="12" fill="#fffaf0"/>'
        f'<rect x="12" y="10" width="1136" height="{card_h}" rx="12" filter="url(#grain)"/>\n'
        f"{rules_svg}\n"
        f'<line x1="74" y1="10" x2="74" y2="{10 + card_h}" stroke="#c4372c" stroke-opacity="0.48" stroke-width="2"/>\n'
        '<g transform="rotate(-2 580 12)" filter="url(#wob2)">'
        '<rect x="500" y="-4" width="160" height="30" fill="#dccb94" opacity="0.85"/>'
        "</g>\n"
        '<g transform="translate(1096 54)" filter="url(#wob2)">'
        '<path d="M0 -14 Q14 -14 14 0 Q14 14 0 14 Q-14 14 -14 0 Q-14 -14 0 -14Z" fill="none" stroke="#c4372c" stroke-width="2"/>'
        '<path d="M0 -7 L7 0 L0 7 L-7 0Z" fill="none" stroke="#e8a621" stroke-width="1.8"/>'
        '<circle cx="0" cy="0" r="2" fill="#e8a621"/>'
        "</g>\n"
        f'<text x="96" y="58" font-family="{escape(header_font, quote=True)}" '
        f'font-size="19" font-weight="bold" fill="#c4372c" text-anchor="start">{escape(header_text)}</text>\n'
        f'<path d="M96 68 q160 5 320 -2" fill="none" stroke="#e8a621" stroke-width="2.6" stroke-linecap="round" filter="url(#wob2)"/>\n'
        + "\n".join(blocks)
        + "\n</svg>"
    )


def build_tamil_meaning_svg(kural: dict) -> str:
    """Render the Tamil commentary card SVG."""
    font_ta = "'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN','Noto Sans',sans-serif"
    mv_lines = wrap_lines(kural["mv"], 76)
    sp_lines = wrap_lines(kural["sp"], 76)
    header = f"திருக்குறள் {kural['n']}  ·  {kural['ch_ta']}  ({kural['sec_ta']})"
    aria = f"{header}. மு. வரதராசனார்: {kural['mv']} சாலமன் பாப்பையா: {kural['sp']}"
    return render_meaning_card(
        aria_label=aria,
        header_text=header,
        header_font=font_ta,
        sections=[
            ("மு. வரதராசனார் விளக்கம்", font_ta, mv_lines, font_ta, 18.0, False),
            ("சாலமன் பாப்பையா விளக்கம்", font_ta, sp_lines, font_ta, 18.0, False),
        ],
    )


def build_english_meaning_svg(kural: dict) -> str:
    """Render the English explanation and transliteration card SVG."""
    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"
    font_ui = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"
    exp_lines = wrap_lines(kural["exp"], 76)
    tr_lines = [f"{kural['tr1']}  /", kural["tr2"]]
    header = f"Thirukkural {kural['n']}  ·  {kural['ch_en']}  ({kural['sec_en']})"
    aria = f"{header}. Meaning: {kural['exp']}"
    return render_meaning_card(
        aria_label=aria,
        header_text=header,
        header_font=font_serif,
        sections=[
            ("Meaning", font_ui, exp_lines, font_serif, 19.0, True),
            ("Transliteration", font_ui, tr_lines, font_serif, 17.0, True),
        ],
    )


def pick_kural(kurals: list[dict], kural_num: int | None, target_date: date | None) -> dict:
    """Pick a specific kural number or deterministically map a date across 1..1330."""
    if kural_num is not None:
        if not 1 <= kural_num <= len(kurals):
            raise ValueError(f"kural_num must be between 1 and {len(kurals)}")
        return kurals[kural_num - 1]
    day = target_date or datetime.now(IST).date()
    idx = (day.toordinal() - EPOCH.toordinal()) % len(kurals)
    return kurals[idx]


def main() -> None:
    parser = argparse.ArgumentParser(description="Update daily Thirukkural Olai SVGs, button pills, and meaning cards.")
    parser.add_argument("--kural", type=int, default=None, help="Explicit kural number (1-1330)")
    parser.add_argument("--date", type=date.fromisoformat, default=None, help="ISO date (YYYY-MM-DD)")
    args = parser.parse_args()

    day = args.date or datetime.now(IST).date()
    tv_year = thiruvalluvar_year(day)
    kurals = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    kural = pick_kural(kurals, args.kural, day)

    TA_OLAI.write_text(build_tamil_svg(kural, tv_year), encoding="utf-8")
    EN_OLAI.write_text(build_english_svg(kural, tv_year), encoding="utf-8")
    TA_BTN.write_text(build_toggle_pill(kural, "ta"), encoding="utf-8")
    EN_BTN.write_text(build_toggle_pill(kural, "en"), encoding="utf-8")
    TA_MEANING.write_text(build_tamil_meaning_svg(kural), encoding="utf-8")
    EN_MEANING.write_text(build_english_meaning_svg(kural), encoding="utf-8")
    print(f"Updated Olai SVGs & meaning cards to Thirukkural #{kural['n']} (TV {tv_year})")


if __name__ == "__main__":
    main()
