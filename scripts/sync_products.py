#!/usr/bin/env python3
"""
sync_products.py

Reads posts.json (Facebook Graph API output) and looks for posts written
in this template:

    Name: Product Name
    Brand: Brand Name
    Icon: emoji (optional, defaults to a box)
    Shopee: link (optional if TikTok is given)
    TikTok: link (optional if Shopee is given)

Any post matching the template becomes a new product, pushed directly to
the same Firebase Realtime Database gcp-shop.html reads from. Already
-processed post IDs are recorded in synced_posts.json so a post is never
turned into a duplicate product on a later run.

Usage:
    python scripts/sync_products.py
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

POSTS_JSON = Path("posts.json")
SYNCED_FILE = Path("synced_posts.json")

# Same Firebase Realtime Database used by gcp-shop.html.
FIREBASE_DB_URL = "https://gcpshop1-default-rtdb.firebaseio.com"
PRODUCTS_URL = f"{FIREBASE_DB_URL}/gcp_shop/products.json"

FIELD_PATTERN = re.compile(
    r"^\s*(name|brand|icon|shopee|tiktok)\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def fetch_json(url):
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def put_json(url, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="PUT",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status


def parse_post(message):
    fields = {}
    for key, value in FIELD_PATTERN.findall(message or ""):
        fields[key.lower()] = value.strip()

    name = fields.get("name")
    brand = fields.get("brand")
    shopee = fields.get("shopee", "")
    tiktok = fields.get("tiktok", "")
    icon = fields.get("icon") or "\U0001F4E6"  # default: package emoji

    if not name or not brand or not (shopee or tiktok):
        return None

    return {
        "name": name,
        "brand": brand.title(),
        "icon": icon,
        "shopee": shopee,
        "tiktok": tiktok,
    }


def fav_key(p):
    return f"{p['name']}|{p['brand']}".lower()


def main():
    posts_data = load_json(POSTS_JSON, {})
    posts = posts_data.get("data", [])
    synced_ids = set(load_json(SYNCED_FILE, []))

    new_products = []
    newly_synced = []

    for post in posts:
        pid = post.get("id")
        if not pid or pid in synced_ids:
            continue
        product = parse_post(post.get("message", ""))
        if product:
            new_products.append(product)
        # Mark every new post as seen, even non-matching ones, so a
        # regular caption post isn't re-checked forever.
        newly_synced.append(pid)

    if not newly_synced:
        print("No new posts to process.")
        return

    if new_products:
        try:
            existing = fetch_json(PRODUCTS_URL) or []
        except Exception as e:
            sys.exit(f"ERROR: could not read current products from Firebase: {e}")

        existing_keys = {fav_key(p) for p in existing if isinstance(p, dict) and "name" in p}
        added = 0
        for p in new_products:
            if fav_key(p) in existing_keys:
                print(f"Skipping duplicate: {p['name']} ({p['brand']})")
                continue
            existing.append(p)
            existing_keys.add(fav_key(p))
            added += 1

        if added:
            try:
                put_json(PRODUCTS_URL, existing)
            except Exception as e:
                sys.exit(f"ERROR: failed to write products to Firebase: {e}")
            print(f"Added {added} new product(s) to Firebase.")
        else:
            print("No new unique products to add.")
    else:
        print("No posts matched the product template.")

    synced_ids.update(newly_synced)
    SYNCED_FILE.write_text(json.dumps(sorted(synced_ids), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
