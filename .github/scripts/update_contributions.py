"""Generate handcrafted parchment GitHub Contribution, Account Age & Achievements SVGs."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
USERNAME = "amudhan-mohan"

MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_TA = ["ஜன", "பிப்", "மார்", "ஏப்", "மே", "ஜூன்", "ஜூலை", "ஆக", "செப்", "அக்", "நவ", "டிச"]
LEVEL_COLORS = ["#efe3c8", "#c5db9f", "#8ab96a", "#3f7d4e", "#245432"]

# Accent color + crisp vector emblem path (centered in a 20x20 icon slot) per achievement slug
BADGE_STYLES: dict[str, tuple[str, str]] = {
    "pull-shark": (
        "#2d3b6b",
        '<path d="M-5 4 Q-1 -5 5 -4 Q2 0 4 4 Z" fill="#fffaf0"/>'
        '<path d="M-6 5 Q0 2 6 5" fill="none" stroke="#fffaf0" stroke-width="1.5" stroke-linecap="round"/>',
    ),
    "yolo": (
        "#b97a00",
        '<path d="M1 -6 L-4 1 H0 L-1 6 L4 -1 H0 Z" fill="#fffaf0"/>',
    ),
    "quickdraw": (
        "#2f6a42",
        '<path d="M-5 0 H4 M1 -4 L5 0 L1 4" fill="none" stroke="#fffaf0" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
    ),
    "starstruck": (
        "#c4372c",
        '<path d="M0 -6 L1.8 -1.8 L6 -1.5 L2.8 1.4 L3.8 5.6 L0 3.4 L-3.8 5.6 L-2.8 1.4 L-6 -1.5 L-1.8 -1.8 Z" fill="#fffaf0"/>',
    ),
    "pair-extraordinaire": (
        "#3f7d4e",
        '<circle cx="-2.5" cy="-1.5" r="2.2" fill="#fffaf0"/><circle cx="2.5" cy="1.5" r="2.2" fill="#fffaf0"/>',
    ),
    "galaxy-brain": (
        "#4b3a52",
        '<circle cx="0" cy="0" r="4" fill="none" stroke="#fffaf0" stroke-width="1.6"/>'
        '<circle cx="0" cy="0" r="1.5" fill="#fffaf0"/>',
    ),
}
DEFAULT_BADGE_STYLE = (
    "#6b5226",
    '<path d="M0 -5 L1.5 -1.5 L5 -1.2 L2.3 1.2 L3.1 4.8 L0 2.9 L-3.1 4.8 L-2.3 1.2 L-5 -1.2 L-1.5 -1.5 Z" fill="#fffaf0"/>',
)


def fetch_public_calendar(username: str) -> tuple[int, list[dict]]:
    """Fetch total contributions and 52-week daily cells from GitHub's profile calendar HTML."""
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "amudhan-mohan-profile-updater"})
    html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")

    m_total = re.search(r"([\d,]+)\s+contributions\s+in the last year", html)
    total = int(m_total.group(1).replace(",", "")) if m_total else 0

    tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]+)</tool-tip>', html))
    tds = re.findall(
        r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="(contribution-day-component-(\d+)-(\d+))"[^>]*data-level="(\d)"',
        html,
    )
    if not tds:
        raise RuntimeError("Could not parse contribution cells from GitHub calendar HTML.")

    days: list[dict] = []
    for dt_str, cid, row_str, col_str, lvl_str in tds:
        tip = tips.get(cid, "")
        m_cnt = re.match(r"(\d+)\s+contribution", tip)
        cnt = int(m_cnt.group(1)) if m_cnt else 0
        days.append(
            {
                "date": dt_str,
                "row": int(row_str),
                "col": int(col_str),
                "level": min(4, max(0, int(lvl_str))),
                "count": cnt,
            }
        )
    if total == 0:
        total = sum(d["count"] for d in days)
    return total, days


