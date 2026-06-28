# GCP Shop — Affiliate Links

A single-page affiliate product shop by Paolo Centeno. Deployable as a static site on Render.

---

## Files

| File | Purpose |
|---|---|
| `index.html` | The entire app — all HTML, CSS, and JS in one file |
| `render.yaml` | Render static site configuration |
| `.gitignore` | Ignores OS/editor junk files |

---

## Firebase Setup (Required for Admin Save)

The app uses **Firebase Realtime Database** to let the admin save product changes that are visible to everyone. Without this, only the local browser save works.

### Step 1 — Create a Firebase project

1. Go to [https://console.firebase.google.com](https://console.firebase.google.com)
2. Click **Add project** → name it (e.g. `gcp-shop`) → continue through the steps
3. Once created, click **Build → Realtime Database** in the left sidebar
4. Click **Create Database** → choose a region → start in **Test mode** (you can lock it down later)

### Step 2 — Get your config

1. In Firebase Console, click the ⚙️ gear icon → **Project Settings**
2. Scroll down to **Your apps** → click the `</>` web icon to register a web app if you haven't yet
3. After registering, you'll see **SDK setup and configuration** — select **Config**
4. Copy the entire `firebaseConfig` object — it looks like this:

```js
const firebaseConfig = {
  apiKey: "AIza...",
  authDomain: "your-project.firebaseapp.com",
  databaseURL: "https://your-project-default-rtdb.firebaseio.com",
  projectId: "your-project",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

### Step 3 — Paste it into index.html

Open `index.html` and find the `<script type="module">` block near the bottom. Replace the placeholder `firebaseConfig` block with your real values.

Look for this comment:
```js
// ── FIREBASE CONFIG ── Replace with your actual project config
```

Paste your copied config object right below it, replacing everything from `const firebaseConfig = {` to the closing `};`.

### Step 4 — Set Realtime Database rules (optional but recommended)

In Firebase Console → Realtime Database → Rules, set:

```json
{
  "rules": {
    "gcp_shop": {
      "products": {
        ".read": true,
        ".write": true
      }
    }
  }
}
```

This allows anyone to read products (so visitors see the latest list) but you can tighten write access later with auth.

---

## Deploy to Render

1. Push this folder to a **GitHub repository** (can be private)
2. Go to [https://render.com](https://render.com) → **New → Static Site**
3. Connect your GitHub account and select the repository
4. Render will detect `render.yaml` automatically
5. Click **Deploy** — your site will be live in about a minute

### Manual settings (if Render doesn't auto-detect)

| Setting | Value |
|---|---|
| Build Command | *(leave empty)* |
| Publish Directory | `.` |

---

## How Save Works

| Context | Behavior |
|---|---|
| Homepage (not in edit mode) | SAVE button shows Admin / User popup |
| Admin choice | Saves products to Firebase (visible to everyone) |
| User choice | Saves favorites + products to this browser only |
| Edit mode (admin unlocked) | Every add/edit/delete auto-saves directly to Firebase — no popup |
