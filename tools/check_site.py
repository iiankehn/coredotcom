#!/usr/bin/env python3
"""Check CORE pages against the BUILD_NOTES.md publishing rules.

Standard library only; nothing to install. Run from the repository root:

    python3 tools/check_site.py          # posts new or changed since origin/main
    python3 tools/check_site.py --all    # audit every post

Exits non-zero when it finds an error. Warnings are printed but do not fail.
Site-wide rules (card order, first-card loading, stylesheet version, unique
field-note numbers) are always checked.
"""

from __future__ import annotations

import re
import struct
import subprocess
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SIZE = (1672, 941)
CARD = re.compile(r"<article class=\"project has-image\">(.*?)</article>", re.S)
STYLESHEET = re.compile(r"css/style\.css\?v=([^\"]+)\"")

errors: list[str] = []
warnings: list[str] = []


def text(fragment: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def first(pattern: str, html: str) -> str | None:
    match = re.search(pattern, html, re.S)
    return match.group(1) if match else None


def webp_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:30]
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X":
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return width, height
    if chunk == b"VP8 ":
        width, height = struct.unpack("<HH", data[26:30])
        return width & 0x3FFF, height & 0x3FFF
    if chunk == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    return None


def check_image(src: str, page: str) -> None:
    path = (ROOT / page).parent / src
    if not path.is_file():
        errors.append(f"{page}: image {src} does not exist")
        return
    if path.suffix == ".webp" and webp_size(path) != IMAGE_SIZE:
        errors.append(f"{page}: {src} is {webp_size(path)}, expected {IMAGE_SIZE}")


def changed_posts() -> set[str]:
    """Post filenames added or modified relative to origin/main, including uncommitted work."""
    def git(*args: str) -> list[str]:
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        return result.stdout.splitlines() if result.returncode == 0 else []

    names = git("diff", "--name-only", "origin/main", "--", "posts")
    names += [line[3:] for line in git("status", "--porcelain", "--", "posts")]
    return {Path(name).name for name in names if name.endswith(".html")}


def check_post(path: Path) -> dict:
    html = path.read_text(encoding="utf-8")
    page = path.relative_to(ROOT).as_posix()
    post = {
        "page": page,
        "title": text(first(r"<h1>(.*?)</h1>", html) or ""),
        "deck": text(first(r"<p class=\"article-deck\">(.*?)</p>", html) or ""),
        "date": first(r"<div class=\"byline\">.*?<time datetime=\"([0-9-]+)\"", html),
        "read": first(r"<span>(\d+ min read)</span>", html),
        "note": first(r"Field note (\d+)", html),
        "end": first(r"End note (\d+)", html),
        "image": first(r"<figure class=\"article-image\"><img src=\"([^\"]+)\"", html),
    }
    for key in ("title", "deck", "date", "read", "note", "image"):
        if not post[key]:
            errors.append(f"{page}: missing {key}")
    if post["note"] != post["end"]:
        errors.append(f"{page}: Field note {post['note']} but End note {post['end']}")
    if post["image"]:
        check_image(post["image"], page)
    return post


def main() -> int:
    audit_all = "--all" in sys.argv[1:]
    scope = None if audit_all else changed_posts()
    posts = {}
    for path in sorted((ROOT / "posts").glob("*.html")):
        before = len(errors)
        posts[path.name] = check_post(path)
        if scope is not None and path.name not in scope:
            del errors[before:]

    numbers: dict[str, str] = {}
    for post in posts.values():
        if post["note"] in numbers:
            errors.append(f"{post['page']}: Field note {post['note']} also used by {numbers[post['note']]}")
        numbers.setdefault(post["note"], post["page"])

    index = (ROOT / "index.html").read_text(encoding="utf-8")
    cards = CARD.findall(index)
    linked: set[str] = set()
    previous_date = "9999-99-99"
    for position, card in enumerate(cards):
        href = first(r"<h3><a href=\"posts/([^\"]+)\"", card)
        if not href:
            errors.append(f"index.html: card {position + 1} has no headline link")
            continue
        linked.add(href)
        post = posts.get(href)
        if post is None:
            errors.append(f"index.html: card links to missing posts/{href}")
            continue
        label = f"index.html card for {href}"
        date = first(r"<time datetime=\"([0-9-]+)\"", card)
        if date and date > previous_date:
            errors.append(f"{label}: out of date order (newest first)")
        previous_date = date or previous_date
        lazy = 'loading="lazy"' in card.split(">", 1)[0]
        if position == 0 and lazy:
            errors.append(f"{label}: the first card must not be lazy-loaded")
        if scope is not None and href not in scope:
            continue
        if position > 0 and not lazy:
            errors.append(f"{label}: cards after the first need loading=\"lazy\"")
        if f'class="project-link" href="posts/{href}"' not in card:
            errors.append(f"{label}: “Read report” link does not match the headline link")
        if date != post["date"]:
            errors.append(f"{label}: date {date} but article says {post['date']}")
        if text(first(r"<h3>(.*?)</h3>", card) or "") != post["title"]:
            errors.append(f"{label}: headline differs from the article h1")
        summary = text(first(r"</h3>\s*<p>(.*?)</p>", card) or "")
        if summary != post["deck"]:
            errors.append(f"{label}: summary differs from the article deck")
        if post["read"] and post["read"] not in card:
            errors.append(f"{label}: reading time differs from the article ({post['read']})")
        image = first(r"<img src=\"([^\"]+)\"", card)
        if post["image"] and image != post["image"].removeprefix("../"):
            errors.append(f"{label}: card image {image} differs from article image {post['image']}")

    for name in sorted(set(posts) - linked if audit_all else (scope or set()) - linked):
        warnings.append(f"posts/{name}: no card on index.html (unpublished draft?)")

    pages = [ROOT / "index.html", ROOT / "about.html", ROOT / "templates/post-template.html"]
    pages += [ROOT / "posts" / name for name in posts]
    versions = {}
    for page in pages:
        if page.is_file():
            versions.setdefault(first(STYLESHEET.pattern, page.read_text(encoding="utf-8")), []).append(
                page.relative_to(ROOT).as_posix())
    if len(versions) > 1:
        detail = "; ".join(f"{v}: {len(p)} pages" for v, p in versions.items())
        errors.append(f"stylesheet cache-busting versions differ ({detail})")

    for message in warnings:
        print(f"warning: {message}")
    for message in errors:
        print(f"error: {message}")
    checked = len(posts) if audit_all else len(scope or ())
    print(f"Checked {checked} of {len(posts)} posts ({'all' if audit_all else 'changed since origin/main'}) "
          f"and {len(cards)} cards: "
          f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
