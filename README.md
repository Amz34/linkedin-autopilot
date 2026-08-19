# LinkedIn Post Tool — IFMI / Luxe Wave

Local CLI tool for posting to LinkedIn — personal profile and company pages.
Write content manually or generate it with AI (DeepSeek).

## Features

- Post to your personal profile or company pages (IFMI, Luxe Wave)
- Manual text or AI-generated content (DeepSeek, approval before publishing)
- Image support (PNG/JPG/WebP/GIF) with automatic banner generation
- Token auto-refresh (60-day access tokens)

## Setup (one-time, ~10 minutes)

### 1. Create a LinkedIn Developer App

1. https://developer.linkedin.com → **My Apps** → **Create app**
   - App name: `IFMI Content Tool`
   - LinkedIn Page: any of your pages (or personal) — changeable later
   - Logo: any image
2. **Products** tab → add these three:
   - ✅ **Sign In with LinkedIn using OpenID Connect**
   - ✅ **Share on LinkedIn**
   - ✅ **Community Management API**
3. **Auth** tab → under **Redirect URLs**, add:
   ```
   http://localhost:8787/callback
   ```
4. **Auth** tab → copy **Client ID** and **Client Secret**

### 2. Create the .env file

```bash
cp .env.example .env
```

Then fill in the values:

- `LINKEDIN_CLIENT_ID` = your Client ID
- `LINKEDIN_CLIENT_SECRET` = your Client Secret
- `DEEPSEEK_API_KEY` = your DeepSeek API key (for AI mode)

### 3. Authorize

```bash
python auth.py
```

The browser opens → click **Allow** on LinkedIn → the token is saved
automatically to `token.json`.

## Usage

```bash
# Manual post — personal profile
python post.py --personal "Hello LinkedIn! ..."

# Manual post with image — personal profile
python post.py --personal "Hello LinkedIn! ..." --image photo.jpg

# Manual post — company page
python post.py --page "Hello! ..."

# AI post — personal (topic optional)
python post.py --ai --personal --topic "facility management trends"

# AI post — company page
python post.py --ai --page --topic "cleaning services KSA"
```

## Image posts

```bash
# Text + image (jpg/png/webp/gif) — personal profile
python post.py --personal "Your text" --image banner.png

# AI post + image
python post.py --ai --personal --image banner.png

# Generate your own banner (Python PIL):
python make_banner.py   # -> banner.png
```

## Files

| File | Purpose |
|---|---|
| `auth.py` | LinkedIn OAuth login + token save/refresh |
| `post.py` | Publish posts (manual + AI) |
| `make_banner.py` | Generate a branded banner image |
| `.env` | Credentials (NEVER share or commit) |
| `token.json` | Access token (auto-refreshed) |

## Security

- Never share or commit `.env` or `token.json`
- Revoke the token anytime in LinkedIn (Settings → Data privacy → Permissions)

## Content guidelines (built into the AI prompt)

- Hook in the first line, value in the middle, question or CTA at the end
- Short lines, 2-4 emojis max, relevant hashtags (3-5)
- 100-220 words, no clickbait, no fake stats
- No em dashes — use commas, colons, or periods
