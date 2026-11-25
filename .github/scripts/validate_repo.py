"""Validate SVGs, Tamil/English asset isolation, README references, and data integrity."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = ROOT / "assets"
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")


def main() -> int:
    errors: list[str] = []

    # 1. Validate XML and language separation for every SVG
    svgs = sorted(ASSETS_DIR.rglob("*.svg"))
    for svg in svgs:
        text = svg.read_text(encoding="utf-8")
        try:
            ET.fromstring(text)
        except ET.ParseError as exc:
            errors.append(f"Invalid XML in {svg.relative_to(ROOT)}: {exc}")

        if svg.parent.name == "en" and TAMIL_RE.search(text):
            errors.append(f"Tamil script leaked into English SVG: {svg.relative_to(ROOT)}")
        if svg.parent.name == "ta" and not TAMIL_RE.search(text):
            errors.append(f"Missing Tamil script in Tamil SVG: {svg.relative_to(ROOT)}")

    # 2. Validate README language buttons, links, and unreferenced assets
    ta_readme = ROOT / "README.md"
    en_readme = ROOT / "README.en.md"

    ta_text = ta_readme.read_text(encoding="utf-8")
    en_text = en_readme.read_text(encoding="utf-8")

    if "btn-ta" in ta_text or "btn-en.svg" not in ta_text:
        errors.append("README.md must only display the English switch button (btn-en.svg).")
    if "btn-en" in en_text or "btn-ta.svg" not in en_text:
        errors.append("README.en.md must only display the Tamil switch button (btn-ta.svg).")

    referenced: set[Path] = set()
    for md_path, text in ((ta_readme, ta_text), (en_readme, en_text)):
        srcs = re.findall(r'src="([^"]+)"', text)
        hrefs = re.findall(r'(?:href="|\]\()(\./[^")]+)', text)
        for rel in srcs + [h[2:] for h in hrefs]:
            target = (ROOT / rel).resolve()
            if not target.exists():
                errors.append(f"Missing target '{rel}' referenced in {md_path.name}")
            elif ASSETS_DIR in target.parents:
                referenced.add(target)

    for svg in svgs:
        if svg.resolve() not in referenced:
            errors.append(f"Unreferenced SVG asset: {svg.relative_to(ROOT)}")

    # 3. Validate Thirukkural dataset and profile config
    kurals = json.loads((ROOT / ".github" / "data" / "thirukkural.json").read_text(encoding="utf-8"))
    if len(kurals) != 1330:
        errors.append(f"Expected 1330 kurals in thirukkural.json, found {len(kurals)}")

    cfg = json.loads((ROOT / ".github" / "profile-config.json").read_text(encoding="utf-8"))
    if cfg.get("availability") not in ("open", "freelance", "busy"):
        errors.append(f"Invalid availability in profile-config.json: {cfg.get('availability')!r}")

    print(f"Validated {len(svgs)} SVGs, 2 READMEs, {len(kurals)} kurals | Errors: {len(errors)}")
    for err in errors:
        print(f"ERROR: {err}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
