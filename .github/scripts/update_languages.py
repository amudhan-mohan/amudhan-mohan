"""Generate interactive Code Shelf & Archive File Folder language SVGs."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import re
import textwrap
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
USERNAME = "amudhan-mohan"
TA_README = ROOT / "README.md"
EN_README = ROOT / "README.en.md"

START_MARKER = "<!-- LANGUAGES:START -->"
END_MARKER = "<!-- LANGUAGES:END -->"

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_TA = ["ஜன", "பிப்", "மார்", "ஏப்", "மே", "ஜூன்", "ஜூலை", "ஆக", "செப்", "அக்", "நவ", "டிச"]

LANG_COLORS = {
    "JavaScript": "#e8a621",
    "TypeScript": "#3b82c4",
    "Python": "#2d3b6b",
    "HTML": "#c4372c",
    "CSS": "#5b7c99",
    "PHP": "#4b3a52",
    "C": "#5b4636",
    "C++": "#6b5226",
    "Svelte": "#b5653a",
    "EJS": "#2f6a42",
    "Java": "#9c522d",
    "Shell": "#3f7d4e",
}
FALLBACK_PALETTE = ["#2f6a42", "#c4372c", "#2d3b6b", "#b97a00", "#4b3a52", "#5b4636"]

LANG_MONOGRAMS = {
    "JavaScript": "JS",
    "TypeScript": "TS",
    "Python": "PY",
    "HTML": "</>",
    "CSS": "#",
    "PHP": "PHP",
    "C": "C",
    "C++": "C++",
    "C#": "C#",
    "Svelte": "SV",
    "EJS": "<%",
    "Java": "JV",
    "Shell": "$_",
}


def fetch_repos(username: str) -> list[dict]:
    """Fetch public non-fork repositories sorted by most recently pushed."""
    headers = {"User-Agent": "amudhan-mohan-profile-updater", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_METRICS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=100"
    last_exc: Exception | None = None
    data = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))
            break
        except Exception as exc:
            last_exc = exc
    if data is None:
        raise last_exc or RuntimeError("Failed to fetch GitHub repos.")
    if not isinstance(data, list):
        raise RuntimeError("Unexpected GitHub API response for repos.")
    return [r for r in data if not r.get("fork") and r.get("language")]


def slugify_lang(lang_name: str) -> str:
    """Return a clean filesystem slug for a programming language name."""
    slug = re.sub(r"[^a-z0-9]+", "-", lang_name.lower().replace("+", "p").replace("#", "sharp")).strip("-")
    return slug or "code"


def lang_color(lang_name: str, idx: int) -> str:
    return LANG_COLORS.get(lang_name, FALLBACK_PALETTE[idx % len(FALLBACK_PALETTE)])


def lang_monogram(lang_name: str) -> str:
    return LANG_MONOGRAMS.get(lang_name, lang_name[:3].upper())


def contrast_ink(hex_color: str) -> str:
    """Pick dark espresso ink for bright fills and cream ink for dark fills using WCAG luminance."""
    h = hex_color.lstrip("#")
    channels = []
    for i in (0, 2, 4):
        c = int(h[i : i + 2], 16) / 255.0
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    lum = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
    return "#3a2d28" if lum > 0.28 else "#fffaf0"


def format_month_year(iso_ts: str, lang: str) -> str:
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    months = MONTHS_TA if lang == "ta" else MONTHS_EN
    return f"{months[dt.month - 1]} ’{dt.strftime('%y')}"


def estimate_text_px(text: str, font_size: float) -> float:
    """Estimate rendered text advance width across Latin and Tamil scripts."""
    scale = font_size / 14.0
    total = 0.0
    for ch in text:
        if "\u0bbe" <= ch <= "\u0bcd" or ch in "\u0b82\u0bd7":
            total += 2.2 * scale
        elif ch in " iIljtfr.,·:;|'!":
            total += 4.3 * scale
        elif ch in "mwMWABCDEFGHIJKLMNOPQRSTUVWXYZ":
            total += 11.2 * scale
        elif "\u0b80" <= ch <= "\u0bff":
            total += 9.6 * scale
        else:
            total += 7.8 * scale
    return total


def wrap_two_lines(text: str, width: int) -> list[str]:
    """Wrap description cleanly across at most two lines with whole-word ellipsis on overflow."""
    words = text.split()
    if not words:
        return []
    lines = textwrap.wrap(" ".join(words), width=width)
    if len(lines) <= 2:
        return lines
    second = lines[1]
    if len(second) > max(4, width - 2):
        trimmed = second[: width - 2].rsplit(" ", 1)[0].rstrip(",;:- ")
        second = trimmed or second[: width - 2].rstrip()
    return [lines[0], f"{second}…"]


def render_overview_svg(groups: list[tuple[str, list[dict]]], lang: str) -> str:
    """Render the handmade 'Code Shelf' bookshelf overview SVG (848px wide)."""
    total_repos = sum(len(items) for _, items in groups)
    max_count = max(len(items) for _, items in groups)
    font_ui = (
        "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',sans-serif"
        if lang == "ta"
        else "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"
    )
    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"

    if lang == "ta":
        title = f"நிரலாக்க அலமாரி  ·  {total_repos} திட்டங்கள்"
        hint = f"{len(groups)} மொழிகள் · கீழே கோப்பைத் திறக்கவும் ▾"
    else:
        title = f"The Code Shelf  ·  {total_repos} repositories"
        hint = f"{len(groups)} languages · open a folder below ▾"

    svg_w = 848
    shelf_y = 224.0
    start_x = 42.0
    max_span = 620.0
    gap = 7.0

    raw_weights = [len(items) ** 0.55 for _, items in groups]
    usable = max(180.0, max_span - gap * max(0, len(groups) - 1))
    scale_w = usable / max(0.1, sum(raw_weights))
    widths = [max(44.0, min(124.0, w * scale_w)) for w in raw_weights]
    # Guarantee total spine width fits cleanly left of the bookend even with many languages
    cur_total = sum(widths)
    if cur_total > usable:
        shrink = usable / cur_total
        widths = [w * shrink for w in widths]

    books_svg: list[str] = []
    cur_x = start_x
    for idx, (name, items) in enumerate(groups):
        color = lang_color(name, idx)
        ink = contrast_ink(color)
        bw = widths[idx]
        bh = 114.0 + round(44.0 * (len(items) / max_count))
        bx = cur_x
        by = shelf_y - bh
        pct = round(100 * len(items) / total_repos)
        cx = bx + bw / 2.0

        # Tiny woven ribbon bookmark hanging below the shelf edge on top two volumes
        ribbon = ""
        if idx < 2:
            rx = cx - 4.0
            ribbon_c = "#c4372c" if idx == 0 else "#e8a621"
            ribbon = (
                f'<path d="M{rx:.1f} {shelf_y - 2:.1f} L{rx:.1f} {shelf_y + 18:.1f} '
                f'L{rx + 4:.1f} {shelf_y + 13:.1f} L{rx + 8:.1f} {shelf_y + 18:.1f} L{rx + 8:.1f} {shelf_y - 2:.1f} Z" '
                f'fill="{ribbon_c}" filter="url(#wob2)"/>'
            )

        label_h = bh - 50.0
        label_y = by + 25.0
        label_w = max(24.0, bw - 14.0)
        label_x = bx + (bw - label_w) / 2.0
        label_cy = label_y + label_h / 2.0

        spine_title = name if len(name) <= 11 else f"{name[:10]}."
        title_size = 13.0 if bw >= 52 else 11.5

        books_svg.append(
            f'<g>'
            f'<rect x="{bx + 3:.1f}" y="{by + 4:.1f}" width="{bw:.1f}" height="{bh - 2:.1f}" rx="4" fill="#000" opacity="0.10"/>'
            f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{color}" filter="url(#wob2)"/>'
            f'<rect x="{bx + 2:.1f}" y="{by + 2:.1f}" width="5" height="{bh - 4:.1f}" rx="2" fill="#ffffff" opacity="0.18"/>'
            f'<rect x="{bx + 5:.1f}" y="{by + 7:.1f}" width="{bw - 10:.1f}" height="3" rx="1.5" fill="#fffaf0" opacity="0.45"/>'
            f'<rect x="{bx + 5:.1f}" y="{by + bh - 10:.1f}" width="{bw - 10:.1f}" height="3" rx="1.5" fill="#fffaf0" opacity="0.45"/>'
            f'<text x="{cx:.1f}" y="{by + 20:.1f}" font-family="{font_ui}" font-size="10.5" font-weight="bold" fill="{ink}" text-anchor="middle">{pct}%</text>'
            f'<rect x="{label_x:.1f}" y="{label_y:.1f}" width="{label_w:.1f}" height="{label_h:.1f}" rx="3.5" fill="#fffaf0" stroke="#dccb94" stroke-width="1"/>'
            f'<text x="{cx:.1f}" y="{label_cy + 4:.1f}" font-family="{font_serif}" font-size="{title_size}" font-weight="bold" fill="#3a2d28" text-anchor="middle" transform="rotate(-90 {cx:.1f} {label_cy:.1f})">{escape(spine_title)}</text>'
            f'<text x="{cx:.1f}" y="{by + bh - 14:.1f}" font-family="{font_ui}" font-size="11" font-weight="bold" fill="{ink}" text-anchor="middle">{len(items)}</text>'
            f"{ribbon}"
            "</g>"
        )
        cur_x += bw + gap

    # Desk bookend scene on the right of the shelf: potted plant + inkwell + dip pen
    pot_x = 716.0
    bookend_svg = (
        f'<g filter="url(#wob2)">'
        # Leafy sprig inside terracotta pot
        f'<path d="M{pot_x + 18} 190 Q{pot_x + 2} 166 {pot_x - 6} 152 Q{pot_x + 14} 156 {pot_x + 20} 188 Z" fill="#2f6a42"/>'
        f'<path d="M{pot_x + 21} 190 Q{pot_x + 22} 154 {pot_x + 24} 138 Q{pot_x + 34} 158 {pot_x + 24} 190 Z" fill="#3f7d4e"/>'
        f'<path d="M{pot_x + 24} 190 Q{pot_x + 40} 164 {pot_x + 50} 154 Q{pot_x + 38} 178 {pot_x + 24} 190 Z" fill="#2f6a42"/>'
        # Terracotta pot
        f'<polygon points="{pot_x + 2},192 {pot_x + 40},192 {pot_x + 35},224 {pot_x + 7},224" fill="#c4372c"/>'
        f'<rect x="{pot_x}" y="186" width="42" height="7" rx="3" fill="#b5653a"/>'
        # Slanted brass pen inside indigo inkwell
        f'<line x1="782" y1="198" x2="799" y2="160" stroke="#b97a00" stroke-width="3" stroke-linecap="round"/>'
        f'<polygon points="798,158 803,152 801,163" fill="#3a2d28"/>'
        f'<rect x="768" y="198" width="26" height="26" rx="5" fill="#2d3b6b"/>'
        f'<rect x="774" y="192" width="14" height="7" rx="2" fill="#5b4636"/>'
        f'<rect x="773" y="206" width="16" height="10" rx="2" fill="#fffaf0" opacity="0.9"/>'
        "</g>"
    )

    # Bottom summary plaque lines
    legend_rows: list[str] = []
    leg_x = 42.0
    leg_y = 276.0
    for idx, (name, items) in enumerate(groups):
        color = lang_color(name, idx)
        lbl = f"{name} ({len(items)})"
        item_w = 18.0 + estimate_text_px(lbl, 12.0)
        if leg_x > 42.0 and leg_x + item_w > 810.0:
            leg_x = 42.0
            leg_y += 22.0
        legend_rows.append(
            f'<circle cx="{leg_x + 5:.1f}" cy="{leg_y - 4:.1f}" r="4.8" fill="{color}"/>'
            f'<text x="{leg_x + 14:.1f}" y="{leg_y:.1f}" font-family="{font_ui}" font-size="12" font-weight="600" fill="#3a2d28" text-anchor="start">{escape(lbl)}</text>'
        )
        leg_x += item_w + 18.0

    svg_h = int(leg_y + 22)
    aria = f"{title}. " + ", ".join(f"{name} ({len(items)})" for name, items in groups)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="{svg_w}" height="{svg_h}" '
        f'role="img" aria-label="{escape(aria, quote=True)}">\n'
        "<defs>"
        '<filter id="wob2" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="1.6" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>"
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.27  0 0 0 0 0.18  0.35 0 0 0 -0.09"/>'
        "</filter>"
        "</defs>\n"
        f'<rect width="{svg_w}" height="{svg_h}" rx="16" fill="#f7f0df"/>'
        f'<rect width="{svg_w}" height="{svg_h}" rx="16" filter="url(#grain)"/>'
        f'<rect x="1.5" y="1.5" width="{svg_w - 3}" height="{svg_h - 3}" rx="15" fill="none" stroke="#dccb94" stroke-width="2" filter="url(#wob2)"/>\n'
        f'<text x="32" y="36" font-family="{font_serif if lang == "en" else font_ui}" font-size="{"18" if lang == "en" else "16"}" font-weight="bold" fill="#3a2d28" text-anchor="start">{escape(title)}</text>\n'
        f'<text x="816" y="36" font-family="{font_ui}" font-size="{"11.5" if lang == "en" else "10.5"}" fill="#7a6a5c" text-anchor="end">{escape(hint)}</text>\n'
        + "".join(books_svg)
        + "\n"
        + bookend_svg
        + "\n"
        # Wooden shelf board + corbels
        f'<polygon points="48,242 66,242 48,256" fill="#8d6435"/>'
        f'<polygon points="800,242 782,242 800,256" fill="#8d6435"/>'
        f'<rect x="26" y="{shelf_y:.0f}" width="796" height="14" rx="4" fill="#c99c62" filter="url(#wob2)"/>'
        f'<rect x="26" y="{shelf_y + 13:.0f}" width="796" height="5" rx="2" fill="#8d6435"/>'
        f'<line x1="60" y1="{shelf_y + 6:.0f}" x2="360" y2="{shelf_y + 6:.0f}" stroke="#a57a45" stroke-width="1.2" opacity="0.6"/>'
        f'<line x1="420" y1="{shelf_y + 8:.0f}" x2="770" y2="{shelf_y + 8:.0f}" stroke="#a57a45" stroke-width="1.2" opacity="0.6"/>\n'
        + "".join(legend_rows)
        + "\n</svg>"
    )


def render_lang_folder_tab_svg(
    name: str, items: list[dict], color: str, total_repos: int, lang: str
) -> str:
    """Render a full-width notched archival file folder tab SVG (780x70)."""
    count = len(items)
    pct = round(100 * count / total_repos)
    mono = lang_monogram(name)

    if lang == "ta":
        unit = "திட்டம்" if count == 1 else "திட்டங்கள்"
        count_lbl = f"{count} {unit} ▾"
        font_ui = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',sans-serif"
    else:
        unit = "repo" if count == 1 else "repos"
        count_lbl = f"{count} {unit} ▾"
        font_ui = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"
    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"

    names = [r["name"] for r in items]
    teaser = "  ·  ".join(names[:3])
    if len(names) > 3:
        teaser = f"{teaser}  (+{len(names) - 3})"
    if len(teaser) > 54:
        teaser = textwrap.shorten(teaser, width=54, placeholder="…")

    title_px = estimate_text_px(name, 17.5)
    pct_x = 84.0 + title_px + 14.0
    bar_w = max(8.0, round(108.0 * (count / total_repos), 1))
    mono_size = 13.0 if len(mono) <= 2 else 11.0

    aria = f"{name}: {count} {unit} ({pct}%)"
    folder_path = (
        "M 6,64 L 6,12 Q 6,4 14,4 L 222,4 Q 234,4 240,14 L 766,14 "
        "Q 774,14 774,22 L 774,64 Q 774,66 772,66 L 8,66 Q 6,66 6,64 Z"
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 780 70" width="780" height="70" '
        f'role="img" aria-label="{escape(aria, quote=True)}">\n'
        "<defs>"
        '<filter id="wob2" x="-2%" y="-6%" width="104%" height="112%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="1.4" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>"
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.27  0 0 0 0 0.18  0.35 0 0 0 -0.09"/>'
        "</filter>"
        f'<clipPath id="tabclip"><path d="{folder_path}"/></clipPath>'
        "</defs>\n"
        f'<path d="{folder_path}" fill="#fffaf0" stroke="#dccb94" stroke-width="1.8" filter="url(#wob2)"/>'
        f'<path d="{folder_path}" filter="url(#grain)"/>\n'
        f'<g clip-path="url(#tabclip)"><rect x="6" y="4" width="12" height="62" fill="{color}"/></g>\n'
        f'<rect x="30" y="19" width="38" height="38" rx="8" fill="{color}" fill-opacity="0.14" stroke="{color}" stroke-width="1.6" filter="url(#wob2)"/>'
        f'<text x="49" y="42.5" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="{mono_size}" font-weight="bold" fill="#3a2d28" text-anchor="middle">{escape(mono)}</text>\n'
        f'<text x="84" y="34" font-family="{font_serif if lang == "en" else font_ui}" font-size="17.5" font-weight="bold" fill="#3a2d28" text-anchor="start">{escape(name)}</text>'
        f'<text x="{pct_x:.1f}" y="33.5" font-family="{font_ui}" font-size="11.5" font-weight="600" fill="#7a6a5c" text-anchor="start">{pct}%</text>\n'
        f'<text x="84" y="54" font-family="{font_ui}" font-size="12" fill="#6d5d50" text-anchor="start">{escape(teaser)}</text>\n'
        f'<rect x="506" y="34" width="108" height="8" rx="4" fill="#efe3c8"/>'
        f'<rect x="506" y="34" width="{bar_w}" height="8" rx="4" fill="{color}"/>\n'
        f'<rect x="634" y="21" width="124" height="34" rx="8" fill="#f7f0df" stroke="{color}" stroke-width="1.6" filter="url(#wob2)"/>'
        f'<text x="696" y="42.5" font-family="{font_ui}" font-size="12.5" font-weight="bold" fill="#3a2d28" text-anchor="middle">{escape(count_lbl)}</text>\n'
        "</svg>"
    )


def repo_card_filename(lang_slug: str, idx_r: int, repo_name: str) -> str:
    """Return a clean, collision-free SVG filename for a clickable repository card."""
    rslug = re.sub(r"[^a-z0-9]+", "-", repo_name.lower()).strip("-") or "repo"
    return f"lang-{lang_slug}-repo-{idx_r + 1}-{rslug}.svg"


def render_repo_card_svg(r: dict, lang_name: str, color: str, tilt: float, lang: str) -> str:
    """Render a standalone clickable cream index card (560x236) displaying the repo URL."""
    font_ui = (
        "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',sans-serif"
        if lang == "ta"
        else "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"
    )
    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"

    rname = r["name"]
    fallback_desc = "பொது GitHub திட்டம்" if lang == "ta" else "Public GitHub repository"
    raw_desc = " ".join((r.get("description") or "").split()) or fallback_desc
    desc_lines = wrap_two_lines(raw_desc, 50)

    title_size = 21.5 if len(rname) <= 28 else (18.5 if len(rname) <= 36 else 16.0)
    disp_name = rname if len(rname) <= 44 else f"{rname[:42]}…"

    stars = int(r.get("stargazers_count", 0))
    when = format_month_year(r["pushed_at"], lang)
    meta_right = (f"★ {stars}  ·  {when}") if stars > 0 else when

    repo_url_display = f"github.com/{USERNAME}/{rname}"
    url_size = 12.5 if len(repo_url_display) <= 46 else 11.0
    if len(repo_url_display) > 58:
        repo_url_display = f"{repo_url_display[:56]}…"

    open_cta = "திறக்க ↗" if lang == "ta" else "Open ↗"
    badge_w = max(56, int(round(estimate_text_px(lang_name, 12.0) + 32)))
    aria = f"{rname} ({lang_name}) — https://github.com/{USERNAME}/{rname}"
    if lang == "ta":
        aria = f"{rname} ({lang_name}) GitHub திட்டம் — https://github.com/{USERNAME}/{rname}"

    desc_svg = "".join(
        f'<text x="40" y="{126 + i * 23}" font-family="{font_ui}" font-size="14.5" fill="#4a3b31" text-anchor="start">{escape(line)}</text>'
        for i, line in enumerate(desc_lines)
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 236" width="560" height="236" '
        f'role="img" aria-label="{escape(aria, quote=True)}">\n'
        "<defs>"
        '<filter id="wob2" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="1.8" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>"
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.27  0 0 0 0 0.18  0.35 0 0 0 -0.09"/>'
        "</filter>"
        '<filter id="soft" x="-10%" y="-10%" width="120%" height="130%">'
        '<feGaussianBlur stdDeviation="4.5"/>'
        "</filter>"
        "</defs>\n"
        f'<g transform="rotate({tilt} 280 118)">\n'
        '  <rect x="22" y="25" width="520" height="196" rx="10" fill="#000" opacity="0.12" filter="url(#soft)"/>\n'
        '  <rect x="18" y="18" width="524" height="198" rx="10" fill="#fffaf0" stroke="#dccb94" stroke-width="1.5" filter="url(#wob2)"/>\n'
        '  <rect x="18" y="18" width="524" height="198" rx="10" filter="url(#grain)"/>\n'
        f'  <g transform="rotate(-1.5 280 16)" filter="url(#wob2)"><rect x="224" y="6" width="112" height="22" rx="2" fill="{color}" opacity="0.58"/></g>\n'
        f'  <rect x="40" y="38" width="{badge_w}" height="24" rx="12" fill="{color}" fill-opacity="0.14" stroke="{color}" stroke-width="1.4"/>\n'
        f'  <circle cx="54" cy="50" r="4.5" fill="{color}"/>\n'
        f'  <text x="64" y="54" font-family="{font_ui}" font-size="12" font-weight="600" fill="#3a2d28" text-anchor="start">{escape(lang_name)}</text>\n'
        f'  <text x="520" y="54" font-family="{font_ui}" font-size="13" font-weight="600" fill="#7a6a5c" text-anchor="end">{escape(meta_right)}</text>\n'
        f'  <text x="40" y="92" font-family="{font_serif}" font-size="{title_size}" font-weight="bold" fill="#2d3b6b" text-anchor="start">{escape(disp_name)}</text>\n'
        f'  {desc_svg}\n'
        '  <line x1="38" y1="173" x2="522" y2="173" stroke="#dccb94" stroke-width="1.2" stroke-dasharray="4 4"/>\n'
        f'  <text x="40" y="198" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="{url_size}" font-weight="600" fill="#2d3b6b" text-anchor="start">{escape(repo_url_display)}</text>\n'
        f'  <text x="520" y="198" font-family="{font_ui}" font-size="12.5" font-weight="bold" fill="#3a2d28" text-anchor="end">{escape(open_cta)}</text>\n'
        "</g>\n"
        "</svg>"
    )


def build_readme_block(groups: list[tuple[str, list[dict]]], lang: str) -> str:
    """Build the interactive <details> showcase block with directly clickable repo cards."""
    lines = [
        START_MARKER,
        '<div align="center">',
        f'  <img src="assets/{lang}/languages.svg" alt="{"நிரலாக்க அலமாரி" if lang == "ta" else "The Code Shelf"}" width="100%">',
        "</div>",
        "",
    ]

    for name, items in groups:
        slug = slugify_lang(name)
        alt_tab = f"{name} ({len(items)})"
        if lang == "en":
            open_lbl = "Repository URL:" if len(items) == 1 else "Repository URLs:"
            live_lbl = "Live"
        else:
            open_lbl = "திட்ட இணைப்பு:" if len(items) == 1 else "திட்ட இணைப்புகள்:"
            live_lbl = "நேரலை"

        card_links: list[str] = []
        text_links: list[str] = []
        for idx_r, r in enumerate(items):
            fname = repo_card_filename(slug, idx_r, r["name"])
            rurl = r["html_url"]
            card_links.append(
                f'    <a href="{escape(rurl, quote=True)}"><img src="assets/{lang}/{fname}" alt="{escape(r["name"], quote=True)} ({escape(rurl, quote=True)})" width="400"></a>'
            )
            link_item = f'<a href="{escape(rurl, quote=True)}">{escape(r["name"])}</a>'
            homepage = (r.get("homepage") or "").strip()
            if homepage.startswith(("http://", "https://")):
                link_item += f' (<a href="{escape(homepage, quote=True)}">{live_lbl} ↗</a>)'
            text_links.append(link_item)

        lines.extend(
            [
                "<details>",
                f'  <summary><img src="assets/{lang}/lang-{slug}.svg" alt="{escape(alt_tab, quote=True)}" width="94%" align="absmiddle"></summary>',
                "  <br>",
                '  <div align="center">',
                *card_links,
                "  </div>",
                f'  <p align="center"><strong>{open_lbl}</strong> {" &nbsp;&middot;&nbsp; ".join(text_links)}</p>',
                "</details>",
                "",
            ]
        )

    lines.append(END_MARKER)
    return "\n".join(lines)


def replace_marker_block(path: Path, new_block: str) -> None:
    content = path.read_text(encoding="utf-8")
    pattern = re.compile(f"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}", re.DOTALL)
    if not pattern.search(content):
        raise RuntimeError(f"Missing {START_MARKER}..{END_MARKER} in {path}")
    path.write_text(pattern.sub(lambda _: new_block, content, count=1), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update Code Shelf and expandable clickable repo cards.")
    parser.add_argument("--offline", action="store_true", help="Skip GitHub fetch if offline")
    args = parser.parse_args()

    if args.offline:
        print("Offline mode: skipping languages update.")
        return

    try:
        repos = fetch_repos(USERNAME)
    except Exception as exc:
        print(f"Warning: could not fetch GitHub repos ({exc}); keeping existing language cards.")
        return

    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in repos:
        grouped[r["language"]].append(r)

    groups = sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0].lower()))
    total_repos = len(repos)
    tilts = [-0.7, 0.65, 0.55, -0.6]

    for lang in ("en", "ta"):
        asset_dir = ROOT / "assets" / lang
        for old in asset_dir.glob("lang-*.svg"):
            old.unlink()

        (asset_dir / "languages.svg").write_text(render_overview_svg(groups, lang), encoding="utf-8")

        for idx, (name, items) in enumerate(groups):
            slug = slugify_lang(name)
            color = lang_color(name, idx)
            (asset_dir / f"lang-{slug}.svg").write_text(
                render_lang_folder_tab_svg(name, items, color, total_repos, lang), encoding="utf-8"
            )
            for idx_r, r in enumerate(items):
                fname = repo_card_filename(slug, idx_r, r["name"])
                (asset_dir / fname).write_text(
                    render_repo_card_svg(r, name, color, tilts[idx_r % len(tilts)], lang), encoding="utf-8"
                )

        readme_path = TA_README if lang == "ta" else EN_README
        replace_marker_block(readme_path, build_readme_block(groups, lang))

    print(f"Updated Code Shelf & clickable repo cards ({len(groups)} languages, {len(repos)} repos).")


if __name__ == "__main__":
    main()
