#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SITE_DIR = BASE_DIR / "site"

FORBIDDEN_TARGETS = [
    "zid.univie.ac.at/helpdesk",
]

HREF_PATTERN = re.compile(r'(?:href|src)=["\']([^"\']+)["\']', re.IGNORECASE)


def _matches_forbidden(url: str) -> str | None:
    lowered = url.lower()
    for forbidden in FORBIDDEN_TARGETS:
        if forbidden.lower() in lowered:
            return forbidden
    return None


def _is_internal_link(url: str) -> bool:
    """Checks if the URL is an internal link that should be verified."""
    if url.startswith(("http://", "https://", "mailto:", "#", "tel:")):
        return False
    # Check for scheme just in case
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme:
        return False
    return True


def _check_target_exists(source_file: Path, url: str) -> bool:
    """
    Checks if the target file exists.
    Handles relative paths and absolute paths (relative to site root).
    Ignores query parameters and fragments.
    """
    # Strip query parameters and fragments
    url_clean = url.split("?")[0].split("#")[0]

    if not url_clean:
        return True # Empty link or just anchor/query

    if url_clean.startswith("/"):
        # Absolute path relative to site root
        target_path = SITE_DIR / url_clean.lstrip("/")
    else:
        # Relative path
        target_path = source_file.parent / url_clean

    # If the target is a directory, check for index.html
    if target_path.is_dir():
        # But wait, checking is_dir() on a non-existent path returns False.
        # So we should first check if it resolves.
        # If it doesn't exist, we can try appending index.html IF the link ends with /
        # or implies a directory.
        # But commonly web servers serve index.html for directory paths.
        if (target_path / "index.html").exists():
            return True
        if (target_path / "index.php").exists():
            return True

    if target_path.exists():
        return True

    # Try resolving to check if it points to an existing directory
    try:
        resolved = target_path.resolve()
        if resolved.exists():
            return True
    except OSError:
        pass

    return False


def main() -> int:
    if not SITE_DIR.exists():
        print("[ALI] site/ directory not found. Run python3 tools/build.py first.")
        return 1

    forbidden_hits: list[tuple[Path, str, str]] = []
    broken_links: list[tuple[Path, str]] = []

    for path in SITE_DIR.rglob("*.html"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for url in HREF_PATTERN.findall(text):
            url = url.strip()

            # Check for forbidden targets
            match = _matches_forbidden(url)
            if match:
                forbidden_hits.append((path, url, match))
                continue

            # Check for broken internal links
            if _is_internal_link(url):
                if not _check_target_exists(path, url):
                    broken_links.append((path, url))

    exit_code = 0

    if forbidden_hits:
        print("[ALI] Forbidden external targets found:")
        for path, url, match in forbidden_hits:
            rel = path.relative_to(BASE_DIR)
            print(f"  {rel}: {url} (matches {match})")
        exit_code = 1

    if broken_links:
        print("[ALI] Broken internal links found:")
        for path, url in broken_links:
            rel = path.relative_to(BASE_DIR)
            print(f"  {rel}: {url}")
        exit_code = 1

    if exit_code == 0:
        print("[ALI] Link verification passed. No forbidden external targets or broken internal links found.")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
