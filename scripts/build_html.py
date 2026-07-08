#!/usr/bin/env python3
"""
build_html.py

Reads posts.json (raw output from the Facebook Graph API /feed endpoint)
and injects a matching-styled HTML block into index.html, between the
markers:

    <!-- FB_POSTS_START -->
    <!-- FB_POSTS_END -->

Usage:
    python scripts/build_html.py
"""

import json
import html
import re
import sys
from datetime import datetime
from pathlib import Path

POSTS_JSON = Path("posts.json")
SITE_HTML = Path("index.html")   # adjust path if your file lives elsewhere
MAX_POSTS = 6                       # how many posts to show
START_MARK = "<!-- FB_POSTS_START -->"
END_MARK = "<!-- FB_POSTS_END -->"


def load_posts():
    if not POSTS_JSON.exists():
        sys.exit(f"ERROR: {POSTS_JSON} not found. Run the curl fetch step first.")
    data = json.loads(POSTS_JSON.read_text(encoding="utf-8"))
    posts = data.get("data", [])
    return posts[:MAX_POSTS]


def format_date(iso_str):
    try:
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S%z")
        return dt.strftime("%b %d, %Y")
    except Exception:
        return iso_str


def build_card(post):
    message = html.escape(post.get("message", "").strip() or "View this post on Facebook")
    date = format_date(post.get("created_time", ""))
    link = post.get("permalink_url") or "https://www.facebook.com/share/18mYZkUZe1/"
    image = post.get("full_picture")

    img_tag = f'<img src="{html.escape(image)}" alt="" loading="lazy"/>' if image else ""

    return f"""<a class="fb-card" href="{html.escape(link)}" target="_blank" rel="noopener">
  {img_tag}
  <div class="fb-card-body">
    <span class="fb-card-date">{html.escape(date)}</span>
    <p class="fb-card-text">{message}</p>
  </div>
</a>"""


def build_block(posts):
    if not posts:
        return '<p style="color:var(--muted);font-size:13px">No posts synced yet.</p>'
    return "\n".join(build_card(p) for p in posts)


def inject(html_text, block):
    pattern = re.compile(
        re.escape(START_MARK) + r".*?" + re.escape(END_MARK),
        re.DOTALL,
    )
    replacement = f"{START_MARK}\n{block}\n{END_MARK}"
    new_text, count = pattern.subn(replacement, html_text)
    if count == 0:
        sys.exit("ERROR: markers not found in gcp-shop.html — did the section get removed?")
    return new_text


def main():
    posts = load_posts()
    block = build_block(posts)

    if not SITE_HTML.exists():
        sys.exit(f"ERROR: {SITE_HTML} not found.")
    original = SITE_HTML.read_text(encoding="utf-8")
    updated = inject(original, block)

    if updated == original:
        print("No changes — HTML already up to date.")
        return

    SITE_HTML.write_text(updated, encoding="utf-8")
    print(f"Injected {len(posts)} post(s) into {SITE_HTML}")


if __name__ == "__main__":
    main()