def fetch_account_created(username: str) -> str | None:
    """Fetch ISO created_at timestamp from GitHub public user API."""
    headers = {"User-Agent": "amudhan-mohan-profile-updater", "Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_METRICS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(f"https://api.github.com/users/{username}", headers=headers)
        data = json.loads(urllib.request.urlopen(req, timeout=12).read().decode("utf-8"))
        return data.get("created_at")
    except Exception:
        return None


def fetch_achievements(username: str) -> list[dict]:
    """Fetch public GitHub achievement badges from the user's achievements tab."""
    url = f"https://github.com/{username}?tab=achievements"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
    except Exception:
        return []

    seen: set[str] = set()
    badges: list[dict] = []
    for slug, inner in re.findall(r'<a[^>]*href="[^"]*achievement=([^"&]+)[^"]*"[^>]*>(.*?)</a>', html, re.S):
        if slug in seen:
            continue
        m_alt = re.search(r'alt="Achievement:\s*([^"]+)"', inner)
        if not m_alt:
            continue
        m_tier = re.search(r"achievement-tier-label[^>]*>([^<]+)<", inner)
        seen.add(slug)
        badges.append(
            {
                "slug": slug,
                "name": m_alt.group(1).strip(),
                "tier": m_tier.group(1).strip() if m_tier else "",
            }
        )
    return badges


def fetch_graphql_breakdown(username: str, token: str) -> dict | None:
    """Optionally query GitHub GraphQL for detailed commits/PRs/issues/reviews breakdown."""
    now = datetime.now(timezone.utc)
    month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    query = """
    query($login: String!, $from: DateTime!) {
      user(login: $login) {
        year: contributionsCollection {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
        }
        recent: contributionsCollection(from: $from) {
          commitContributionsByRepository(maxRepositories: 10) {
            repository { name isPrivate }
            contributions { totalCount }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": username, "from": month_ago}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "amudhan-mohan-profile-updater",
        },
    )
    try:
        res = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))
        return res.get("data", {}).get("user")
    except Exception:
        return None


def compute_streaks(days: list[dict]) -> tuple[int, int]:
    """Return (active_days, best_streak) sorted chronologically."""
    ordered = sorted(days, key=lambda d: d["date"])
    active_days = sum(1 for d in ordered if d["count"] > 0 or d["level"] > 0)
    best = 0
    cur = 0
    prev_dt: date | None = None
    for d in ordered:
        dt = date.fromisoformat(d["date"])
        has = d["count"] > 0 or d["level"] > 0
        if has:
            if prev_dt and (dt - prev_dt).days == 1:
                cur += 1
            else:
                cur = 1
            best = max(best, cur)
            prev_dt = dt
        else:
            cur = 0
            prev_dt = None
    return active_days, best


def render_achievement_pills(badges: list[dict], start_x: float, y: float, font_ui: str) -> str:
    """Render handcrafted vector badge pills for unlocked GitHub achievements."""
    x = start_x
    parts: list[str] = []
    for b in badges[:5]:
        text = f"{b['name']} {b['tier']}".strip()
        color, icon = BADGE_STYLES.get(b["slug"], DEFAULT_BADGE_STYLE)
        pill_w = max(92.0, 44.0 + len(text) * 8.2)
        if x + pill_w > 880:
            break
        parts.append(
            f'<g transform="translate({x:.1f} {y:.1f})">'
            f'<rect width="{pill_w:.1f}" height="32" rx="16" fill="#fffaf0" stroke="{color}" stroke-width="1.8" filter="url(#wob2)"/>'
            f'<circle cx="17" cy="16" r="10.5" fill="{color}"/>'
            f'<g transform="translate(17 16)">{icon}</g>'
            f'<text x="34" y="20.5" font-family="{font_ui}" font-size="12.5" font-weight="600" fill="#3a2d28" text-anchor="start">{escape(text)}</text>'
            "</g>"
        )
        x += pill_w + 10.0
    return "".join(parts)


def render_contributions_svg(
    *,
    total: int,
    days: list[dict],
    lang: str,
    gql_data: dict | None,
    created_at: str | None,
    badges: list[dict],
) -> str:
    """Render a 1160x436 warm parchment contributions, activity compass & achievements SVG."""
    months = MONTHS_TA if lang == "ta" else MONTHS_EN
    font_ui = (
        "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans Tamil','Nirmala UI',Latha,'Tamil Sangam MN',sans-serif"
        if lang == "ta"
        else "'Segoe UI','Helvetica Neue',Helvetica,Arial,'Noto Sans',sans-serif"
    )
    font_serif = "Georgia,'Palatino Linotype',Palatino,'Noto Serif',serif"

    active_days, best_streak = compute_streaks(days)
    max_col = max(d["col"] for d in days)

    by_month: dict[str, int] = defaultdict(int)
    for d in days:
        by_month[d["date"][:7]] += d["count"]
    recent_months = sorted(by_month.keys())[-4:][::-1]

    joined_label = ""
    if created_at:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        m_lbl = months[dt.month - 1]
        joined_label = f"{m_lbl} {dt.year} முதல் கணக்கு" if lang == "ta" else f"Joined {m_lbl} {dt.year}"

    if lang == "ta":
        title = f"கடந்த ஆண்டில் {total} பங்களிப்புகள்"
        stats = f"செயல் நாட்கள்: {active_days}  ·  சிறந்த தொடர்ச்சி: {best_streak} நாட்கள்"
        weekdays = [(1, "திங்"), (3, "புதன்"), (5, "வெள்")]
        less_lbl, more_lbl = "குறைவு", "அதிகம்"
        left_title = "சமீபத்திய கமிட் & பங்களிப்பு"
        compass_title = "செயல்பாட்டுப் பிரிவு"
        axes_lbls = ("கமிட்கள்", "சிக்கல்கள்", "PR-கள்", "ஆய்வு")
        ach_title = "சாதனைகள்"
        ach_start_x = 154.0
    else:
        title = f"{total} contributions in the last year"
        stats = f"Active days: {active_days}  ·  Best streak: {best_streak}d"
        weekdays = [(1, "Mon"), (3, "Wed"), (5, "Fri")]
        less_lbl, more_lbl = "Less", "More"
        left_title = "Recent activity breakdown"
        compass_title = "Activity overview"
        axes_lbls = ("Commits", "Issues", "Pull requests", "Code review")
        ach_title = "Achievements"
        ach_start_x = 152.0

    grid_x0 = 92.0
    grid_y0 = 86.0
    pitch = 19.3
    cell_size = 15.0

    month_labels_svg: list[str] = []
    seen_ym: set[str] = set()
    col_first_date: dict[int, str] = {}
    for d in sorted(days, key=lambda x: (x["col"], x["row"])):
        col_first_date.setdefault(d["col"], d["date"])
    for col in range(max_col + 1):
        dt_str = col_first_date.get(col)
        if not dt_str:
            continue
        ym = dt_str[:7]
        if ym not in seen_ym:
            seen_ym.add(ym)
            if col == 0 and int(dt_str[8:10]) > 22:
                continue
            m_idx = int(dt_str[5:7]) - 1
            mx = grid_x0 + col * pitch
            month_labels_svg.append(
                f'<text x="{mx:.1f}" y="74" font-family="{font_ui}" font-size="11.5" '
                f'fill="#7a6a5c" text-anchor="start">{escape(months[m_idx])}</text>'
            )

    weekday_svg = "".join(
        f'<text x="36" y="{grid_y0 + r * pitch + 11.5:.1f}" font-family="{font_ui}" '
        f'font-size="11.5" fill="#7a6a5c" text-anchor="start">{escape(lbl)}</text>'
        for r, lbl in weekdays
    )

    cells_svg = "".join(
        f'<rect x="{grid_x0 + d["col"] * pitch:.1f}" y="{grid_y0 + d["row"] * pitch:.1f}" '
        f'width="{cell_size}" height="{cell_size}" rx="3.5" fill="{LEVEL_COLORS[d["level"]]}"/>'
        for d in days
    )

    legend_x = 964.0
    legend_svg = (
        f'<text x="{legend_x - 8:.1f}" y="241" font-family="{font_ui}" font-size="11.5" '
        f'fill="#7a6a5c" text-anchor="end">{escape(less_lbl)}</text>'
        + "".join(
            f'<rect x="{legend_x + i * 18:.1f}" y="229" width="13" height="13" rx="3" fill="{c}"/>'
            for i, c in enumerate(LEVEL_COLORS)
        )
        + f'<text x="{legend_x + 96:.1f}" y="241" font-family="{font_ui}" font-size="11.5" '
        f'fill="#7a6a5c" text-anchor="start">{escape(more_lbl)}</text>'
    )

    bars: list[tuple[str, int]] = []
    if gql_data and gql_data.get("recent"):
        show_priv = os.environ.get("INCLUDE_PRIVATE_NAMES") == "1"
        priv_total = 0
        for item in gql_data["recent"].get("commitContributionsByRepository", []):
            repo = item["repository"]
            cnt = int(item["contributions"]["totalCount"])
            if cnt <= 0:
                continue
            if repo["isPrivate"] and not show_priv:
                priv_total += cnt
            else:
                bars.append((repo["name"], cnt))
        if priv_total > 0:
            bars.append(("தனிப்பட்ட திட்டங்கள்" if lang == "ta" else "Private repositories", priv_total))
        bars.sort(key=lambda x: x[1], reverse=True)
        bars = bars[:4]

    if not bars:
        for ym in recent_months:
            m_idx = int(ym[5:7]) - 1
            yr = ym[2:4]
            bars.append((f"{months[m_idx]} ’{yr}", by_month[ym]))

    max_bar = max((v for _, v in bars), default=1) or 1
    bars_svg: list[str] = []
    for idx, (label, val) in enumerate(bars):
        by = 294 + idx * 19
        bar_w = max(8.0, 290.0 * (val / max_bar))
        unit = "கமிட்" if (gql_data and lang == "ta") else ("commits" if gql_data else "")
        val_str = f"{val} {unit}".strip()
        bars_svg.append(
            f'<text x="36" y="{by}" font-family="{font_ui}" font-size="12.5" fill="#3a2d28" text-anchor="start">{escape(label[:26])}</text>'
            f'<rect x="230" y="{by - 10}" width="290" height="8" rx="4" fill="#efe3c8"/>'
            f'<rect x="230" y="{by - 10}" width="{bar_w:.1f}" height="8" rx="4" fill="#3f7d4e" filter="url(#wob2)"/>'
            f'<text x="532" y="{by}" font-family="{font_ui}" font-size="12" font-weight="600" fill="#2f6a42" text-anchor="start">{escape(val_str)}</text>'
        )

    if gql_data and gql_data.get("year"):
        yr_col = gql_data["year"]
        c_commits = int(yr_col["totalCommitContributions"])
        c_issues = int(yr_col["totalIssueContributions"])
        c_prs = int(yr_col["totalPullRequestContributions"])
        c_reviews = int(yr_col["totalPullRequestReviewContributions"])
    else:
        c_commits, c_issues, c_prs, c_reviews = max(total, 1), 0, 0, 0

    c_sum = max(1, c_commits + c_issues + c_prs + c_reviews)
    p_commits = round(100 * c_commits / c_sum)
    p_issues = round(100 * c_issues / c_sum)
    p_prs = round(100 * c_prs / c_sum)
    p_reviews = max(0, 100 - p_commits - p_issues - p_prs) if (c_issues or c_prs or c_reviews) else 0

    cx, cy, arm = 918.0, 312.0, 28.0
    l_len = max(8.0, arm * (p_commits / 100.0)) if p_commits else 0.0
    r_len = max(6.0, arm * (p_issues / 100.0)) if p_issues else 0.0
    b_len = max(6.0, arm * (p_prs / 100.0)) if p_prs else 0.0
    t_len = max(6.0, arm * (p_reviews / 100.0)) if p_reviews else 0.0

    poly_pts = f"{cx - l_len:.1f},{cy} {cx},{cy - t_len:.1f} {cx + r_len:.1f},{cy} {cx},{cy + b_len:.1f}"
    lbl_c, lbl_i, lbl_p, lbl_r = axes_lbls

    compass_svg = (
        f'<text x="720" y="274" font-family="{font_ui}" font-size="14" font-weight="bold" fill="#3a2d28" text-anchor="start">{escape(compass_title)}</text>'
        f'<line x1="{cx - arm}" y1="{cy}" x2="{cx + arm}" y2="{cy}" stroke="#dccb94" stroke-width="2.4" stroke-linecap="round"/>'
        f'<line x1="{cx}" y1="{cy - arm}" x2="{cx}" y2="{cy + arm}" stroke="#dccb94" stroke-width="2.4" stroke-linecap="round"/>'
        f'<polygon points="{poly_pts}" fill="#3f7d4e" fill-opacity="0.22" stroke="#2f6a42" stroke-width="2" stroke-linejoin="round"/>'
        f'<line x1="{cx}" y1="{cy}" x2="{cx - l_len:.1f}" y2="{cy}" stroke="#2f6a42" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="{cx - l_len:.1f}" cy="{cy}" r="3.6" fill="#2f6a42" stroke="#fffaf0" stroke-width="1.2"/>'
        f'<text x="{cx}" y="{cy - arm - 7}" font-family="{font_ui}" font-size="11.5" fill="#7a6a5c" text-anchor="middle">{escape(lbl_r)}</text>'
        f'<text x="{cx + arm + 10}" y="{cy + 4}" font-family="{font_ui}" font-size="11.5" fill="#7a6a5c" text-anchor="start">{escape(lbl_i)}</text>'
        f'<text x="{cx}" y="{cy + arm + 14}" font-family="{font_ui}" font-size="11.5" fill="#7a6a5c" text-anchor="middle">{escape(lbl_p)}</text>'
        f'<text x="{cx - arm - 10}" y="{cy - 2}" font-family="{font_ui}" font-size="12" font-weight="bold" fill="#2f6a42" text-anchor="end">{p_commits}%</text>'
        f'<text x="{cx - arm - 10}" y="{cy + 12}" font-family="{font_ui}" font-size="11.5" fill="#3a2d28" text-anchor="end">{escape(lbl_c)}</text>'
    )

    badges_svg = render_achievement_pills(badges, ach_start_x, 383.0, font_ui)
    ach_names = ", ".join(b["name"] for b in badges)
    aria = f"{title}. {stats}. {ach_title}: {ach_names}. {joined_label}."

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1160 436" width="1160" height="436" '
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
        "</defs>\n"
        '<rect width="1160" height="436" rx="18" fill="#f7f0df"/>'
        '<rect width="1160" height="436" rx="18" filter="url(#grain)"/>'
        '<rect x="1.5" y="1.5" width="1157" height="433" rx="17" fill="none" stroke="#dccb94" stroke-width="2" filter="url(#wob2)"/>\n'
        f'<text x="36" y="42" font-family="{font_serif if lang == "en" else font_ui}" font-size="21" font-weight="bold" fill="#3a2d28" text-anchor="start">{escape(title)}</text>\n'
        f'<text x="1124" y="42" font-family="{font_ui}" font-size="13" fill="#7a6a5c" text-anchor="end">{escape(stats)}</text>\n'
        + "".join(month_labels_svg)
        + "\n"
        + weekday_svg
        + "\n"
        + cells_svg
        + "\n"
        + legend_svg
        + '\n<line x1="36" y1="254" x2="1124" y2="254" stroke="#dccb94" stroke-width="1.8" stroke-dasharray="5 6" stroke-linecap="round"/>\n'
        f'<text x="36" y="274" font-family="{font_ui}" font-size="14" font-weight="bold" fill="#3a2d28" text-anchor="start">{escape(left_title)}</text>\n'
        + "\n".join(bars_svg)
        + "\n"
        + compass_svg
        + '\n<line x1="36" y1="368" x2="1124" y2="368" stroke="#dccb94" stroke-width="1.8" stroke-dasharray="5 6" stroke-linecap="round"/>\n'
        + f'<text x="36" y="404" font-family="{font_ui}" font-size="14" font-weight="bold" fill="#3a2d28" text-anchor="start">{escape(ach_title)}</text>\n'
        + badges_svg
        + f'\n<text x="1124" y="404" font-family="{font_ui}" font-size="13" font-weight="600" fill="#7a6a5c" text-anchor="end">{escape(joined_label)}</text>\n'
        + "</svg>"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Update GitHub contribution calendar, achievements & account age SVGs.")
    parser.add_argument("--offline", action="store_true", help="Keep existing SVGs if offline")
    args = parser.parse_args()

    if args.offline:
        print("Offline mode: skipping contribution fetch.")
        return

    try:
        total, days = fetch_public_calendar(USERNAME)
    except Exception as exc:
        print(f"Warning: could not fetch contribution calendar ({exc}); keeping existing SVGs.")
        return

    created_at = fetch_account_created(USERNAME)
    badges = fetch_achievements(USERNAME)
    token = os.environ.get("GH_METRICS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    gql_data = fetch_graphql_breakdown(USERNAME, token) if token else None

    for lang in ("en", "ta"):
        svg = render_contributions_svg(
            total=total,
            days=days,
            lang=lang,
            gql_data=gql_data,
            created_at=created_at,
            badges=badges,
        )
        (ROOT / "assets" / lang / "contributions.svg").write_text(svg, encoding="utf-8")

    print(
        f"Updated contributions.svg ({total} contributions, {len(days)} days, "
        f"joined={created_at[:10] if created_at else 'n/a'}, badges={[b['name'] for b in badges]})."
    )


if __name__ == "__main__":
    main()
