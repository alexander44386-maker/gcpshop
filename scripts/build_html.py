"""
Reads posts.json (fetched from the Facebook Graph API) and writes
fb-posts.html — a ready-to-embed HTML snippet you can include on
your GitHub Pages site.

Usage in your site (plain HTML, no build step needed):
    <div id="fb-posts"></div>
    <script>
      fetch('fb-posts.html')
        .then(r => r.text())
        .then(html => document.getElementById('fb-posts').innerHTML = html);
    </script>

Or, if your site uses Jekyll, save this as _includes/fb-posts.html
instead and use {% include fb-posts.html %} in a layout.
"""

import json
import html
from datetime import datetime

INPUT_FILE = "posts.json"
OUTPUT_FILE = "fb-posts.html"


def format_date(iso_string):
    dt = datetime.strptime(iso_string, "%Y-%m-%dT%H:%M:%S%z")
    return dt.strftime("%B %d, %Y")


def build_post_html(post):
    message = html.escape(post.get("message", "")).replace("\n", "<br>")
    date = format_date(post["created_time"]) if post.get("created_time") else ""
    link = post.get("permalink_url", "#")
    image = post.get("full_picture")

    image_html = f'<img src="{image}" alt="" class="fb-post-image">' if image else ""

    return f"""
    <article class="fb-post">
      {image_html}
      <p class="fb-post-text">{message}</p>
      <div class="fb-post-meta">
        <time>{date}</time>
        <a href="{link}" target="_blank" rel="noopener">View on Facebook →</a>
      </div>
    </article>
    """.strip()


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    posts = data.get("data", [])

    if not posts:
        print("No posts found in posts.json — check your token/page ID and permissions.")

    posts_html = "\n".join(build_post_html(p) for p in posts if p.get("message"))

    output = f'<div class="fb-posts-container">\n{posts_html}\n</div>\n'

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Wrote {len(posts)} posts to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
