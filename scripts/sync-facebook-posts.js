/**
 * sync-facebook-posts.js
 *
 * Fetches recent posts from a Facebook Page, extracts product info from
 * posts written in the tagged format:
 *
 *   Product: <name>
 *   Brand: <brand>
 *   Icon: <emoji>          (optional)
 *   Shopee: <link>         (optional if Tiktok is present)
 *   Tiktok: <link>         (optional if Shopee is present)
 *
 * New products are appended to the Firebase Realtime Database list your
 * site already reads from (CLOUD_PRODUCTS_URL). Already-processed post IDs
 * are tracked in data/processed_posts.json so the same post never gets
 * added twice, even if the workflow runs again.
 *
 * Required environment variables (set as GitHub Actions secrets):
 *   FB_PAGE_ID            - your Facebook Page's numeric ID
 *   FB_PAGE_ACCESS_TOKEN  - a Page Access Token with pages_read_engagement
 *   FIREBASE_DB_URL       - e.g. https://gcpshop1-default-rtdb.firebaseio.com
 */

const fs = require("fs");
const path = require("path");

const FB_PAGE_ID = process.env.FB_PAGE_ID;
const FB_PAGE_ACCESS_TOKEN = process.env.FB_PAGE_ACCESS_TOKEN;
const FIREBASE_DB_URL = process.env.FIREBASE_DB_URL;

const PROCESSED_POSTS_PATH = path.join(__dirname, "..", "data", "processed_posts.json");
const GRAPH_API_VERSION = "v22.0";

function loadProcessedIds() {
  try {
    const raw = fs.readFileSync(PROCESSED_POSTS_PATH, "utf8");
    return new Set(JSON.parse(raw));
  } catch (e) {
    return new Set();
  }
}

function saveProcessedIds(idsSet) {
  fs.writeFileSync(
    PROCESSED_POSTS_PATH,
    JSON.stringify([...idsSet], null, 2) + "\n"
  );
}

// Pulls a value out of a "Tag: value" line, case-insensitive, anywhere in the text.
function extractTag(message, tag) {
  const re = new RegExp(`^\\s*${tag}\\s*:\\s*(.+)$`, "im");
  const match = message.match(re);
  return match ? match[1].trim() : "";
}

function parseProductFromPost(message) {
  if (!message) return null;
  const name = extractTag(message, "Product");
  const brand = extractTag(message, "Brand");
  const icon = extractTag(message, "Icon");
  const shopee = extractTag(message, "Shopee");
  const tiktok = extractTag(message, "Tiktok");

  if (!name || !brand) return null;
  if (!shopee && !tiktok) return null;

  return {
    name,
    brand,
    icon: icon || "📦",
    shopee: shopee || "",
    tiktok: tiktok || "",
  };
}

async function fetchRecentPosts() {
  const url =
    `https://graph.facebook.com/${GRAPH_API_VERSION}/${FB_PAGE_ID}/posts` +
    `?fields=id,message,created_time&limit=25&access_token=${FB_PAGE_ACCESS_TOKEN}`;

  const res = await fetch(url);
  const data = await res.json();

  if (data.error) {
    throw new Error(`Facebook API error: ${data.error.message}`);
  }
  return data.data || [];
}

async function fetchCurrentProducts() {
  const url = `${FIREBASE_DB_URL}/gcp_shop/products.json`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Could not reach Firebase to read products");
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

async function saveProducts(products) {
  const url = `${FIREBASE_DB_URL}/gcp_shop/products.json`;
  const res = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(products),
  });
  if (!res.ok) throw new Error("Could not save updated products to Firebase");
}

async function main() {
  if (!FB_PAGE_ID || !FB_PAGE_ACCESS_TOKEN || !FIREBASE_DB_URL) {
    console.error(
      "Missing required env vars. Need FB_PAGE_ID, FB_PAGE_ACCESS_TOKEN, FIREBASE_DB_URL."
    );
    process.exit(1);
  }

  const processedIds = loadProcessedIds();
  const posts = await fetchRecentPosts();

  // Oldest first, so products are added in the order they were posted.
  posts.sort((a, b) => new Date(a.created_time) - new Date(b.created_time));

  const newProducts = [];
  for (const post of posts) {
    if (processedIds.has(post.id)) continue;

    const product = parseProductFromPost(post.message);
    if (product) {
      newProducts.push(product);
      console.log(`Parsed new product from post ${post.id}: ${product.name}`);
    } else {
      console.log(`Post ${post.id} did not match product tag format — skipped.`);
    }
    processedIds.add(post.id);
  }

  if (newProducts.length === 0) {
    console.log("No new products found. Nothing to sync.");
    saveProcessedIds(processedIds);
    return;
  }

  const currentProducts = await fetchCurrentProducts();
  const updatedProducts = [...currentProducts, ...newProducts];
  await saveProducts(updatedProducts);
  saveProcessedIds(processedIds);

  console.log(`Synced ${newProducts.length} new product(s) to Firebase.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
