"""Update live GitHub repo metrics on project sticky notes and pulse strip SVGs."""

from __future__ import annotations

import argparse
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
USERNAME = "amudhan-mohan"

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_TA = ["ஜன", "பிப்", "மார்", "ஏப்", "மே", "ஜூன்", "ஜூலை", "ஆக", "செப்", "அக்", "நவ", "டிச"]

SHARED_DEFS = (
    "<defs>"
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
)


def fetch_json(url: str) -> object:
    headers = {"User-Agent": "amudhan-mohan-profile-updater", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def check_url_live(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "amudhan-mohan-profile-updater"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


def format_month_year(iso_ts: str, lang: str) -> str:
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    months = MONTHS_TA if lang == "ta" else MONTHS_EN
    return f"{months[dt.month - 1]} ’{dt.strftime('%y')}"


def format_month_day(iso_ts: str, lang: str) -> str:
    dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    months = MONTHS_TA if lang == "ta" else MONTHS_EN
    return f"{months[dt.month - 1]} {dt.day}"


def note_stamp(repo: dict | None, lang: str, accent: str) -> tuple[str, str]:
    """Return (label, color) for the bottom-right sticky note badge."""
    if not repo:
        return "", accent
    stars = int(repo.get("stargazers_count", 0))
    if stars > 0:
        return f"★ {stars}", accent
    pushed = repo.get("pushed_at", "")
    if pushed:
        return format_month_year(pushed, lang), "#7a6a5c"
    return "", accent


def render_note_svg(
    *,
    aria_label: str,
    rotate: str,
    accent: str,
    title: str,
    title_font: str,
    title_size: int,
    pills: list[tuple[int, int, str]],
    desc_lines: list[str],
    desc_font: str,
    desc_size: float,
    desc_italic: bool,
    url_text: str,
    badge_text: str,
    badge_color: str,
    badge_font: str,
    doodle: str,
) -> str:
    pills_svg = "".join(
        f'<rect x="{x}" y="104" width="{w}" height="26" rx="13" fill="none" stroke="{accent}" '
        f'stroke-width="2" filter="url(#wob2)"/>'
        f'<text x="{x + w / 2:.1f}" y="121" font-family="{escape(badge_font, quote=True)}" '
        f'font-size="12.5" fill="{accent}" text-anchor="middle">{escape(label)}</text>'
        for x, w, label in pills
    )
    style_attr = ' font-style="italic"' if desc_italic else ""
    desc_svg = "".join(
        f'<text x="50" y="{168 + i * 25}" font-family="{escape(desc_font, quote=True)}" '
        f'font-size="{desc_size}"{style_attr} fill="#3a2d28" text-anchor="start">{escape(line)}</text>'
        for i, line in enumerate(desc_lines)
    )
    badge_svg = (
        f'<text x="550" y="234" font-family="{escape(badge_font, quote=True)}" '
        f'font-size="12.5" font-weight="600" fill="{badge_color}" text-anchor="end">{escape(badge_text)}</text>'
        if badge_text
        else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 286" width="600" height="286" '
        f'role="img" aria-label="{escape(aria_label, quote=True)}">\n'
        f"{SHARED_DEFS}"
        f'<g transform="rotate({rotate} 300 143)">\n'
        '<rect x="34" y="44" width="540" height="216" rx="6" fill="#000" opacity="0.14" filter="url(#soft)"/>\n'
        '<rect x="26" y="30" width="548" height="222" rx="6" fill="#fffaf0" filter="url(#wob2)"/>\n'
        '<rect x="26" y="30" width="548" height="222" rx="6" filter="url(#grain)"/>\n'
        f'<g transform="rotate(-3 300 32)" filter="url(#wob2)"><rect x="236" y="14" width="124" height="32" fill="{accent}" opacity="0.55"/></g>\n'
        f'<text x="50" y="82" font-family="{escape(title_font, quote=True)}" font-size="{title_size}" font-weight="bold" fill="#3a2d28" text-anchor="start">{escape(title)}</text>\n'
        f"{pills_svg}"
        f"{desc_svg}\n"
        '<text x="50" y="234" font-family="\'Segoe UI\',\'Helvetica Neue\',Helvetica,Arial,\'Noto Sans\',sans-serif" '
        f'font-size="12.5" fill="#7a6a5c" text-anchor="start">{escape(url_text)}</text>\n'
        f"{badge_svg}\n"
        f"{doodle}\n"
        "</g>\n</svg>"
    )


def render_pulse_svg(repos: list[dict], lang: str, open_year: int | None) -> str:
    """Render the compact recent GitHub activity strip matching the parchment theme."""
    active = [r for r in repos if not r.get("fork") and r.get("name", "").lower() != USERNAME.lower()]
    top = active[:2]
    total_repos = len([r for r in repos if not r.get("fork")])

    font_ui = (
        "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',sans-serif"
        if lang == "ta"
        else "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"
    )
    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"

    chunks = []
    for r in top:
        name = r["name"][:26]
        lang_tag = r.get("language") or "Code"
        when = format_month_day(r["pushed_at"], lang)
        chunks.append(f"{name} ({lang_tag} · {when})")

    if lang == "ta":
        prefix = "சமீபத்திய GitHub செயல்பாடு:"
        right_label = f"{total_repos} பொதுத் திட்டங்கள்" + (f" · {open_year} முதல்" if open_year else "")
        detail = "  ·  ".join(chunks) if chunks else "செயலில் உள்ளது"
        aria = f"{prefix} {detail}. {right_label}."
    else:
        prefix = "Recent GitHub activity:"
        right_label = f"{total_repos} public repos" + (f" · since {open_year}" if open_year else "")
        detail = "  ·  ".join(chunks) if chunks else "Active on GitHub"
        aria = f"{prefix} {detail}. {right_label}."

    italic_attr = 'font-style="italic" ' if lang == "en" else ""
    detail_font = font_serif if lang == "en" else font_ui
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 80" width="1160" height="80" '
        f'role="img" aria-label="{escape(aria, quote=True)}">\n'
        "<defs>"
        '<filter id="wob2" x="-4%" y="-4%" width="108%" height="108%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.06" numOctaves="2" seed="11" result="n"/>'
        '<feDisplacementMap in="SourceGraphic" in2="n" scale="2.0" xChannelSelector="R" yChannelSelector="G"/>'
        "</filter>"
        '<filter id="grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="8"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.27  0 0 0 0 0.18  0.35 0 0 0 -0.09"/>'
        "</filter>"
        "</defs>\n"
        '<rect width="1160" height="80" rx="14" fill="#f7f0df"/>'
        '<rect width="1160" height="80" rx="14" filter="url(#grain)"/>'
        '<rect x="1.5" y="1.5" width="1157" height="77" rx="13" fill="none" stroke="#dccb94" stroke-width="2" filter="url(#wob2)"/>\n'
        '<circle cx="38" cy="40" r="6" fill="#2f6a42" filter="url(#wob2)">'
        '<animate attributeName="opacity" values="1;0.45;1" dur="3.2s" repeatCount="indefinite"/>'
        "</circle>\n"
        f'<text x="58" y="45" font-family="{font_ui}" font-size="14.5" text-anchor="start">'
        f'<tspan font-weight="bold" fill="#3a2d28">{escape(prefix)}</tspan>'
        f'<tspan dx="12" font-family="{detail_font}" {italic_attr}fill="#2f6a42">{escape(detail)}</tspan>'
        "</text>\n"
        f'<text x="1124" y="45" font-family="{font_ui}" font-size="13.5" font-weight="600" fill="#7a6a5c" text-anchor="end">{escape(right_label)}</text>\n'
        "</svg>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Update sticky note metrics and pulse strip SVGs.")
    parser.add_argument("--offline", action="store_true", help="Skip network calls and keep existing files if present")
    args = parser.parse_args()

    repos: list[dict] = []
    open_year: int | None = None
    renderping_live = False

    if not args.offline:
        try:
            user = fetch_json(f"https://api.github.com/users/{USERNAME}")
            if isinstance(user, dict) and user.get("created_at"):
                open_year = int(user["created_at"][:4])
        except Exception as exc:
            print(f"Warning: GitHub user fetch failed ({exc}).")
        try:
            data = fetch_json(f"https://api.github.com/users/{USERNAME}/repos?sort=pushed&per_page=100")
            if isinstance(data, list):
                repos = data
        except Exception as exc:
            print(f"Warning: GitHub API fetch failed ({exc}); keeping fallback state.")
        renderping_live = check_url_live("https://renderping.amudhanmohan.in/")

    if not repos:
        if (ROOT / "assets" / "en" / "pulse.svg").exists() and (ROOT / "assets" / "ta" / "pulse.svg").exists():
            print("No GitHub repo data available; keeping existing note and pulse SVGs.")
            return

    by_name = {r["name"].lower(): r for r in repos if isinstance(r, dict) and "name" in r}

    serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"
    sans_en = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"
    sans_ta = "'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN','Noto Sans',sans-serif"
    mixed_ta = "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',sans-serif"

    doodle_au = '<g transform="translate(488 52)" fill="none" stroke="#2f6a42" stroke-width="3" stroke-linecap="round" filter="url(#wob2)"><rect width="40" height="64" rx="9"/><line x1="9" y1="16" x2="31" y2="16"/><line x1="9" y1="28" x2="31" y2="28" opacity="0.6"/><line x1="9" y1="40" x2="22" y2="40" opacity="0.4"/></g>'
    doodle_rp = '<g transform="translate(508 70)"><path d="M0 -22 C10 -6 15 2 15 9 A15 15 0 0 1 -15 9 C-15 2 -10 -6 0 -22Z" fill="#b97a00" filter="url(#wob2)"><animateTransform attributeName="transform" type="translate" values="0 -14;0 6;0 6" keyTimes="0;0.45;1" dur="3s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;0;0" keyTimes="0;0.1;0.5;1" dur="3s" repeatCount="indefinite"/></path></g><g transform="translate(508 120)" fill="none" stroke="#b97a00" stroke-width="2.4" filter="url(#wob2)"><ellipse rx="22" ry="6"/></g>'
    doodle_cgpa = '<g transform="translate(486 54)" fill="#2d3b6b" filter="url(#wob2)"><rect x="0" y="40" width="11" height="26" rx="3" opacity="0.45"/><rect x="17" y="24" width="11" height="42" rx="3" opacity="0.7"/><rect x="34" y="6" width="11" height="60" rx="3"/></g>'
    doodle_nptel = '<g transform="translate(508 84)" fill="none" stroke="#c4372c" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" filter="url(#wob2)"><circle r="30" stroke-dasharray="150 40"/><path d="M-12 2 L-3 12 L14 -10"/></g>'

    for lang in ("en", "ta"):
        au_badge, au_color = note_stamp(by_name.get("ausmarthub"), lang, "#2f6a42")
        cgpa_badge, cgpa_color = note_stamp(by_name.get("annamalai-university-cgpa-ogpa"), lang, "#2d3b6b")
        nptel_badge, nptel_color = note_stamp(by_name.get("nptel-calculator"), lang, "#c4372c")
        rp_badge = ("● இயக்கம்" if lang == "ta" else "● Live") if renderping_live else ""

        if lang == "en":
            notes = {
                "note-ausmarthub.svg": render_note_svg(
                    aria_label="AU Smart Hub: A mobile utility app built for Annamalai University students.",
                    rotate="-1.2",
                    accent="#2f6a42",
                    title="AU Smart Hub",
                    title_font=serif,
                    title_size=28,
                    pills=[(50, 80, "Android"), (140, 80, "Cordova"), (230, 88, "Tailwind")],
                    desc_lines=["A mobile utility app built for", "Annamalai University students."],
                    desc_font=serif,
                    desc_size=17,
                    desc_italic=True,
                    url_text="github.com/amudhan-mohan/ausmarthub",
                    badge_text=au_badge,
                    badge_color=au_color,
                    badge_font=sans_en,
                    doodle=doodle_au,
                ),
                "note-renderping.svg": render_note_svg(
                    aria_label="RenderPing: Wakes free Render apps every 10 minutes so they never sleep. Free, no card required.",
                    rotate="1.0",
                    accent="#b97a00",
                    title="RenderPing",
                    title_font=serif,
                    title_size=28,
                    pills=[(50, 64, "Flask"), (124, 88, "Tailwind"), (222, 56, "cron")],
                    desc_lines=["Wakes free Render apps every 10 minutes", "so they never sleep. Free, no card required."],
                    desc_font=serif,
                    desc_size=17,
                    desc_italic=True,
                    url_text="renderping.amudhanmohan.in",
                    badge_text=rp_badge,
                    badge_color="#2f6a42",
                    badge_font=sans_en,
                    doodle=doodle_rp,
                ),
                "note-cgpa.svg": render_note_svg(
                    aria_label="CGPA & OGPA Calculator: Calculate GPA, manage semesters, and track grade points — even offline.",
                    rotate="0.8",
                    accent="#2d3b6b",
                    title="CGPA & OGPA Calculator",
                    title_font=serif,
                    title_size=28,
                    pills=[(50, 64, "React"), (124, 56, "Vite"), (190, 80, "Offline")],
                    desc_lines=["Calculate GPA, manage semesters, and", "track grade points — even offline."],
                    desc_font=serif,
                    desc_size=17,
                    desc_italic=True,
                    url_text="github.com/amudhan-mohan/annamalai-university-cgpa-ogpa",
                    badge_text=cgpa_badge,
                    badge_color=cgpa_color,
                    badge_font=sans_en,
                    doodle=doodle_cgpa,
                ),
                "note-nptel.svg": render_note_svg(
                    aria_label="NPTEL Calculator: A fast internal-mark calculator built for NPTEL courses.",
                    rotate="-1.0",
                    accent="#c4372c",
                    title="NPTEL Calculator",
                    title_font=serif,
                    title_size=28,
                    pills=[(50, 104, "JavaScript")],
                    desc_lines=["A fast internal-mark calculator", "built for NPTEL courses."],
                    desc_font=serif,
                    desc_size=17,
                    desc_italic=True,
                    url_text="github.com/amudhan-mohan/nptel-calculator",
                    badge_text=nptel_badge,
                    badge_color=nptel_color,
                    badge_font=sans_en,
                    doodle=doodle_nptel,
                ),
            }
        else:
            notes = {
                "note-ausmarthub.svg": render_note_svg(
                    aria_label="AU Smart Hub: அண்ணாமலைப் பல்கலைக்கழக மாணவர்களுக்காக உருவாக்கப்பட்ட பயனுள்ள மொபைல் செயலி.",
                    rotate="-1.2",
                    accent="#2f6a42",
                    title="AU Smart Hub",
                    title_font=serif,
                    title_size=28,
                    pills=[(50, 80, "Android"), (140, 80, "Cordova"), (230, 88, "Tailwind")],
                    desc_lines=["அண்ணாமலைப் பல்கலைக்கழக மாணவர்களுக்காக", "உருவாக்கப்பட்ட பயனுள்ள மொபைல் செயலி."],
                    desc_font=sans_ta,
                    desc_size=15.5,
                    desc_italic=False,
                    url_text="github.com/amudhan-mohan/ausmarthub",
                    badge_text=au_badge,
                    badge_color=au_color,
                    badge_font=mixed_ta,
                    doodle=doodle_au,
                ),
                "note-renderping.svg": render_note_svg(
                    aria_label="RenderPing: Render இலவச செயலிகள் உறங்காமல் இருக்க, 10 நிமிடத்திற்கு ஒருமுறை எழுப்பும் இலவச சேவை.",
                    rotate="1.0",
                    accent="#b97a00",
                    title="RenderPing",
                    title_font=serif,
                    title_size=28,
                    pills=[(50, 64, "Flask"), (124, 88, "Tailwind"), (222, 56, "cron")],
                    desc_lines=["Render இலவச செயலிகள் உறங்காமல் இருக்க,", "10 நிமிடத்திற்கு ஒருமுறை எழுப்பும் இலவச சேவை."],
                    desc_font=mixed_ta,
                    desc_size=15.5,
                    desc_italic=False,
                    url_text="renderping.amudhanmohan.in",
                    badge_text=rp_badge,
                    badge_color="#2f6a42",
                    badge_font=mixed_ta,
                    doodle=doodle_rp,
                ),
                "note-cgpa.svg": render_note_svg(
                    aria_label="CGPA & OGPA கணிப்பான்: GPA கணக்கிடவும், செமஸ்டர்கள் மற்றும் கிரேடு புள்ளிகளை இணையமின்றியும் நிர்வகிக்கவும்.",
                    rotate="0.8",
                    accent="#2d3b6b",
                    title="CGPA & OGPA கணிப்பான்",
                    title_font=mixed_ta,
                    title_size=24,
                    pills=[(50, 64, "React"), (124, 56, "Vite"), (190, 94, "ஆஃப்லைன்")],
                    desc_lines=["GPA கணக்கிடவும், செமஸ்டர்கள் மற்றும் கிரேடு", "புள்ளிகளை இணையமின்றியும் நிர்வகிக்கவும்."],
                    desc_font=mixed_ta,
                    desc_size=15.5,
                    desc_italic=False,
                    url_text="github.com/amudhan-mohan/annamalai-university-cgpa-ogpa",
                    badge_text=cgpa_badge,
                    badge_color=cgpa_color,
                    badge_font=mixed_ta,
                    doodle=doodle_cgpa,
                ),
                "note-nptel.svg": render_note_svg(
                    aria_label="NPTEL கணிப்பான்: NPTEL பாடங்களுக்கான விரைவான மற்றும் துல்லியமான உள் மதிப்பெண் கணிப்பான்.",
                    rotate="-1.0",
                    accent="#c4372c",
                    title="NPTEL கணிப்பான்",
                    title_font=mixed_ta,
                    title_size=25,
                    pills=[(50, 104, "JavaScript")],
                    desc_lines=["NPTEL பாடங்களுக்கான விரைவான மற்றும்", "துல்லியமான உள் மதிப்பெண் கணிப்பான்."],
                    desc_font=mixed_ta,
                    desc_size=15.5,
                    desc_italic=False,
                    url_text="github.com/amudhan-mohan/nptel-calculator",
                    badge_text=nptel_badge,
                    badge_color=nptel_color,
                    badge_font=mixed_ta,
                    doodle=doodle_nptel,
                ),
            }

        for filename, content in notes.items():
            (ROOT / "assets" / lang / filename).write_text(content, encoding="utf-8")

        (ROOT / "assets" / lang / "pulse.svg").write_text(render_pulse_svg(repos, lang, open_year), encoding="utf-8")

    print(f"Updated note badges and pulse SVGs (repos fetched: {len(repos)}, RenderPing live: {renderping_live}).")


if __name__ == "__main__":
    main()
